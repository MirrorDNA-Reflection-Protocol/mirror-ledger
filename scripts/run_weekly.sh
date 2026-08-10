#!/bin/bash
# mirror-ledger weekly entry point. One scheduled run per week — never a poller.
# LaunchAgent: ai.mirrordna.ledger-weekly (Mondays 12:30 local/IST).
# Contract: gather -> URL-validate -> draft -> lint -> attest -> commit -> stop.
# The pipeline NEVER publishes a post; Paul reviews and publishes manually.
# On failure: write fail receipt + STATE.md entry, exit nonzero, NO retry.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
. "$REPO_ROOT/config.env"

RUN_DATE="$(date +%Y-%m-%d)"
RUN_ID="ledger-$(date +%Y%m%dT%H%M%S)"
STAGE="init"
LOCK_DIR="$REPO_ROOT/.run-lock"
LOCK_HELD="0"

log() { echo "[mirror-ledger $RUN_ID] $*" >&2; }

# Resolve a python that can read YAML. The governance venv is preferred; it is
# the interpreter the body's own hooks run on.
PYBIN="${PYBIN_OVERRIDE:-}"
if [ -z "$PYBIN" ]; then
  for cand in "$HOME/.mirrordna/venv/bin/python" /opt/homebrew/bin/python3 /usr/bin/python3; do
    if [ -x "$cand" ] && "$cand" -c "import yaml" >/dev/null 2>&1; then
      PYBIN="$cand"
      break
    fi
  done
fi
if [ -z "$PYBIN" ]; then
  log "FATAL: no python interpreter with the yaml module; set PYBIN_OVERRIDE in config.env"
  exit 78
fi
export PYBIN RUN_ID RUN_DATE REPO_ROOT CLAUDE_BIN MODEL GATHER_TIMEOUT URL_TIMEOUT

cleanup_and_report() {
  status=$?
  if [ "$LOCK_HELD" = "1" ]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
  if [ "$status" -ne 0 ]; then
    log "FAILED at stage=$STAGE exit=$status"
    "$PYBIN" "$REPO_ROOT/scripts/write_health.py" fail "$RUN_ID" "$STAGE" || true
    printf -- '- %s | run %s FAILED at stage %s (exit %s). No auto-retry; fix forward and note the repair here (EM-007 scoring input).\n' \
      "$(date '+%Y-%m-%d %H:%M %Z')" "$RUN_ID" "$STAGE" "$status" >> "$REPO_ROOT/STATE.md" || true
  fi
  exit "$status"
}
trap cleanup_and_report EXIT

STAGE="lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "another run holds $LOCK_DIR; refusing to double-run"
  exit 75
fi
LOCK_HELD="1"

STAGE="layout"
mkdir -p "$REPO_ROOT/evidence/_incoming/$RUN_ID" "$REPO_ROOT/posts" "$REPO_ROOT/receipts" "$HOME/.mirrordna/logs"

STAGE="gather"
log "gathering evidence via headless subscription Claude ($MODEL)"
bash "$REPO_ROOT/scripts/gather_evidence.sh"

STAGE="validate"
log "validating every evidence URL (fabrication guard)"
"$PYBIN" "$REPO_ROOT/scripts/validate_urls.py" --run-id "$RUN_ID"

SUMMARY_FILE="$REPO_ROOT/evidence/_incoming/$RUN_ID/summary.json"
GATHERED="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1]))['gathered'])" "$SUMMARY_FILE")"
VALIDATED="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1]))['validated'])" "$SUMMARY_FILE")"
REJECTED="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1]))['rejected'])" "$SUMMARY_FILE")"
GATHER_CALLS="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1])).get('gather_calls', 0))" "$SUMMARY_FILE")"
GATHER_SUCCESSES="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1])).get('gather_successes', 0))" "$SUMMARY_FILE")"
GATHER_GAPS="$("$PYBIN" -c "import json,sys;print(json.load(open(sys.argv[1])).get('gather_gaps', 0))" "$SUMMARY_FILE")"
log "evidence: gathered=$GATHERED validated=$VALIDATED rejected=$REJECTED gather_calls=$GATHER_SUCCESSES/$GATHER_CALLS gaps=$GATHER_GAPS"

