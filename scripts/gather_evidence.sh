#!/bin/bash
# Thin entry per pipeline contract; the work happens in gather_evidence.py
# under the resolved PYBIN. Expects env from run_weekly.sh (or sets defaults
# for a manual supervised run).
set -euo pipefail
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [ -z "${PYBIN:-}" ]; then
  echo "[gather_evidence] PYBIN not set; run through scripts/run_weekly.sh" >&2
  exit 78
fi
exec "$PYBIN" "$REPO_ROOT/scripts/gather_evidence.py"
