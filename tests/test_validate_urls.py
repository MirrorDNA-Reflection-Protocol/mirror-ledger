"""Acceptance test 2 (poison test) at unit level: a fabricated/unreachable URL
injected into gather output must be rejected and never enter the ledger."""

import json
import sys

import pytest

from conftest import load_script

validate = load_script("validate_urls")


def test_poison_url_is_unreachable():
    # RFC 2606 reserves .invalid — deterministic failure without live network.
    status, reason = validate.fetch_status("https://mirror-ledger-poison.invalid/x", 5)
    assert status == 0
    assert reason


def test_flow_rejects_poison_and_keeps_valid(tmp_path, monkeypatch):
    pytest.importorskip("yaml")
    import yaml

    run_id = "ledger-test"
    incoming = tmp_path / "evidence" / "_incoming" / run_id
    incoming.mkdir(parents=True)
    (incoming / "EM-001.items.json").write_text(
        json.dumps(
            [
                {"claim": "real filing", "url": "https://good.example/filing", "date": "2026-08-01", "quote_fragment": "q"},
                {"claim": "fabricated", "url": "https://mirror-ledger-poison.invalid/x", "date": "2026-08-02", "quote_fragment": "q"},
            ]
        ),
        encoding="utf-8",
    )

    def fake_fetch(url, timeout):
        return (200, "ok") if "good.example" in url else (0, "unreachable: dns")

    monkeypatch.setattr(validate, "fetch_status", fake_fetch)
    monkeypatch.setattr(
        sys, "argv", ["validate_urls.py", "--run-id", run_id, "--repo-root", str(tmp_path)]
    )
    validate.main()

    ledger = yaml.safe_load((tmp_path / "evidence" / "EM-001.yaml").read_text(encoding="utf-8"))
    assert len(ledger) == 1
    assert ledger[0]["url"] == "https://good.example/filing"
    assert ledger[0]["http_status"] == 200

    rejected = (tmp_path / "evidence" / "_rejected.log").read_text(encoding="utf-8")
    assert "mirror-ledger-poison.invalid" in rejected

    summary = json.loads((incoming / "summary.json").read_text(encoding="utf-8"))
    assert summary["gathered"] == 2
    assert summary["validated"] == 1
    assert summary["rejected"] == 1
