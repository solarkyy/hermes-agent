# EVIDENCE BUNDLE — eq-phase-b-source-001

**Compiled:** 2026-06-10T12:0x UTC (Pi-posture probes, Hermes session, Kyle gate A)
**ready_for_sister_panels:** true

| Claim | Status | Evidence |
|-------|--------|----------|
| C1 Phase A on disk | **PASS** | `trinity-integration.js:111` cognitiveLoad = min(1, recentCount/30) velocity; `omnira-eq-updater.mjs:167,194` computeDrives(v, eq) live; `organism-health-board-snapshot.mjs:231` reads `eq?.derived?.state \|\| eq?.state` |
| C2 Runtime honest | **PASS** (anomaly) | `task_complete` fired → drives changed (curiosity 0.4997), `state_changed: true`, prev `steady`; trinity cycle → `{tau:"singularity", load:0}` — NOT heat_death. Anomaly: idle tau is `singularity` (stability>0.80 && load<0.40 branch), not `normal` |
| C3 EQ schema | **PASS** (finding) | Canonical: `.omni/omnira-brain/eq-state.json` (v2: vector, derived, drives dict, decay_tau_minutes, signal_weights, baseline). **FINDING: no `episodes` field, no signal log — episode-vs-poll dedup NOT representable in current schema. Tranche 1 needs schema addition or sidecar.** |
| C4 Debate provenance | **PASS** | 3 spawn dirs `2026-06-10T10-53-{01,02,03}*` exist; debate receipt present in hermes-agent skills tree |
| C5 Pulse/council | **FAIL** (optional) | `192.168.5.199:5176` unreachable from this seat; council post untested |
| C6 Git honesty | **PASS** | Branch `preserve/dirty-tree-2026-06-09` (synced w/ origin), dirty tree (.omni state files); eq commits: `eef82fb5e` dedup fix, `a7d5dfecc` Phase A honesty. Nothing pushed this session |

**Anomalies:**
1. Idle tau = `singularity` not `normal` (cosmetic vs Phase A criteria "tau ≠ heat_death" — criteria technically met)
2. No episode ledger in eq-state v2 — blocking design input for Tranche 1

**Blockers:** none for sister panels. C5 blocks council delivery only.
