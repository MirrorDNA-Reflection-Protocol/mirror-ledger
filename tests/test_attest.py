"""Attestation hashing must be deterministic and content-sensitive."""

from conftest import load_script

attest = load_script("attest")


def build_tree(root):
    (root / "sub").mkdir(parents=True)
    (root / "a.yaml").write_text("alpha\n", encoding="utf-8")
    (root / "sub" / "b.yaml").write_text("beta\n", encoding="utf-8")


def test_tree_hash_deterministic(tmp_path):
    build_tree(tmp_path)
    assert attest.tree_sha256(tmp_path) == attest.tree_sha256(tmp_path)


def test_tree_hash_changes_on_content_change(tmp_path):
    build_tree(tmp_path)
    before = attest.tree_sha256(tmp_path)
    (tmp_path / "a.yaml").write_text("alpha-changed\n", encoding="utf-8")
    assert attest.tree_sha256(tmp_path) != before


def test_tree_hash_changes_on_new_file(tmp_path):
    build_tree(tmp_path)
    before = attest.tree_sha256(tmp_path)
    (tmp_path / "sub" / "c.yaml").write_text("gamma\n", encoding="utf-8")
    assert attest.tree_sha256(tmp_path) != before


def test_tree_hash_ignores_creation_order(tmp_path):
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()
    (first / "a").write_text("same", encoding="utf-8")
    (first / "b").write_text("data", encoding="utf-8")
    (second / "b").write_text("data", encoding="utf-8")
    (second / "a").write_text("same", encoding="utf-8")
    assert attest.tree_sha256(first) == attest.tree_sha256(second)
