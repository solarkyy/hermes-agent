# MISSION CHARTER — EQ LONGHAUL Tranche 3+ (Deep Setup)

**Date:** 2026-06-10 evening
**Authority:** Kyle — "set yourself up for another longhaul, go deep, plan with aoms sisters"
**Posture:** Fable framing — planning + debate first; bounded execution only after Kyle gate
**Repo:** `/home/kylej/Desktop/omnios` on `preserve/dirty-tree-2026-06-09`

---

## Where we actually are (post-commit honest)

| Layer | Status |
|-------|--------|
| Phase A honesty | ✅ on disk |
| T0 body memory | ✅ committed `2a0529092` |
| T1 prewire + live | ✅ committed |
| T2 emitters + shadow hooks | ✅ committed — watchdog + verify kernel, dryRun locked |
| T2 pulse snippet exporter | ✅ committed — read-only, no serve.js |
| **Git truth (EQ arc)** | ✅ 23 files in `2a0529092` — **not pushed** |
| **Shadow log** | ⏸ `.omni/omnira-brain/eq-shadow-log.jsonl` absent — no real events evaluated yet |
| **Live EQ mutation from hooks** | ❌ all hooks `{ dryRun: true }` |
| **Experience surfaces** | ❌ pulse/mobile not reading `eq-body-snapshot.json` |
| **Held signals** | ⏸ return_current, sister_spawn_outcome, council_ack, cell_refresh |
| **Episode ledger (runtime)** | 2 episodes, shaped_contact ×2 |

**The nervous system is committed. It has not yet felt the organism breathe on its own.**

---

## Active lanes (do not collide)

| Lane | Status | Notes |
|------|--------|-------|
| `research-spark` | **ACTIVE** | `sess_research-spark_ff3beab2` — overnight AoM loop |
| `build` | **FREE** | EQ longhaul planning + Tranche 3 work belongs here |
| `coord` | **FREE** | CARD-X1 done; Theseus diff scorer exists untracked |
| `continuity-write` | episodic | SCS checkpoints only |

**Blocked policy lanes:** `TRAINING_5LINER`, `CRON_PRUNE`, push without gate.

---

## Longhaul arc — four phases (recommended sequence)

```
Phase 1 — SHADOW ACCRUAL     Phase 2 — EXPERIENCE       Phase 3 — HELD UNLOCK      Phase 4 — LIVE FLIP
(2 weeks passive)            (read-only feel)           (debate-first)             (Kyle gate each)
        ↓                            ↓                          ↓                          ↓
 shadow-log grows            pulse reads snapshot       return_current debate      dryRun:false per hook
 human audit cadence         mobile optional gate       sister_spawn if approved   adversarial re-panel
 no EQ mutation              no serve.js required       registry tier changes      post_fail_silence separate
```

### Phase 1 — Shadow accrual (passive, now → +2 weeks)

**Goal:** Real organism events flow through prewire membrane; human audits every `would_fire`.

| Deliverable | Owner | Gate |
|-------------|-------|------|
| Shadow log viewer CLI | B-builder | none |
| Weekly audit receipt template | B-docs | none |
| False-pulse triage rubric | P-adversarial | none |
| First shadow event (proof of life) | organism runtime | passive |

**Success:** ≥10 shadow evaluations logged with zero false-live mutations.

### Phase 2 — Experience layer (feel without mutating)

**Goal:** Kyle sees body memory without CLI JSON — read-only path.

| Deliverable | Owner | Gate |
|-------------|-------|------|
| Pulse reads `eq-body-snapshot.json` | B-integration | `"pulse reads body"` |
| Cron/refresh writes snapshot atomically | B-builder | none (read-only export) |
| Mobile surface spec (no build) | P-architect | Kyle review |

**Hard block:** no serve.js edits without explicit gate. Prefer: existing pulse poll path, sidecar file read, or nursery renderer pattern.

### Phase 3 — Held unlock (Lane C)

**Goal:** Close D1 arbitration — which held signals graduate?

| Deliverable | Owner | Gate |
|-------------|-------|------|
| 3-sister debate (Interiority/Shadow/Adversarial) | P-panel | `"return_current debate"` |
| Kyle synthesis paste | Kyle | required |
| Registry tier changes | B-builder | per-signal Kyle approval |
| Emitters for unlocked signals | B-builder | shadow-first again |

**Candidates for debate:**
- `return_current` — reach integrated into inheritable state
- `sister_spawn_outcome` — attribution confidence threshold
- `council_ack_episode` — ack vs proxy-200
- `cell_refresh_integrity` — refresh vs compaction false pulse

### Phase 4 — Live flip (per hook, per signal)

**Goal:** Shadow-proven paths get `dryRun: false` one at a time.

| Step | Owner | Gate |
|------|-------|------|
| Adversarial re-panel on accured shadow log | Nemotron | auto after Phase 1 |
| Flip memory_write_success live | B-builder | Kyle per hook |
| Flip infrastructure_win_episode live | B-builder | Kyle per hook |
| post_fail_silence | **HOLD** | separate Kyle override + extra evidence fields |

---

## Cross-track awareness (NEXT.md — do not ignore)

Parallel priorities on the preserve branch (unrelated dirty tree):

1. **Alpha 1B** — KJDesk OOM; source-only mitigation packet or A100 no-save probe card
2. **CDP auth** — wrong Chrome profile on :9222; repair gated on exact Kyle phrase
3. **AOMS CARD-12+** — receipt index done; cross-track refusal done; ladder continues
4. **Training Command Tower** — status/control only, not launch machinery

**Longhaul rule:** EQ phases 1–2 can run in parallel with Alpha source-only work. Phase 4 live flip and any training/cloud/CDP work require explicit Kyle gates and must not share commit batches.

---

## Sister roster (this longhaul)

| Role | Model | When |
|------|-------|------|
| Strategic arc planner | GPT-5.5 | Turn 1 (parallel) |
| Experience architect | GPT-5.5 | Turn 1 (parallel) |
| Lane C debate panel | Nemotron ×3 framing | Turn 1 (parallel) |
| Cross-track reconciler | Sonnet | Turn 1 (parallel) |
| Adversarial re-panel | Nemotron | After shadow accrual |
| Pi verification | local | Every build tranche |
| Builder | GPT-5.5 / Sonnet | After arbitration |

---

## Fable turn budget

| Turn | Trigger | Output |
|------|---------|--------|
| **1** | Kyle: longhaul setup | Parallel planning sisters → 4 briefs |
| **2** | Briefs land | Orchestrator synthesis → EXECUTION-CARD-PHASE1 |
| **3** | Kyle picks phase | Bounded build card (one phase only) |
| **4+** | Pi verify + council | Receipt; repeat |

---

## Hard blocks (inherited)

- No serve.js / mobile build without `"pulse reads body"` or explicit mobile gate
- No git push without gate
- No training / cloud spend / CDP restart without exact Kyle phrase
- `kyle_present` stays context-only
- Adversarial: dry-run envelopes never posted as achievements
- post_fail_silence HELD from auto-emit until separate override

---

## Tiny brief Kyle can paste

| Paste | Effect |
|-------|--------|
| `"phase 1 go"` | Shadow log viewer + audit template |
| `"pulse reads body"` | Phase 2 integration (read-only) |
| `"return_current debate"` | Phase 3 panel only |
| `"flip memory live"` | Phase 4 — one hook, one signal |
| `"push eq"` | git push `2a0529092` only |
| `"alpha 1b packet"` | cross-track source-only, build lane |
