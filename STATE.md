# mirror-ledger STATE

Last run: 2026-08-10 | ledger-20260810T155159 | status ok | gathered 18 | validated 18 | rejected 0 | gather calls 7/7 | gaps 0

Status: preactivation_repair_in_progress

## Open issues (blockers before activation)

- LaunchAgent ai.mirrordna.ledger-weekly is STAGED, not installed. Deliberate:
  activation happens only after acceptance tests 1–4 pass (runbook step order).
- Acceptance test 1 has two preserved pre-activation runs. The first exposed
  forbidden launcher overrides. The second completed but is not accepted:
  MirrorState freshness expired before EM-006/EM-007, and EM-003's gathered
  evidence concerned Texas rather than India. Forward fixes refresh the
  canonical guard, deduplicate URLs, enforce an explicit India claim marker,
  and surface gather-call gaps in the post, receipt, health, and STATE.
- Acceptance tests 3 (bus fallback under denied write) and 5 (single-fire
  schedule check) remain pending. Tests 2 and 4 have receipted unit-level
  equivalents in tests/ (see README).
- EM-007 clock: made 2026-08-10, resolve_by 2026-09-14 assumes the four weekly
  runs land 2026-08-17 / 08-24 / 08-31 / 09-07. A later activation slips the
  window; adjust resolve_by consciously if so.

## Repair log (pipeline appends below on failures — EM-007 scoring input)
- 2026-08-10 15:16 IST | PRE-ACTIVATION SHAKEDOWN (excluded from EM-007's four scored Mondays) | run ledger-20260810T151651 FAILED at stage gather (exit 1): governed Claude wrapper rejected --allowed-tools/--model overrides. Fixed forward before activation; no automatic retry.
- 2026-08-10 15:20 IST | PRE-ACTIVATION SHAKEDOWN (excluded from EM-007's four scored Mondays) | run ledger-20260810T152010 completed mechanically but was rejected during audit: 5/7 gather calls succeeded, the MirrorState freshness guard blocked the last two, and EM-003 evidence was out of India scope. Duplicate URL intake also caused one unnecessary repeat validation. Evidence, post, receipt, and commit are preserved; fixes move forward.