STAGE="draft"
log "rendering weekly post deterministically from VALIDATED evidence only"
bash "$REPO_ROOT/scripts/draft_post.sh"

STAGE="lint"
POST_FILE="$REPO_ROOT/posts/$RUN_DATE.md"
log "linting draft for ticker/price/buy-sell language"
"$PYBIN" "$REPO_ROOT/scripts/lint_post.py" "$POST_FILE"

STAGE="attest"
log "writing attestation receipt (repo-first, bus-second)"
bash "$REPO_ROOT/scripts/attest.sh"

STAGE="health"
HEALTH_STAGE="done"
if [ "$GATHER_GAPS" -gt 0 ]; then
  HEALTH_STAGE="done_with_gather_gaps"
fi
"$PYBIN" "$REPO_ROOT/scripts/write_health.py" ok "$RUN_ID" "$HEALTH_STAGE" \
  --gathered "$GATHERED" --validated "$VALIDATED" --rejected "$REJECTED" \
  --gather-calls "$GATHER_CALLS" --gather-successes "$GATHER_SUCCESSES" --gather-gaps "$GATHER_GAPS" \
  --post "posts/$RUN_DATE.md"

"$PYBIN" - "$REPO_ROOT/STATE.md" "$RUN_ID" "$RUN_DATE" "$GATHERED" "$VALIDATED" "$REJECTED" "$GATHER_SUCCESSES" "$GATHER_CALLS" "$GATHER_GAPS" <<'PYEOF'
import io, re, sys
path, run_id, run_date, gathered, validated, rejected, successes, calls, gaps = sys.argv[1:10]
line = f"Last run: {run_date} | {run_id} | status ok | gathered {gathered} | validated {validated} | rejected {rejected} | gather calls {successes}/{calls} | gaps {gaps}"
text = io.open(path, encoding="utf-8").read()
new, n = re.subn(r"(?m)^Last run: .*$", line, text, count=1)
if n == 0:
    new = line + "\n" + text
io.open(path, "w", encoding="utf-8").write(new)
PYEOF

# Commit last so a successful run leaves all repository-owned state inside the
# weekly commit. If this stage fails, the EXIT trap overwrites the health
# receipt with fail and records the commit-stage failure in STATE.md.
STAGE="commit"
if [ -d "$REPO_ROOT/.git" ]; then
  git -C "$REPO_ROOT" add -A
  if git -C "$REPO_ROOT" commit -m "ledger: weekly run $RUN_DATE ($GATHERED items, $VALIDATED validated)"; then
    log "committed run $RUN_ID"
  else
    log "nothing new to commit"
  fi
  if [ "$PUSH_ON_RUN" = "1" ]; then
    if git -C "$REPO_ROOT" remote get-url origin >/dev/null 2>&1; then
      git -C "$REPO_ROOT" push origin HEAD
      log "pushed to origin"
    else
      log "PUSH_ON_RUN=1 but no origin remote; flagging in STATE.md"
      printf -- '- %s | run %s: PUSH_ON_RUN=1 but no origin remote configured.\n' \
        "$(date '+%Y-%m-%d %H:%M %Z')" "$RUN_ID" >> "$REPO_ROOT/STATE.md"
    fi
  fi
else
  log "WARNING: repo has no .git yet; commit skipped (executor runbook step pending)"
  printf -- '- %s | run %s completed WITHOUT a git commit (.git missing — runbook step pending).\n' \
    "$(date '+%Y-%m-%d %H:%M %Z')" "$RUN_ID" >> "$REPO_ROOT/STATE.md"
fi

log "run complete: draft at posts/$RUN_DATE.md — awaiting Paul's review. Pipeline stops here by design."
