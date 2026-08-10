#!/usr/bin/env python3
"""Attestation receipt: hash of ledger state + timestamp. Receipt-first,
transport-second — the repo receipt is always written; the MirrorBus append
(~/.mirrordna/bus/mirror_ledger_attestations.jsonl, the body's append-only
bus lane convention) is attempted afterwards and any failure is flagged in
the receipt and STATE.md instead of failing the run.

These are L1 hash commitments on the host clock, not zero-knowledge proofs
and not independent attestations (ZKP_READY_NOT_ZKP_PROVEN).
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(root):
    """Manifest hash over relative path + content hash of every file, sorted."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8") + b"\0" + sha256_file(path).encode("ascii") + b"\n")
    return digest.hexdigest()


def main():
    repo_root = Path(os.environ["REPO_ROOT"])
    run_id = os.environ["RUN_ID"]
    run_date = os.environ["RUN_DATE"]
    bus_lane = Path.home() / ".mirrordna" / "bus" / "mirror_ledger_attestations.jsonl"

    now = datetime.now(timezone.utc).isoformat()
    receipts_dir = repo_root / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    summary_path = repo_root / "evidence" / "_incoming" / run_id / "summary.json"
    counts = {}
    if summary_path.exists():
        loaded = json.loads(summary_path.read_text(encoding="utf-8"))
        counts = {k: loaded.get(k) for k in ("gathered", "validated", "rejected")}

    post_path = repo_root / "posts" / f"{run_date}.md"
    receipt = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": now,
        "predictions_sha256": sha256_file(repo_root / "predictions.yaml"),
        "evidence_tree_sha256": tree_sha256(repo_root / "evidence"),
        "post_file": f"posts/{run_date}.md" if post_path.exists() else None,
        "post_sha256": sha256_file(post_path) if post_path.exists() else None,
        "counts": counts,
        "proof_class": "sha256-hash-commitment-host-clock",
        "transport": {"bus_lane": str(bus_lane), "posted": False, "error": None},
    }
    receipt_path = receipts_dir / f"{run_id}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    bus_record = {
        "ts": now,
        "actor": "mirror-ledger-pipeline",
        "run_id": run_id,
        "predictions_sha256": receipt["predictions_sha256"],
        "evidence_tree_sha256": receipt["evidence_tree_sha256"],
        "post_sha256": receipt["post_sha256"],
        "receipt_path": str(receipt_path),
    }
    try:
        bus_lane.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(bus_lane), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(bus_record, sort_keys=True) + "\n")
        receipt["transport"]["posted"] = True
    except OSError as exc:
        receipt["transport"]["error"] = f"{type(exc).__name__}: {exc}"
        with (repo_root / "STATE.md").open("a", encoding="utf-8") as handle:
            handle.write(
                f"- {now} | run {run_id}: MirrorBus lane append FAILED "
                f"({receipt['transport']['error']}); local receipt retained at receipts/{run_id}.json.\n"
            )
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"[attest] receipt receipts/{run_id}.json bus_posted={receipt['transport']['posted']}")


if __name__ == "__main__":
    main()
