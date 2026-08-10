#!/usr/bin/env python3
"""Fabrication guard, layer 2 of 4: every evidence URL must be live.

Each gathered item is fetched over HTTP. Only final-status 2xx items enter
evidence/<EM-ID>.yaml; everything else goes to evidence/_rejected.log and can
never reach the ledger or the drafted post. predictions.yaml itself is never
rewritten by the pipeline (comment-preserving source of truth); the append
surface is the evidence/ directory keyed by prediction id.

Stdlib-only on purpose: the validator must not depend on the model runtime or
third-party packages beyond PyYAML (already required by the pipeline).
"""

import argparse
import json
import os
import ssl
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "mirror-ledger-validator/1.0 (+https://github.com/MirrorDNA-Reflection-Protocol)"
MAX_BODY_BYTES = 65536


def fetch_status(url, timeout):
    """Return (final_http_status, reason) for a GET of the URL."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            response.read(MAX_BODY_BYTES)
            return int(response.status), "ok"
    except urllib.error.HTTPError as exc:
        return int(exc.code), f"http {exc.code}"
    except urllib.error.URLError as exc:
        return 0, f"unreachable: {getattr(exc, 'reason', exc)}"
    except (ssl.SSLError, TimeoutError, OSError, ValueError) as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def atomic_dump_yaml(path, payload):
    import yaml

    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", default=os.environ.get("REPO_ROOT", "."))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("URL_TIMEOUT", "20")))
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    incoming = repo / "evidence" / "_incoming" / args.run_id
    evidence_dir = repo / "evidence"
    rejected_log = evidence_dir / "_rejected.log"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    gathered = validated = rejected = 0
    per_prediction = {}
    gather_report_path = incoming / "gather_report.json"
    gather_statuses = {}
    if gather_report_path.exists():
        gather_report = json.loads(gather_report_path.read_text(encoding="utf-8"))
        for pid, entry in gather_report.get("predictions", {}).items():
            gather_statuses[pid] = entry.get("status", "unknown")

    for items_file in sorted(incoming.glob("*.items.json")):
        pid = items_file.name.replace(".items.json", "")
        items = json.loads(items_file.read_text(encoding="utf-8"))
        accepted = []
        for item in items:
            gathered += 1
            url = str(item.get("url") or "")
            status, reason = fetch_status(url, args.timeout)
            if 200 <= status < 300:
                validated += 1
                accepted.append(
                    {
                        "run_id": args.run_id,
                        "gathered_at": now,
                        "claim": item.get("claim", ""),
                        "url": url,
                        "date": item.get("date", ""),
                        "quote_fragment": item.get("quote_fragment", ""),
                        "http_status": status,
                    }
                )
            else:
                rejected += 1
                with rejected_log.open("a", encoding="utf-8") as handle:
                    handle.write(f"{now}\t{args.run_id}\t{pid}\t{url}\t{reason}\n")
                print(f"[validate] REJECTED {pid} {url} ({reason})", file=sys.stderr)
        per_prediction[pid] = {"gathered": len(items), "validated": len(accepted)}
        if accepted:
            import yaml

            target = evidence_dir / f"{pid}.yaml"
            existing = []
            if target.exists():
                loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    existing = loaded
            atomic_dump_yaml(target, existing + accepted)

    summary = {
        "run_id": args.run_id,
        "validated_at": now,
        "gathered": gathered,
        "validated": validated,
        "rejected": rejected,
        "gather_calls": len(gather_statuses),
        "gather_successes": sum(status == "ok" for status in gather_statuses.values()),
        "gather_gaps": sum(status != "ok" for status in gather_statuses.values()),
        "gather_statuses": gather_statuses,
        "per_prediction": per_prediction,
    }
    (incoming / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[validate] gathered={gathered} validated={validated} rejected={rejected}", file=sys.stderr)


if __name__ == "__main__":
    main()
