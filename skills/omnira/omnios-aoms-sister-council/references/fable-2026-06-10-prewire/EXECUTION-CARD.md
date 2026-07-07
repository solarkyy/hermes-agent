# EXECUTION CARD — EQ_PHASE_B_TRANCHE1_PREWIRE_V0

**Kyle CEO directive — source/test-only. Fable orchestrates; sisters build; Pi proves.**

## Build B1 — `tools/eq-phase-b-prewire.mjs`

Export `evaluateEvent(event, opts)` and CLI `node tools/eq-phase-b-prewire.mjs --event <path.json>`.

Pipeline (in order):
1. Validate event shape (signal, vector_key, upstream_hash required; evidence object required for active signals)
2. Registry lookup — `getSignal`, `assertFireable` path for active; held → BLOCKED + hold_reason; unknown → BLOCKED
3. `kyle_present` in context → annotate `context.kyle_present: true` only — **never** proposed_eq_delta, verdict CONTEXT_ONLY if signal is kyle_present
4. Dedup — `shouldFire(signal, vector_key, upstream_hash, opts)` — **READ ONLY**. Default: read real ledger path. opts.ledgerPath for tests only.
5. If would fire → build `proposed_episode` object (full entry shape) but **do not call recordEpisode**
6. Return dry-run envelope with `mutations: { ledger: false, eq_state: false }` always

Also export `evaluateEventBatch(events, opts)` for batch dry-run.

**Hard law:** grep the file — zero calls to `recordEpisode`, `appendFileSync` on DEFAULT_LEDGER, or any write to eq-state path.

## Build B2 — `tools/tests/eq-phase-b-prewire.test.mjs`

Follow pattern of `tools/tests/eq-fallback.test.mjs` (temp dirs, assert, no jest).

Required cases (CEO directive):
- active + evidence → WOULD_FIRE + proposed_episode + proposed_eq_delta
- duplicate (pre-seed temp ledger via recordEpisode on TEMP path only) → BLOCKED dedup
- held signal → BLOCKED
- kyle_present → CONTEXT_ONLY, no delta
- missing evidence → BLOCKED
- **non-mutation proof:** snapshot real ledger + eq-state mtime/size before/after full test run → unchanged

## Build B3 — docs (GPT-5.5)

- `docs/specs/eq-phase-b-tranche1-prewire-v0.md` — event schema, output schema, pipeline, hard blocks, relationship to Tranche 0 modules
- `docs/receipts/2026-06-10-eq-phase-b-tranche1-prewire-v0.md` — fill template; Pi completes verification section after tests

## Panel P1 — Adversarial (Nemotron, no tools)

Attack: can this module accidentally write? Can dry-run be mistaken for live? Can reading real ledger while testing mutate? Recommend holds.

## Panel P2 — Test Designer (Nemotron, no tools)

Grade CEO test requirements vs B2 plan. List any missing fail-before case. Propose one adversarial fixture (e.g. event that looks like win but is cycling task).

## Pi verification checklist

1. All 4 files exist
2. `node tools/tests/eq-phase-b-prewire.test.mjs` exit 0
3. `rg 'recordEpisode|appendFileSync.*episode-ledger|writeFileSync.*eq-state' tools/eq-phase-b-prewire.mjs` — recordEpisode must NOT appear (only shouldFire import from ledger)
4. Real ledger mtime unchanged after test suite
5. Report in CEO format

## Report template (Pi fills)

```
EQ_PHASE_B_TRANCHE1_PREWIRE_V0
Verdict: PASS_SOURCE_TEST / PARTIAL / BLOCKED
Files changed: ...
Tests: command + result
Confirmed non-actions: ...
Risks/caveats: ...
Next gate needed: G-KYLE-5 live wiring
```
