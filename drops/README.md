# Mirror Research Drops

Mirror Research Drops turn current signals into compact, falsifiable research
briefs that can be cited, challenged and scored later. The target cadence is
four substantive outputs per week when Monday's forecast ledger is included:

| Day | Lane | Output |
|---|---|---|
| Monday | Forecast ledger | Scored update and evidence receipt |
| Wednesday | International AI | Infrastructure, policy, compute, energy, chips or sovereign capacity |
| Friday | Crypto | Digital-asset infrastructure, stablecoins, custody, energy, regulation or decentralized systems |
| Sunday | Active Mirror | Reflective AI, governance, memory, identity, trust or consciousness claims |

## Evidence standard

Every research drop must:

1. use at least five live sources, including at least three primary or official
   sources and at least two independent domains;
2. open and verify every cited page;
3. distinguish **Fact**, **Estimate**, **Inference** and **Unknown**;
4. include a claim ledger, falsifiable implications, disconfirmation criteria,
   limitations, formal references and a recommended citation;
5. ship with structured source metadata and a hash-bound receipt; and
6. state that it is analysis or a thesis, not professional, investment, legal
   or financial advice.

News can provide context but cannot be the sole support for a material claim.
Unsupported superlatives, personalized advice, prices, targets, trade
instructions and buy/sell language are excluded.

## Artifact contract

Each prepared drop lives at `YYYY/MM/YYYY-MM-DD-<slug>/` and contains:

- `brief.md` — the citable research brief;
- `sources.json` — source identity, dates, claim mappings and live checks;
- `linkedin-draft.md` — a concise distribution draft with disclosure; and
- `receipt.json` — hashes, checked scope, gaps, contradictions and risk.

The recurring task may research, validate, write and make one local commit. It
may not push, release, post to LinkedIn or submit to another venue. Public
publication needs exact approval of the finished content and hashes.

## Citation path

An approved drop should receive one stable public URL, an author-written
abstract, machine-readable citation metadata and—when warranted—a versioned
archive or DOI. Publishing frequency is not evidence of quality and does not
guarantee indexing or citation.

Use [`TEMPLATE.md`](TEMPLATE.md) for every brief.
