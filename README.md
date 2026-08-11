# mirror-ledger

Weekly forecast-ledger pipeline for the MirrorDNA public prediction ledger — and,
deliberately, the live acceptance test of the MirrorDNA long-horizon stack.
EM-007 in `predictions.yaml` is the pipeline betting on itself: four consecutive
clean weekly runs, zero fabricated citations, zero manual repairs.

**The pipeline never publishes.** Every run ends at a draft plus receipts; Paul
reviews and publishes manually.

## Published thesis

- [The Electric Mind — India AI–Power Investment Thesis](papers/the-electric-mind-2026/README.md)

## Weekly run (Mondays 12:30 IST, one shot, never a poller)

`scripts/run_weekly.sh` (called by the active Codex schedule; staged
LaunchAgent `ai.mirrordna.ledger-weekly` is recovery-only):

0. **State preflight** — refresh and validate the canonical MirrorState runtime
   guard; fail closed before any model call if the proof cannot be written.
1. **Gather** — one headless subscription-Claude call per `status: open`
   prediction, with WebSearch/WebFetch, demanding
   `{claim, url, date, quote_fragment}` JSON. URLs are deduplicated before
   validation; `india-ai-power` claims must explicitly state their India scope.
2. **Validate** — `validate_urls.py` HTTP-fetches every URL. Non-2xx or
   unreachable → `evidence/_rejected.log`, never the ledger.
3. **Draft** — `draft_post.py` deterministically writes `posts/YYYY-MM-DD.md`
   from validated evidence only. It makes no model or tool call, so it cannot
   invent or fetch sources it was never given.
4. **Lint** — `lint_post.py` fails the run on ticker/price/buy-sell language
   ("buy NTPC at ₹344" kills the run) and on any URL not in the validated set.
5. **Attest** — `attest.py` writes `receipts/<run_id>.json`
   (sha256 of `predictions.yaml` + evidence tree + post, host clock), then
   appends to the MirrorBus lane `~/.mirrordna/bus/mirror_ledger_attestations.jsonl`.
   Receipt-first, transport-second: a bus failure is flagged, never fatal.
6. **Commit** — `ledger: weekly run YYYY-MM-DD (N items, M validated)`.
   Push is off by default (`PUSH_ON_RUN=0` in `config.env`); flip to 1 after the
   first supervised run so commits get public timestamps.
7. **Stop.** Health receipt at `~/.mirrordna/health/mirror_ledger_weekly.json`
   (`ok|fail`). Failures also append to the repair log in `STATE.md` and never
   auto-retry. Partial gather-call gaps remain visible in the post footer,
   attestation receipt, health receipt, and `STATE.md`.

## The fabrication guard (four layers)

| Layer | Where | Rule |
|---|---|---|
| 1 | `gather_evidence.py` | no URL → item dropped at intake; model told `[]` beats invention |
| 2 | `validate_urls.py` | every URL fetched live; non-2xx → `_rejected.log` |
| 3 | `draft_post.py` | deterministic renderer gets validated items only; no model/tool call |
| 4 | `lint_post.py` | any URL outside the validated set fails the run |

A fabricated citation would have to defeat all four before it could even reach
the *draft* that Paul still reviews by hand.

## Layout

```
predictions.yaml   source of truth; humans edit, pipeline only reads
evidence/          EM-XXX.yaml validated items; _rejected.log; _incoming/<run>/ raw audit
posts/             drafted updates (never auto-published)
papers/            manually approved, published long-form research
receipts/          attestation receipts per run
scripts/           pipeline (bash entry points + python workers)
tests/             pytest suite incl. poison-URL and finance-lint fixtures
deploy/            staged LaunchAgent plist, MANIFEST patch, executor runbook
STATE.md           last run, blockers, repair log (EM-007 scoring input)
```

## Deviations from the 2026-08-10 handoff (deliberate, all visible)

- **LaunchAgent name** `ai.mirrordna.ledger-weekly`, not `com.mirrordna.ledger.weekly`
  — the body's hardening standard names agents `ai.mirrordna.*`.
- **State integration**: the handoff's `~/.mirrordna/current_state.json` and
  `~/.mirrordna/open_loops.md` do not exist on this body. The real conventions
  are used instead: a health receipt (`mirror_ledger_weekly.json`), the bus
  attestation lane, and `STATE.md`.
- **Evidence placement**: validated evidence is appended to `evidence/EM-XXX.yaml`
  rather than into `predictions.yaml`'s `evidence:` field, so the pipeline never
  rewrites the human-owned file (which would destroy comments and invite drift).
- **Seeding**: EM-007 comes from the handoff. EM-001..006 were transcribed from
  the six-row forecast table in *The Electric Mind — Public Edition v2* found
  in Downloads and are provenance-commented with source hashes. An exact-value
  regression test protects the statements, criteria, dates, and probabilities
  from transcription drift.
- **Model pin**: headless calls pin `claude-opus-4-6` per
  `~/.mirrordna/policy/model_registry.json`, via the governed wrapper
  `/Users/pauldesai/bin/claude`, with `ANTHROPIC_API_KEY` stripped —
  subscription lane only.

## Manual supervised run

```bash
bash /Users/pauldesai/repos/mirror-ledger/scripts/run_weekly.sh
```

## Durable scheduler

The active schedule is a local Codex recurring task, Mondays at 12:30 IST,
which invokes the exact script above and verifies its receipt, health record,
commit, and draft. The staged LaunchAgent remains disabled so two schedulers
can never race; its plist is retained under `deploy/` only as a recovery path.

## Tests

```bash
/Users/pauldesai/bin/mirror-run --project /Users/pauldesai/repos/mirror-ledger deps -- uv sync
/Users/pauldesai/bin/mirror-run --project /Users/pauldesai/repos/mirror-ledger verify -- pytest
```

Unit fixtures cover acceptance tests 2 (poison URL rejected end-to-end) and 4
(lint kills "buy NTPC at ₹344"). Acceptance tests 1, 3, 5 (live dry run, bus
fallback, single-fire schedule check) are in `deploy/EXECUTOR_RUNBOOK.md`.

## Definition of working

Four green Mondays. Paul's weekly cost ≤ 15 minutes (read draft, publish, push).
EM-007 resolves `confirmed` on 2026-09-14. Then — and only then — v2 talk.
