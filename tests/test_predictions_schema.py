"""predictions.yaml is the source of truth — keep it schema-clean."""

import datetime
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_KEYS = {
    "id",
    "domain",
    "statement",
    "made",
    "resolve_by",
    "probability",
    "confirm",
    "invalidate",
    "status",
    "evidence",
}
VALID_STATUSES = {"open", "confirmed", "invalidated", "ambiguous"}

PUBLIC_FORECASTS = [
    (
        "EM-001",
        "Listed grid EPC and metering firms show double-digit order-book conversion AND improving cash conversion (receivable days flat or falling year-on-year in aggregate).",
        datetime.date(2027, 3, 31),
        0.65,
        "FY27 filings show both.",
        "conversion stalls, or growth arrives only with ballooning receivables.",
    ),
    (
        "EM-002",
        "At least five distinct hyperscale Indian campuses (across at least three operators) disclose dedicated EHV substations, captive supply, or firm round-the-clock power structures.",
        datetime.date(2027, 12, 31),
        0.70,
        "utility or company filings.",
        "fewer than five; ordinary distribution connections dominate.",
    ),
    (
        "EM-003",
        "A marquee data-centre cluster is publicly delayed by power, water, land or right-of-way — not chip supply.",
        datetime.date(2028, 12, 31),
        0.70,
        "disclosed schedule slip citing those causes.",
        "all major projects commission on time.",
    ),
    (
        "EM-004",
        "Operational Indian data-centre capacity reaches 8–12GW; AI-specific capacity exceeds 4GW.",
        datetime.date(2030, 3, 31),
        0.60,
        "independent capacity audit.",
        "operational capacity remains below 8GW.",
    ),
    (
        "EM-005",
        "Firm clean-power contracts and storage grow faster than merchant electricity volumes at the major data-centre nodes.",
        datetime.date(2030, 3, 31),
        0.65,
        "PPA and BESS award data.",
        "spot power becomes the dominant procurement route.",
    ),
    (
        "EM-006",
        "The best risk-adjusted listed-equity returns in the theme came from the broader grid stack, not from the highest-multiple 'AI power' equipment names as priced in mid-2026.",
        datetime.date(2032, 3, 31),
        0.60,
        "total-return comparison from Aug 2026 baseline.",
        "premium multiples keep expanding with superior earnings.",
    ),
]


def load():
    data = yaml.safe_load((REPO_ROOT / "predictions.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, list) and data
    return data


def test_entries_have_required_fields_and_sane_values():
    for entry in load():
        assert isinstance(entry, dict)
        missing = REQUIRED_KEYS - set(entry)
        assert not missing, f"{entry.get('id')}: missing {missing}"
        assert entry["status"] in VALID_STATUSES
        assert 0.0 <= float(entry["probability"]) <= 1.0
        assert isinstance(entry["made"], datetime.date)
        assert isinstance(entry["resolve_by"], datetime.date)
        assert isinstance(entry["evidence"], list)


def test_ids_unique():
    ids = [e["id"] for e in load()]
    assert len(ids) == len(set(ids))


def test_public_forecasts_match_source_transcription():
    by_id = {entry["id"]: entry for entry in load()}
    for pid, statement, resolve_by, probability, confirm, invalidate in PUBLIC_FORECASTS:
        entry = by_id[pid]
        assert entry["domain"] == "india-ai-power"
        assert entry["statement"] == statement
        assert entry["made"] == datetime.date(2026, 8, 10)
        assert entry["resolve_by"] == resolve_by
        assert float(entry["probability"]) == probability
        assert entry["confirm"] == confirm
        assert entry["invalidate"] == invalidate
        assert entry["status"] == "open"
        assert entry["evidence"] == []


def test_em007_meta_prediction_seeded_verbatim():
    em007 = {e["id"]: e for e in load()}["EM-007"]
    assert em007["status"] == "open"
    assert float(em007["probability"]) == 0.60
    assert em007["resolve_by"] == datetime.date(2026, 9, 14)
    assert "4 consecutive weekly updates with zero fabricated citations" in em007["statement"]


def test_weekly_success_state_is_written_before_commit():
    script = (REPO_ROOT / "scripts" / "run_weekly.sh").read_text(encoding="utf-8")
    health_stage = script.index('STAGE="health"')
    state_update = script.index('line = f"Last run:')
    commit_stage = script.index('STAGE="commit"')
    assert health_stage < state_update < commit_stage
