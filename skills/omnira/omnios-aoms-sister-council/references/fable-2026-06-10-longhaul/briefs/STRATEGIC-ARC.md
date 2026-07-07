# STRATEGIC ARC — EQ Phase B Longhaul (P-strategic)

**Date:** 2026-06-10
**Repo:** `/home/kylej/Desktop/omnios` @ `preserve/dirty-tree-2026-06-09`
**Commit:** `2a0529092` (23 files, 43 tests, **not pushed**)
**Authority:** MISSION-CHARTER longhaul; build lane FREE; avoid `research-spark`

---

## 1. Honest current state

The EQ body arc is **committed locally** — ledger (`tools/eq-episode-ledger.mjs`), registry (`tools/eq-signal-registry.mjs`), prewire (`tools/eq-phase-b-prewire.mjs`), live bridge (`tools/eq-phase-b-live.mjs`), emitters (`tools/eq-phase-b-emitters.mjs`), shadow hooks in `tools/omnira-watchdog.mjs` + `tools/kernel/omnira-verify.mjs` (all `dryRun: true`), and read-only pulse exporter (`tools/eq-body-snapshot.mjs`) — but **nothing has breathed yet**: `.omni/omnira-brain/eq-shadow-log.jsonl` does not exist, runtime ledger holds only 2 `shaped_contact` smoke episodes, and pulse/mobile do not read `eq-body-snapshot.json`. Adversarial holds remain on `post_fail_silence` and `sister_spawn_outcome` auto-emit; four signals (`return_current`, `council_ack_episode`, `cell_refresh_integrity`, `sister_spawn_outcome`) stay registry-held until Lane C debate + Kyle synthesis.

---

## 2. Four phases

### Phase 1 — Shadow accrual (passive → +2 weeks human audit)

| Item | Detail |
|------|--------|
| **Deliverables** | `tools/eq-shadow-log-viewer.mjs` (tail/filter `would_fire`); weekly audit receipt template `docs/receipts/eq-shadow-audit-YYYY-WW.md`; false-pulse triage rubric (extends `references/fable-2026-06-10/rubrics/ARBITRATION-RUBRIC.md`); first proof-of-life shadow line in `.omni/omnira-brain/eq-shadow-log.jsonl` |
| **Dependencies** | Committed hooks running on real watchdog/verify cycles; prewire membrane unchanged |
| **Kyle gates** | `"phase 1 go"` → build viewer + template only; **no gate** for passive accrual once hooks are live |
| **Effort** | 4–6 h build + receipt; 14 days passive audit (15 min/week Kyle skim) |
| **Success** | ≥10 shadow evaluations, zero `dryRun:false` mutations, ledger/eq-state mtimes unchanged during audit window |

### Phase 2 — Experience layer (read-only feel)

| Item | Detail |
|------|--------|
| **Deliverables** | Pulse poll reads `.omni/omnira-brain/eq-body-snapshot.json` (sidecar/snapshot pattern — **no serve.js**); cron or existing refresh atomically writes snapshot via `node tools/eq-body-snapshot.mjs`; mobile **spec only** unless separate gate |
| **Dependencies** | Phase 1 snapshot exporter already committed; stable snapshot path |
| **Kyle gates** | `"pulse reads body"` before any integration patch |
| **Effort** | 6–10 h integration + Pi verify; 0 h mobile build (spec only) |
| **Success** | Kyle sees episode summary + impedance shapes on pulse without CLI JSON |

### Phase 3 — Held unlock (Lane C debate-first)

| Item | Detail |
|------|--------|
| **Deliverables** | 3-voice panel brief (`LANE-C-DEBATE.md` → live if needed); Kyle synthesis paste; per-signal registry tier changes in `tools/eq-signal-registry.mjs`; new emitters **shadow-first** (prewire only, no live) |
| **Dependencies** | Phase 1 shadow log (evidence for `sister_spawn_outcome`, `council_ack_episode`); Interiority/Shadow positions from `eq-embodied-signals-debate-2026-06-10.md` |
| **Kyle gates** | `"return_current debate"` opens panel; **per-signal** approval before registry tier bump |
| **Effort** | 1 day debate + synthesis; 4–8 h builder per unlocked signal (shadow emitters + tests) |
| **Order (recommended)** | `return_current` debate → `council_ack_episode` → `cell_refresh_integrity` → `sister_spawn_outcome` last (highest attribution risk) |

