# mirror-ledger STATE

Last run: never (scaffolded 2026-08-10; first scheduled run is the Monday 12:30 IST after activation — see deploy/EXECUTOR_RUNBOOK.md)

Status: preactivation_repair_in_progress

## Open issues (blockers before activation)

- LaunchAgent ai.mirrordna.ledger-weekly is STAGED, not installed. Deliberate:
  activation happens only after acceptance tests 1–4 pass (runbook step order).
- Acceptance test 1 reached the gather stage and correctly stopped when the
  governed Claude wrapper rejected launcher overrides. The pre-activation fix
  removes those overrides and makes drafting deterministic; clean rerun pending.
- Acceptance tests 3 (bus fallback under denied write) and 5 (single-fire
  schedule check) remain pending. Tests 2 and 4 have receipted unit-level
  equivalents in tests/ (see README).
- EM-007 clock: made 2026-08-10, resolve_by 2026-09-14 assumes the four weekly
  runs land 2026-08-17 / 08-24 / 08-31 / 09-07. A later activation slips the
  window; adjust resolve_by consciously if so.

## Repair log (pipeline appends below on failures — EM-007 scoring input)
- 2026-08-10 15:16 IST | PRE-ACTIVATION SHAKEDOWN (excluded from EM-007's four scored Mondays) | run ledger-20260810T151651 FAILED at stage gather (exit 1): governed Claude wrapper rejected --allowed-tools/--model overrides. Fixed forward before activation; no automatic retry.
