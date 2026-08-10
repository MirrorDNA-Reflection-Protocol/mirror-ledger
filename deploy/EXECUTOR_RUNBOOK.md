# mirror-ledger — Executor Runbook (gated steps)

**Why this exists:** the authoring session (Claude Code, 2026-08-10) ran behind
the deterministic shell gate (`read_only_shell` disabled; only the typed
`mirror-run verify|deps` lane). Everything below needs a shell-capable governed
session — Codex as execution foreman, or Paul for the two human-authority steps.
Already receipted from the authoring session: py_compile of all 12 Python files
(`project-exec-20260810T091409Z-8c8e15e799`) and 23/23 pytest passing
(`project-exec-20260810T091442Z-37edd1b08c`) — including the poison-URL and
"buy NTPC at ₹344" lint fixtures (acceptance tests 2 and 4 at unit level).

Repo: `/Users/pauldesai/repos/mirror-ledger`. Run steps in order; stop on any red.

## 0. Preflight (Codex)

```
date +%Z                      # expect IST — the plist schedules 12:30 local
/opt/homebrew/bin/python3 -c "import yaml, pytest; print('deps ok')"
gh auth status                # must be logged in with MirrorDNA-Reflection-Protocol access
/Users/pauldesai/bin/claude --version   # governed wrapper resolves and runs
```

## 1. Seed predictions (PAUL — content authority)

Paste EM-002..EM-006 VERBATIM from *The Electric Mind — Public Edition v2* into
`predictions.yaml` (template comment at the bottom of the file), set each
`status: open`. Confirm EM-001's wording against the source (it was seeded from
the handoff's schema block). Then re-verify:

```
/Users/pauldesai/bin/mirror-run --project /Users/pauldesai/repos/mirror-ledger verify -- python3 -m pytest tests
```

## 2. Git init + first commit (Codex)

```
cd /Users/pauldesai/repos/mirror-ledger
git init -b main
git add -A
git commit -m "ledger: scaffold weekly pipeline (fabrication guard, receipts, staged launchagent)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

## 3. Public org repo (PAUL approval required — publishing escalation)

Org confirmed to exist with no mirror-ledger repo (checked 2026-08-10 via web).

```
gh repo create MirrorDNA-Reflection-Protocol/mirror-ledger --public --source /Users/pauldesai/repos/mirror-ledger --push
```

## 4. Acceptance test 1 — supervised dry run (Codex)

```
bash /Users/pauldesai/repos/mirror-ledger/scripts/run_weekly.sh
```

Expect: gather runs one headless subscription-Claude call per open prediction;
`evidence/_incoming/<run>/` raw + items JSON; validated items in
`evidence/EM-XXX.yaml`; drops in `evidence/_rejected.log`; draft at
`posts/<date>.md` with the counts footer; receipt in `receipts/`; health receipt
`~/.mirrordna/health/mirror_ledger_weekly.json` status ok; a git commit
`ledger: weekly run ...`. If the claude CLI rejects a flag (e.g. --allowed-tools
naming drift), fix scripts/config NOW — pre-activation shakedown repairs do not
count against EM-007; the four scored runs start at activation.

## 5. Acceptance test 3 — MirrorBus down fallback (Codex)

Force the bus append to fail by pointing HOME at an unwritable dir for the
attest step only (never chmod the real bus — other writers use it):

```
cd /Users/pauldesai/repos/mirror-ledger
HOME=/var/empty REPO_ROOT="$PWD" RUN_ID=ledger-bustest RUN_DATE=$(date +%Y-%m-%d) /opt/homebrew/bin/python3 scripts/attest.py
```

Expect: exit 0, `receipts/ledger-bustest.json` with `"posted": false` and an
error string, and a STATE.md flag line. Delete the test receipt + STATE line
after checking, or leave them as visible test evidence (note which you did).

## 6. Acceptance test 5 — fires once and only once (Codex)

> **Superseded 2026-08-10 before the first test fire:** Paul selected one
> durable local Codex recurring task as the production scheduler. Do not load
> this LaunchAgent while that automation is active; the repository lock is a
> safety net, not permission to run duplicate schedulers. The plist remains a
> parked recovery path.

```
mkdir -p ~/.mirrordna/logs
cp deploy/ai.mirrordna.ledger-weekly.plist ~/Library/LaunchAgents/
```

Edit `~/Library/LaunchAgents/ai.mirrordna.ledger-weekly.plist`: replace the
single `StartCalendarInterval` dict with an ARRAY of two dicts ~5 and ~10
minutes ahead (Weekday/Hour/Minute of today), then:

```
launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.mirrordna.ledger-weekly.plist
```

Watch `~/.mirrordna/logs/ledger-weekly.log`: exactly one run per fire (the
`.run-lock` dir also refuses overlap). Then bootout, restore the weekly
Monday-12:30 dict from `deploy/`, and bootstrap again:

```
launchctl bootout gui/501/ai.mirrordna.ledger-weekly
cp deploy/ai.mirrordna.ledger-weekly.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/501 ~/Library/LaunchAgents/ai.mirrordna.ledger-weekly.plist
launchctl print gui/501/ai.mirrordna.ledger-weekly | head -20
```

## 7. Manifest + lattice convergence (Codex)

Merge the `services:` block from `deploy/manifest_patch.yaml` into
`~/.activemirror/body/MANIFEST.yaml` (keep `status: parked` until steps 4-6 are
green, then set `status: active`), then:

```
python3 ~/.mirrordna/scripts/body_lattice_sync.py --apply
```

## 8. Post-activation

- After the first clean scheduled Monday, consider `PUSH_ON_RUN="1"` in
  `config.env` so run commits get public timestamps (Paul's call).
- If activation slipped past 2026-08-17, adjust EM-007 `resolve_by`
  consciously (four Mondays + one week).
- Weekly loop for Paul: read `posts/<date>.md`, publish manually, `git push`
  if PUSH_ON_RUN=0. Target ≤ 15 minutes.

## Known deviations from the handoff (already documented in README)

ai.mirrordna.* agent name; health-receipt/STATE.md instead of the nonexistent
current_state.json/open_loops.md; evidence in evidence/*.yaml instead of
rewriting predictions.yaml. EM-001..006 were source-transcribed on 2026-08-10
from the Downloads copy of *The Electric Mind — Public Edition v2* and bound to
its SHA-256 in predictions.yaml.
