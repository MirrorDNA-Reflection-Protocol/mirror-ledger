#!/usr/bin/env python3
"""Fabrication guard, layer 4 of 4 — plus the finance-language tripwire.

Fails the run loudly (nonzero exit) when the drafted post contains:
  exit 2 — ticker/price/buy-sell patterns (the ledger scores events, never
           trades: "buy NTPC at ₹344" must kill the run), or
  exit 3 — any http(s) URL that is not in the URL-validated evidence set
           (a URL the drafter was never given == potential fabrication).

Deterministic and stdlib+PyYAML only; no model involvement.
"""

import argparse
import re
import sys
from pathlib import Path

# Precision over recall by design: an over-eager tripwire that fails a run on
# legitimate event evidence ("acquires a 20% stake for ₹1,000 crore") would
# count as a manual repair against EM-007. "buy NTPC at ₹344" must still die.
FINANCE_PATTERNS = [
    (re.compile(r"\b(?:[Bb]uy|[Ss]ell)\s+[A-Z]{2,12}\b"), "buy/sell + ticker"),
    (re.compile(r"\btarget\s+price\b|\bstop\s?-?loss\b", re.IGNORECASE), "target-price/stop-loss language"),
    (re.compile(r"\b[A-Z]{2,12}\s+at\s+₹\s*\d"), "ticker at ₹price"),
]

URL_RE = re.compile(r"https?://[^\s)\]>\"'`]+")
ALWAYS_ALLOWED_PREFIXES = (
    "https://github.com/MirrorDNA-Reflection-Protocol/",
)


def allowed_urls(repo_root):
    allowed = set()
    paths = sorted((repo_root / "evidence").glob("EM-*.yaml"))
    if not paths:
        return allowed
    import yaml

    for path in paths:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            for entry in loaded:
                if isinstance(entry, dict) and entry.get("url"):
                    allowed.add(str(entry["url"]).rstrip("/"))
    return allowed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("post_file")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()

    post_path = Path(args.post_file).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else post_path.parent.parent
    text = post_path.read_text(encoding="utf-8")

    violations = []
    for pattern, label in FINANCE_PATTERNS:
        for match in pattern.finditer(text):
            violations.append(f"{label}: {match.group(0)!r}")
    if violations:
        for line in violations:
            print(f"[lint] FINANCE VIOLATION — {line}", file=sys.stderr)
        sys.exit(2)

    allowed = allowed_urls(repo_root)
    unknown = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;:!?").rstrip("/")
        if url in allowed or any(url.startswith(p) for p in ALWAYS_ALLOWED_PREFIXES):
            continue
        unknown.append(url)
    if unknown:
        for url in unknown:
            print(f"[lint] UNVALIDATED URL — {url} (not in evidence set)", file=sys.stderr)
        sys.exit(3)

    print("[lint] clean", file=sys.stderr)


if __name__ == "__main__":
    main()
