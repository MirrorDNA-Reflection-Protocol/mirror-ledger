"""Acceptance test 4 (lint test) at unit level: ticker/price/buy-sell language
in a draft must fail the run loudly, while legitimate event evidence passes."""

import sys

import pytest

from conftest import load_script

lint = load_script("lint_post")


def run_lint(monkeypatch, post_path, repo_root):
    monkeypatch.setattr(sys, "argv", ["lint_post.py", str(post_path), "--repo-root", str(repo_root)])
    lint.main()


def make_repo(tmp_path):
    (tmp_path / "evidence").mkdir()
    (tmp_path / "posts").mkdir()
    return tmp_path


def test_handoff_poison_fixture_fails(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    post = repo / "posts" / "2026-08-17.md"
    post.write_text("Strong week. You should buy NTPC at ₹344 before results.\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        run_lint(monkeypatch, post, repo)
    assert excinfo.value.code == 2


@pytest.mark.parametrize(
    "text",
    [
        "Sell TATAPOWER now",
        "our target price of 500 stands",
        "keep a stop-loss under it",
        "NTPC at ₹344 looks attractive",
    ],
)
def test_finance_patterns_catch_variants(text):
    assert any(p.search(text) for p, _ in lint.FINANCE_PATTERNS), text


@pytest.mark.parametrize(
    "text",
    [
        "The company sells transformers and won an order worth ₹1,200 crore.",
        "The firm will buy a 20% stake in the metering JV for ₹1,000 crore.",
        "Order book conversion improved; receivable days fell YoY.",
    ],
)
def test_legitimate_event_evidence_passes(text):
    assert not any(p.search(text) for p, _ in lint.FINANCE_PATTERNS), text


def test_clean_post_passes(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    post = repo / "posts" / "2026-08-17.md"
    post.write_text(
        "# Ledger Update\n\nEM-007: No verifiable evidence surfaced this week.\n",
        encoding="utf-8",
    )
    run_lint(monkeypatch, post, repo)  # must not raise


def test_unvalidated_url_fails(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    post = repo / "posts" / "2026-08-17.md"
    post.write_text(
        "Per [this report](https://example.com/made-up-report) things improved.\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as excinfo:
        run_lint(monkeypatch, post, repo)
    assert excinfo.value.code == 3


def test_validated_url_passes(tmp_path, monkeypatch):
    yaml = pytest.importorskip("yaml")
    repo = make_repo(tmp_path)
    (repo / "evidence" / "EM-001.yaml").write_text(
        yaml.safe_dump([{"url": "https://example.com/real-filing", "claim": "x"}]),
        encoding="utf-8",
    )
    post = repo / "posts" / "2026-08-17.md"
    post.write_text(
        "Per [the filing](https://example.com/real-filing) conversion improved.\n",
        encoding="utf-8",
    )
    run_lint(monkeypatch, post, repo)  # must not raise
