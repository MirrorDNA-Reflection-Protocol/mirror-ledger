# mirror-ledger STATE

Last run: 2026-08-10 | ledger-20260810T155159 | status ok | gathered 18 | validated 18 | rejected 0 | gather calls 7/7 | gaps 0

Status: active_codex_scheduled

## Activation state and open operating decisions

- LaunchAgent ai.mirrordna.ledger-weekly remains STAGED and disabled. Paul chose
  a single durable local Codex recurring task for Monday 12:30 IST instead;
  keeping the LaunchAgent parked prevents duplicate runs. Automation id:
  `mirror-ledger-weekly`; stored state: `ACTIVE`; execution: local.
- Acceptance test 1 passed on supervised run `ledger-20260810T155159`: 7/7
  gather calls, 18/18 URLs live, zero rejects/gaps, India scope clean, lint
  clean, receipt and health ok, bus posted, commit `033e6aa`. This remains a
  pre-activation run and does not start EM-007's four-Monday clock.
- Acceptance test 3 (bus fallback under denied write) passed with visible
  receipt `receipts/ledger-bustest.json`. The LaunchAgent-specific test 5 was
  superseded before its first fire by Paul's durable Codex scheduler decision.
  Tests 2 and 4 have receipted unit-level equivalents in tests/ (see README).
- EM-007 clock: made 2026-08-10, resolve_by 2026-09-14 assumes the four weekly
  runs land 2026-08-17 / 08-24 / 08-31 / 09-07. A later activation slips the
  window; adjust resolve_by consciously if so.
- `PUSH_ON_RUN=0` remains deliberate. Codex will leave each clean Monday commit
  local for Paul's review and push; automatic public pushing remains a later
  explicit operating decision.
- Body-lattice convergence passed at 2026-08-10 16:32 IST with manifest SHA-256
  `6e7d3af8df83836473039a7bd4edbef0ab09e1a7edcf1b6dfa68a3e4d01401c2`;
  the recovery LaunchAgent was verified disabled/unloaded.

## Repair log (pipeline appends below on failures — EM-007 scoring input)
- 2026-08-10 15:16 IST | PRE-ACTIVATION SHAKEDOWN (excluded from EM-007's four scored Mondays) | run ledger-20260810T151651 FAILED at stage gather (exit 1): governed Claude wrapper rejected --allowed-tools/--model overrides. Fixed forward before activation; no automatic retry.
- 2026-08-10 15:20 IST | PRE-ACTIVATION SHAKEDOWN (excluded from EM-007's four scored Mondays) | run ledger-20260810T152010 completed mechanically but was rejected during audit: 5/7 gather calls succeeded, the MirrorState freshness guard blocked the last two, and EM-003 evidence was out of India scope. Duplicate URL intake also caused one unnecessary repeat validation. Evidence, post, receipt, and commit are preserved; fixes move forward.
- 2026-08-10T10:58:22.773401+00:00 | run ledger-bustest: MirrorBus lane append FAILED (PermissionError: [Errno 1] Operation not permitted: '/var/empty/.mirrordna'); local receipt retained at receipts/ledger-bustest.json.
