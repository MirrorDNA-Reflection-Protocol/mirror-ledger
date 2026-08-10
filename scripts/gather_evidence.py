#!/usr/bin/env python3
"""Gather fresh evidence for each open prediction via headless Claude.

Fabrication guard, layer 1 of 4: the prompt demands {claim, url, date,
quote_fragment} JSON and instructs the model that an item without a URL is
worthless; items arriving without a usable url field are dropped here and
logged. Layers 2-4 live in validate_urls.py, draft_post.py, lint_post.py.

Boundary: uses the governed subscription launcher only. ANTHROPIC_API_KEY is
stripped from the child environment so this can never silently become an
API-billed surface (claude.routing.subscription_api_boundary).
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROMPT_TEMPLATE = """You are the evidence gatherer for a public forecast ledger. Work ONLY with sources you can actually open on the live web right now.

PREDICTION {pid}: {statement}
Confirmed when: {confirm}
Invalidated when: {invalidate}

Search the public web for material published in the last 10 days that bears on this prediction, in either direction. Return ONLY a JSON array — no prose, no markdown fences. Each element:
{{"claim": "<one factual sentence stating what the source shows>", "url": "<the exact URL you opened>", "date": "<publication date, YYYY-MM-DD>", "quote_fragment": "<verbatim fragment from the page, at most 25 words>"}}

Hard rules:
- An item without a real, working URL is worthless. If you cannot open and verify a source, leave it out.
- If nothing verifiable exists this week, return exactly: []
- Never fabricate, reconstruct, or approximate a URL. Returning [] is always better than inventing anything.
- No price targets, tickers, or buy/sell language in claims. Events and filings only.
"""


def open_predictions(repo_root):
    import yaml

    data = yaml.safe_load((repo_root / "predictions.yaml").read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("predictions.yaml did not parse to a list")
    return [p for p in data if isinstance(p, dict) and p.get("status") == "open"]


def extract_items(result_text):
    """Pull the first JSON array out of the model's reply, defensively."""
    text = (result_text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, list) else None


def clean_items(raw_items, report_notes):
    items = []
    for item in raw_items:
        if not isinstance(item, dict):
            report_notes.append("dropped non-object item")
            continue
        url = str(item.get("url") or "").strip()
        claim = str(item.get("claim") or "").strip()
        if not url.lower().startswith(("http://", "https://")) or not claim:
            report_notes.append(f"dropped item without usable url/claim: {url[:80]!r}")
            continue
        items.append(
            {
                "claim": claim,
                "url": url,
                "date": str(item.get("date") or "").strip(),
                "quote_fragment": str(item.get("quote_fragment") or "").strip(),
            }
        )
    return items


def main():
    repo_root = Path(os.environ["REPO_ROOT"])
    run_id = os.environ["RUN_ID"]
    claude_bin = os.environ.get("CLAUDE_BIN", "/Users/pauldesai/bin/claude")
    model = os.environ.get("MODEL", "claude-opus-4-6")
    gather_timeout = int(os.environ.get("GATHER_TIMEOUT", "600"))
    incoming = repo_root / "evidence" / "_incoming" / run_id

    incoming.mkdir(parents=True, exist_ok=True)
    child_env = dict(os.environ)
    child_env.pop("ANTHROPIC_API_KEY", None)  # subscription lane only

    predictions = open_predictions(repo_root)
    report = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "predictions": {},
    }
    errored = 0

    for pred in predictions:
        pid = str(pred["id"])
        prompt = PROMPT_TEMPLATE.format(
            pid=pid,
            statement=pred.get("statement", ""),
            confirm=pred.get("confirm", ""),
            invalidate=pred.get("invalidate", ""),
        )
        entry = {"status": "ok", "items": 0, "notes": []}
        try:
            proc = subprocess.run(
                [
                    claude_bin,
                    "-p",
                    prompt,
                    "--output-format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=gather_timeout,
                env=child_env,
                cwd=str(repo_root),
            )
            (incoming / f"{pid}.raw.json").write_text(proc.stdout or "", encoding="utf-8")
            if proc.returncode != 0:
                entry["status"] = "error"
                entry["notes"].append(f"claude exit {proc.returncode}: {(proc.stderr or '')[:300]}")
            else:
                try:
                    envelope = json.loads(proc.stdout)
                    result_text = envelope.get("result", "") if isinstance(envelope, dict) else proc.stdout
                except json.JSONDecodeError:
                    result_text = proc.stdout
                raw_items = extract_items(result_text)
                if raw_items is None:
                    entry["status"] = "unparseable"
                    entry["notes"].append("no JSON array found in reply")
                    raw_items = []
                items = clean_items(raw_items, entry["notes"])
                entry["items"] = len(items)
                (incoming / f"{pid}.items.json").write_text(
                    json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except subprocess.TimeoutExpired:
            entry["status"] = "timeout"
            entry["notes"].append(f"exceeded {gather_timeout}s")
        except OSError as exc:
            entry["status"] = "error"
            entry["notes"].append(f"launch failed: {exc}")

        if entry["status"] in {"error", "timeout"}:
            errored += 1
        if not (incoming / f"{pid}.items.json").exists():
            (incoming / f"{pid}.items.json").write_text("[]", encoding="utf-8")
        report["predictions"][pid] = entry
        print(f"[gather] {pid}: {entry['status']} items={entry['items']}", file=sys.stderr)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    (incoming / "gather_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    if predictions and errored == len(predictions):
        print("[gather] every headless call failed — failing the run for visibility", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
