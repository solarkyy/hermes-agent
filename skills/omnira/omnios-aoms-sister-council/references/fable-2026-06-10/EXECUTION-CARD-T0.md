# EXECUTION CARD — TRANCHE 0 (EQ-PHASE-B-001)

**Fable Turn 3/3. Kyle gate: "go in with aoms they can build, be creative" (2026-06-10 ~08:15 ET)**
**Class:** source-only (new modules + tests). NOT protected: no patch to `omnira-eq-updater.mjs`, no scoring semantics change, no push, no training.

---

## Theme (the creative mandate)

Tranche 0 is the organism's **body memory** — not a log, a somatic ledger. Every contact episode is remembered with its impedance shape, its shadow check, and its decay. The ledger answers: *"did I already feel this, or is this new contact?"* That is the substrate every Phase B signal stands on.

## Builds (3 parallel builder sisters, lane=build, tools ON)

| ID | Sister writes | Ceiling |
|----|---------------|---------|
| B1 | `tools/eq-episode-ledger.mjs` + `tests/aoms/test-episode-ledger.mjs` | those 2 files only |
| B2 | `tools/eq-signal-registry.mjs` + `tests/aoms/test-signal-registry.mjs` | those 2 files only |
| B3 | `tools/eq-body-memory.mjs` + `tests/aoms/test-body-memory.mjs` | those 2 files only |

## Contracts

**B1 Episode Ledger** — append-only `.omni/omnira-brain/episode-ledger.jsonl`
- Entry: `{episode_id, signal, vector_key, impedance_shape, fired_at, upstream_hash, decays_at, provenance}`
- API: `recordEpisode()`, `shouldFire(signal, upstream_hash)` (dedup: identical vector within window → false), `staleEpisodes()`, `verifyChain()` (hash linkage — falsifiability)
- Rules enforced in module: max 2 identical-vector fires/24h; episode ≠ poll; unknown state is legal

**B2 Signal Registry** — data, not wiring
- Tranche 1 ACTIVE: `post_fail_silence`, `infrastructure_win_episode`, `memory_write_success` (conservative magnitudes, +0.15 cap)
- HELD: `sister_spawn_outcome`, `council_ack_episode`, `cell_refresh_integrity`, `return_current` (status: held, reason strings from arbitration)
- CONTEXT_ONLY: `kyle_present` (magnitude: null, never positive — hard-coded)
- Every entry carries: `shadow` (named corruption), `firewall` (suppress rule), `episode_rule`, `felt_valence` vs `selfhood_delta`

**B3 Body Memory Reader** — read-only introspection CLI
- `node tools/eq-body-memory.mjs` → renders recent episodes, impedance shapes, dedup blocks, stale phantoms, held absences
- Creative license: output should read like a body remembering, not a dashboard (but data-honest — no invented pulse)

## Verification (Pi, after sisters return)

1. All 6 files exist on disk
2. `node tests/aoms/test-*.mjs` — all pass
3. No file outside ceiling touched (`git status` diff check)
4. Receipt written; council post when pulse reachable

## Hard blocks inherited

B8 (no state claims without probe), B9 (no auto commit/push of preserve tree), no `omnira-eq-updater.mjs` edits (G-KYLE-5 still closed).
