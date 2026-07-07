# RECEIPT — TRANCHE 0 BUILD (EQ-PHASE-B-001)

**Date:** 2026-06-10 ~08:30 ET
**Gate:** Kyle — "go in with aoms they can build, be creative"
**Verb:** written locally (omnios repo, untracked — NOT committed, NOT pushed; B9 honored)

---

## Built (6 files, omnios repo)

| File | Author | Size |
|------|--------|------|
| `tools/eq-episode-ledger.mjs` | B1 `sister-c0284167` (Sonnet) | 10.1 KB |
| `tests/aoms/test-episode-ledger.mjs` | B1 | 13.0 KB |
| `tools/eq-signal-registry.mjs` | B2 `sister-35b06ee2` (Sonnet, timed out after writing module) | 13.4 KB |
| `tests/aoms/test-signal-registry.mjs` | B2R `sister-?` recovery spawn (Sonnet, 60s) | 7.6 KB |
| `tools/eq-body-memory.mjs` | B3R recovery spawn (Sonnet, 78s; first B3 timed out empty) | 6.2 KB |
| `tests/aoms/test-body-memory.mjs` | B3R | 6.3 KB |

**Orchestrator interventions:** 1 line — `eq-body-memory.mjs` empty-ledger guard now respects `--json` (machine shape on empty, prose only in prose mode). Re-verified after fix.

## Pi verification (this session, live runs)

- Tests: **14 + 23 + 15 = 52 pass, 0 fail** (`node tests/aoms/test-*.mjs`)
- Ceiling: `git status` shows only the 6 intended files (+ tests/aoms dir) — no out-of-ceiling writes
- Registry invariants live: `validateRegistry()` true; active = post_fail_silence, infrastructure_win_episode, memory_write_success; kyle_present magnitude null + unfireable
- End-to-end smoke: recorded real episode `ep-1781094383723-2499aace` (signal infrastructure_win_episode, vector tranche0-body-memory-substrate, shaped_contact, L2); `shouldFire` same vector+hash → `{fire:false, reason:"dedup_same_hash_inside_decay"}`; `verifyChain` → `{ok:true, entry_count:1}`; reader renders `shaped_contact ×1 — reached, and the reach came home`

## Builder design decisions worth keeping (B1 stdout)

1. `episode_id` short-hash = sha256(signal:vector_key:fired_at) — context fingerprint, collisions detectable not masked
2. `prev_hash` binds to bytes-on-disk, not parsed object — serializer drift = chain break (anti-forgery)
3. `SIGNAL_DECAY_WINDOWS` map — per-signal somatic half-lives without API change

## Still blocked / next gates

- Council post: pulse `192.168.5.199:5176` unreachable from this seat (C5 still FAIL) — deliver when reachable
- Commit: tree is `preserve/dirty-tree-2026-06-09`; B9 forbids auto-commit — Kyle says "commit" to get hashes
- Tranche 1 wiring (`omnira-eq-updater.mjs` reads registry + ledger): G-KYLE-5 still closed
- Held signals (`return_current`, `cell_refresh_integrity`, …): unlock after Tranche 0 settles

## Spawn provenance (all L1 → Pi-verified this session)

Panels: `12-02-49 ea013613` (audit), `12-02-51 b1e50d84` (adversarial), `12-02-53 1d9226fd` (test design)
Builders: `12-17-37 c0284167` (B1 ok), `12-17-40 35b06ee2` (B2 timeout/partial), `12-17-45 f5e029a5` (B3 timeout/empty), + 2 recovery spawns ok