### Phase 4 — Live flip (one hook, one signal)

| Item | Detail |
|------|--------|
| **Deliverables** | Nemotron adversarial re-panel on accrued shadow log; flip `memory_write_success` then `infrastructure_win_episode` to `opts.dryRun === false` in one hook at a time; receipt per flip |
| **Dependencies** | Phase 1 complete + re-panel pass; Phase 3 only for held signals |
| **Kyle gates** | `"flip memory live"` / `"flip infra live"` — literal per hook; `post_fail_silence` **separate override** (never batch with DEFAULT_SIGNALS) |
| **Effort** | 1 day re-panel; 2–4 h per hook flip + 48 h observation |
| **Success** | Live episodes match shadow predictions; no false-pulse on dedup/stale vectors |

---

## 3. Critical path (ASCII)

```
2a0529092 (committed, unpushed)
        │
        ▼
[Phase 1] hooks emit → eq-shadow-log.jsonl grows ──(14d audit)──► adversarial re-panel
        │                                                              │
        ├──────────────────────────────┐                               │
        ▼                              ▼                               ▼
[Phase 2] "pulse reads body"     [Phase 3] "return_current debate"   [Phase 4] per-hook live flip
 snapshot → pulse poll            registry + shadow emitters           dryRun:false one at a time
 (parallel OK)                    (serial per signal)                  (blocked until 1+3 pass)

HARD BLOCKS (any phase): serve.js/mobile │ git push │ training/CDP/cloud
Gates: "phase 1 go" │ "pulse reads body" │ "return_current debate" │ "flip * live" │ "push eq"
```

**Parallel allowed:** Phase 1 accrual + Alpha 1B source-only (NEXT.md) — **different commit batches**.

---

## 4. Top 5 risks + mitigations

| # | Risk | Mitigation |
|---|------|------------|
| 1 | **False pulse** — dry-run logged as achievement or live fires on proxy success | Envelope law: shadow only in jsonl; council posts require receipt; re-panel before any flip |
| 2 | **Shadow log never accrues** — hooks not on hot path | Proof-of-life check day 3: `wc -l eq-shadow-log.jsonl`; if 0, trace watchdog/verify call chain |
| 3 | **serve.js creep** — pulse integration bypasses gate | Experience architect brief mandates sidecar read; Pi grep `serve.js` in EQ tranche diffs |
| 4 | **Held signal premature unlock** — Kyle-attention outweighs coherence | Debate order; Shadow DO NOT list; max 2 identical-vector/24h already in registry |
| 5 | **Unpushed commit drift** — dirty tree merges overwrite EQ arc | `"push eq"` pushes **only** `2a0529092`; no mixed batches with Alpha/CDP/training |

---

## 5. Recommended Kyle paste (first execution tranche)

```
phase 1 go
```

**Effect:** Orchestrator writes `EXECUTION-CARD-PHASE1.md` → builder ships shadow log viewer + weekly audit template → Pi runs existing 43 tests + viewer smoke → passive accrual starts. **Do not** paste `"pulse reads body"` or `"return_current debate"` in the same tranche — sequence after Phase 1 card lands.

Optional same evening (cross-track, build lane): `"alpha 1b packet"` — source-only OOM mitigation, zero EQ files in commit.

---

## 6. What NOT to do this longhaul

- Edit `serve.js` or ship mobile body UI without `"pulse reads body"` / explicit mobile gate
- `git push`, training launch, cloud spend, or CDP restart without exact Kyle phrase
- Set `dryRun: false` on any hook before Phase 1 audit + adversarial re-panel
- Auto-emit `post_fail_silence` or unlock `sister_spawn_outcome` without separate override + extra evidence fields
- Collide with `research-spark` overnight loop or mix EQ commits with Alpha/CDP dirty-tree batches
- Treat dry-run envelopes as council achievements or skip weekly human audit of `would_fire` lines
- Debate `return_current` before shadow log has ≥10 real evaluations (no evidence-free unlock)

---

**Next orchestrator action:** Read four briefs → synthesize → `EXECUTION-CARD-PHASE1.md` → present phase picker to Kyle.
