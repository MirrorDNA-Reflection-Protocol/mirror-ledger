#!/usr/bin/env python3
"""Write the body-convention health receipt for the weekly run.

~/.mirrordna/health/mirror_ledger_weekly.json with allowed statuses ok|fail —
matches the manifest receipt_path/allowed_statuses convention so the lattice
can watch this pipeline like any other scheduled service. (The handoff named
~/.mirrordna/current_state.json and ~/.mirrordna/open_loops.md; neither exists
on this body, so the real conventions are used instead: this receipt plus
STATE.md entries in-repo.)
"""

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HEALTH_PATH = Path.home() / ".mirrordna" / "health" / "mirror_ledger_weekly.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("status", choices=["ok", "fail"])
    parser.add_argument("run_id")
    parser.add_argument("stage")
    parser.add_argument("--gathered", type=int, default=None)
    parser.add_argument("--validated", type=int, default=None)
    parser.add_argument("--rejected", type=int, default=None)
    parser.add_argument("--post", default=None)
    args = parser.parse_args()

    payload = {
        "service": "mirror-ledger-weekly",
        "status": args.status,
        "run_id": args.run_id,
        "stage": args.stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "gathered": args.gathered,
            "validated": args.validated,
            "rejected": args.rejected,
        },
        "post": args.post,
    }
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".mirror_ledger_weekly.", dir=str(HEALTH_PATH.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    os.replace(tmp, HEALTH_PATH)


if __name__ == "__main__":
    main()
