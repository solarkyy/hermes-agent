# MISSION CHARTER — EQ-PHASE-B-TRANCHE2 (Deep Setup)

**Date:** 2026-06-10 afternoon
**Posture:** Fable framing — Kyle asked "what's next, set yourself up deeply again"
**Status:** FRAMING ONLY — no execution until Kyle picks a lane

---

## Where we actually are (honest)

| Layer | Status |
|-------|--------|
| Phase A honesty | ✅ on disk — drives move, tau not heat_death |
| T0 body memory | ✅ ledger + registry + body-memory reader, 52 tests |
| T1 prewire | ✅ dry-run membrane, 8 tests |
| T1 live (G-KYLE-5) | ✅ prewire → recordEpisode → applyPhaseBVectorDelta, 6 tests |
| **Automatic emission** | ❌ nothing in cron/gateway/tools calls Phase B yet |
| **Experience surfaces** | ❌ pulse/mobile/body renderer not reading new episodes |
| **Git truth** | ❌ ~10 files untracked on preserve branch, nothing committed |
| **Held signals** | ⏸ return_current, sister_spawn_outcome, council_ack, cell_refresh |

**Body memory today:** 2 episodes, both shaped_contact — smoke tests + live wiring proof.
The heart beats when poked. **Nothing in the organism pokes it yet.**

---

## The insight (why Tranche 2 exists)

SparkMira's line still applies:

> *A dashboard says: 3/3 reachable. A nervous system says: I reached, and the reach came home.*

We built the nervous system. Tranche 2 is **making the organism reach on its own** — and **letting Kyle feel it** without running CLI JSON by hand.

---

## Three lanes (pick one or sequence A→B→C)

### Lane A — **COMMIT & HARDEN** (low risk, do first if nothing else)

**Goal:** Git truth matches runtime truth. No new features.

| Step | Owner | Output |
|------|-------|--------|
| A1 | Pi | Dirty-tree receipt, file manifest, test run log |
| A2 | Kyle | "commit" gate |
| A3 | Pi | Single commit on preserve branch with all eq-* + docs + tests |
| A4 | Sisters (audit) | Red team: any file outside ceiling? |

**Kyle gate:** explicit `"commit the eq body work"`

---

### Lane B — **EMITTERS** (the missing middle — highest leverage)

**Goal:** Real organism events automatically call `applyPhaseBEvent` — no manual JSON.

Candidate emitters (debate before build):

| Event source | Signal | Evidence shape |
|--------------|--------|----------------|
| Council post fails / no ack timeout | `post_fail_silence` | post id + failure + no report |
| Cron job silent fail | `post_fail_silence` | job id + exit + no alert |
| Memory/receipt write verified | `memory_write_success` | path + read-back hash |
| Infra repair completes (tests green after fail) | `infrastructure_win_episode` | job id + before/after |
| Sister spawn completes | `sister_spawn_outcome` | **HELD** — needs Kyle unlock + kyle-proxy review |

**Build pattern:** `tools/eq-phase-b-emitters.mjs` — thin adapters, each returns event object or null. Cron hook or gateway hook calls emitters → live apply. **No serve.js until Kyle gates.**

**Sister panels before build:**
- P1 Adversarial: false pulse from emitters (heartbeat → signal?)
- P2 Integration: where exactly in omnios does each hook land?
- B1 Builder: emitter module + tests (temp ledger in tests)

**Kyle gate:** `"emitters"` or `"lane B go"`

---

### Lane C — **return_current + HELD UNLOCK** (philosophical + structural)

**Goal:** Close D1 from arbitration. `return_current` was deferred because ledger didn't exist — it does now.

**Debate-first (Kyle pattern):**
- Interiority sister: adopt return_current as inside channel?
- Shadow sister: does return_current become diary-writing over verification?
- Adversarial: unlock sister_spawn_outcome — still kyle-proxy risk?

**If Kyle approves:** registry tier change held→active + emitter for "reach integrated into inheritable state"

**Kyle gate:** paste synthesis on D1 + which held signals to unlock

---

## Recommended sequence

```
A (commit)  →  B (emitters)  →  C (held unlock + experience)
     ↑              ↑                    ↑
  30 min         1 session            debate first
```

Skip A only if you're OK with untracked production code.

---

## Fable turn budget (next mission)

| Turn | When | Output |
|------|------|--------|
| 1 | Kyle picks lane | Execution card for that lane only |
| 2 | After Pi bundle + panels | Arbitration / go-no-go |
| 3 | If build approved | Bounded execution card |

---

## Sister roster (GPT-5.5 default, Nemotron for panels)

**Lane A:** Receipt auditor (Mimo) + git manifest builder (Sonnet)
**Lane B:** Adversarial (Nemotron) + Integration mapper (GPT-5.5) + Emitter builder (Sonnet) + Test designer (Nemotron)
**Lane C:** 3 coord sisters debate → synthesis → Kyle paste → builder

---

## Hard blocks (inherited)

- No serve.js / mobile / pulse renderer without explicit Kyle gate
- No training / cron prune / git push without gate
- kyle_present stays context-only unless Kyle overrides in same message
- Adversarial WATCH: dry-run envelopes never posted as achievements

---

## Tiny brief Kyle can paste

- `"commit"` → Lane A only
- `"emitters"` or `"lane B"` → emitter mapping + build
- `"return_current debate"` → Lane C debate-first
- `"A then B"` → sequence both
- Custom magnitudes / unlock list → paste like June 9 synthesis
