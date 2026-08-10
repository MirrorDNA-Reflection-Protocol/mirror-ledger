#!/bin/bash
# Thin entry per pipeline contract; the work happens in attest.py.
set -euo pipefail
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [ -z "${PYBIN:-}" ]; then
  echo "[attest] PYBIN not set; run through scripts/run_weekly.sh" >&2
  exit 78
fi
exec "$PYBIN" "$REPO_ROOT/scripts/attest.py"
