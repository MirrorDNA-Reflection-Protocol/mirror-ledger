"""Layer-1 guard: items without usable URLs are dropped before validation."""

from pathlib import Path

from conftest import load_script

gather = load_script("gather_evidence")


def test_extract_items_from_fenced_json():
    text = '```json\n[{"claim": "c", "url": "https://x.example/a"}]\n```'
    items = gather.extract_items(text)
    assert isinstance(items, list) and len(items) == 1


def test_extract_items_plain_and_empty():
    assert gather.extract_items("Here you go: []") == []
    assert gather.extract_items("no array here") is None
    assert gather.extract_items('{"claim": "not a list"}') is None


def test_clean_items_drops_urlless_and_non_http():
    notes = []
    items = gather.clean_items(
        [
            {"claim": "has url", "url": "https://x.example/a", "date": "2026-08-01", "quote_fragment": "q"},
            {"claim": "missing url"},
            {"claim": "ftp scheme", "url": "ftp://x.example/a"},
            {"claim": "", "url": "https://x.example/empty-claim"},
            "not-a-dict",
        ],
        notes,
    )
    assert [i["url"] for i in items] == ["https://x.example/a"]
    assert len(notes) == 4


def test_clean_items_deduplicates_urls_and_enforces_india_scope():
    notes = []
    items = gather.clean_items(
        [
            {"claim": "Indian grid filing disclosed an award.", "url": "https://x.example/a"},
            {"claim": "India duplicate.", "url": "https://x.example/a/"},
            {"claim": "Texas project was delayed.", "url": "https://x.example/texas"},
        ],
        notes,
        ("india", "indian"),
    )
    assert [item["url"] for item in items] == ["https://x.example/a"]
    assert any("duplicate" in note for note in notes)
    assert any("out-of-scope" in note for note in notes)


def test_governed_launcher_contract_is_not_overridden():
    source = Path(gather.__file__).read_text(encoding="utf-8")
    assert '"--allowed-tools"' not in source
    assert '"--model"' not in source
