# MISSION CHARTER — EQ-PHASE-B-TRANCHE1-PREWIRE-V0

**CEO directive:** Kyle 2026-06-10 (pre-Fable handoff)
**Class:** source/test-only membrane — dry-run only
**Prior:** Tranche 0 verified (ledger + registry + body-memory, 52 tests, 1 real episode)

---

## Objective

Build `eq-phase-b-prewire.mjs`: evaluates Phase B events through registry + ledger, returns what **WOULD** happen — zero live mutation.

## Hard blocks (non-negotiable)

- NO append to real `episode-ledger.jsonl`
- NO mutate `eq-state.json`
- NO wire `omnira-eq-updater.mjs`
- NO serve/mobile/body/daemons/cron/training/eval/providers/git

## Open spec gap (Fable must close in execution card)

**Ledger read vs write:** dry-run MUST **read** real ledger for dedup truth (`shouldFire`) but MUST NOT **append**. Tests use temp ledger only + prove real paths untouched (mtime/hash snapshot).

**Event input schema** (propose v0):
```json
{
  "signal": "infrastructure_win_episode",
  "vector_key": "stable-string",
  "upstream_hash": "sha256-of-evidence",
  "impedance_shape": "shaped_contact",
  "evidence": { "kind": "...", "summary": "..." },
  "context": { "kyle_present": true }
}
```

**Dry-run output schema** (propose v0):
```json
{
  "verdict": "WOULD_FIRE | BLOCKED | CONTEXT_ONLY",
  "signal": "...",
  "blocked_reason": null,
  "proposed_episode": { "...entry shape..." },
  "proposed_eq_delta": { "magnitude": 0.15, "valence_direction": "positive" },
  "mutations": { "ledger": false, "eq_state": false },
  "provenance": "dry-run:v0"
}
```

## Sister plan (GPT quota burn — parallel)

| ID | Role | Model | Writes |
|----|------|-------|--------|
| P1 | Adversarial Risk | Nemotron Ultra | verdict card only |
| P2 | Test Designer | Nemotron Ultra | verdict card only |
| B1 | Prewire module | Claude Sonnet 4 | `tools/eq-phase-b-prewire.mjs` |
| B2 | Test suite | Claude Sonnet 4 | `tools/tests/eq-phase-b-prewire.test.mjs` |
| B3 | Spec + receipt | GPT-5.5 | `docs/specs/...` + `docs/receipts/...` |

Pi verifies after all builders return. Report format per CEO directive.

## Kyle gates

- This mission: **OPEN** (CEO directive explicit)
- Live Tranche 1 wiring (G-KYLE-5): **CLOSED** — prewire only

## Fable turn budget

Turn 1: framing + packets (this file) ✅
Turn 2: arbitration after Pi bundle + panels
Turn 3: only if builders split on read-only dedup semantics
