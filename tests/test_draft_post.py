"""Layer-3 guard: drafting is deterministic and validated-input-only."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_draft_contains_only_validated_evidence(tmp_path):
    repo = tmp_path / "ledger"
    incoming = repo / "evidence" / "_incoming" / "test-run"
    incoming.mkdir(parents=True)
    (repo / "posts").mkdir()
    (repo / "predictions.yaml").write_text(
        "- id: EM-001\n"
        "  statement: Exact prediction text.\n"
        "  status: open\n"
        "- id: EM-002\n"
        "  statement: Second prediction.\n"
        "  status: open\n",
        encoding="utf-8",
    )
    (repo / "evidence" / "EM-001.yaml").write_text(
        "- run_id: test-run\n"
        "  claim: Verified claim.\n"
        "  url: https://example.com/verified\n"
        "  date: 2026-08-10\n"
        "  quote_fragment: exact fragment\n",
        encoding="utf-8",
    )
    (incoming / "summary.json").write_text(
        json.dumps(
            {
                "gathered": 1,
                "validated": 1,
                "rejected": 0,
                "gather_calls": 2,
                "gather_successes": 1,
                "gather_gaps": 1,
            }
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.update(REPO_ROOT=str(repo), RUN_ID="test-run", RUN_DATE="2026-08-10")
    script = Path(__file__).resolve().parents[1] / "scripts" / "draft_post.py"

    proc = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True)

    assert proc.returncode == 0, proc.stderr
    post = (repo / "posts" / "2026-08-10.md").read_text(encoding="utf-8")
    assert "Exact prediction text." in post
    assert "[Verified claim.](https://example.com/verified) — 2026-08-10" in post
    assert "Second prediction." in post
    assert "No verifiable evidence surfaced this week." in post
    assert "https://example.com/unvalidated" not in post
    assert "1/2 gather calls succeeded with 1 gaps" in post
