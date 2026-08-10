"""Layer-1 guard: items without usable URLs are dropped before validation."""

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
