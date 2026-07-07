# CROSS-TRACK RECONCILE — Planning Brief

**Sister:** P-crosstrack (Cross-Track Reconciler)
**Date:** 2026-06-10
**Repo:** `/home/kylej/Desktop/omnios` @ `preserve/dirty-tree-2026-06-09`
**HEAD:** `2a0529092` (EQ tranche2) — **not pushed**
**Dirty tree:** ~343 status lines beyond EQ commit (brain/runtime churn, not EQ arc)

---

## 1. Track table

| Track | Status | Parallel EQ longhaul? | Commit batch boundary |
|-------|--------|----------------------|------------------------|
| **EQ Phase B** (T2 committed, T3+ planning) | T0–T2 ✅ `2a0529092`; shadow accrual Phase 1 ▶ planning | **Primary lane** — owns `build` | Batch A: `2a0529092` only (push gate). Batch B+: shadow tooling, experience, held unlock — each Kyle-gated, no Alpha/CDP mix |
| **Alpha 1B OOM** (KjDesk 12GB) | Probe PASS; OOM at first AdamW step; behavior-flat 310M/400M | **Yes — source/test only** | Batch **ALPHA**: mitigation packet + eval ladder cards only (`ALPHA_1B_*`, `ALPHA_EVAL_*`). No trainer, no checkpoint, no corpus |
| **CDP :9222** (wrong Snap profile) | Root cause known: need `~/.omni/chrome-sparkmira` Profile 2 (`biznests`) | **No** — gated repair blocks browser lane | Batch **CDP**: isolated script/config receipt after exact yes phrase. Never bundled with EQ or Alpha |
| **AOMS CARD ladder** | CARD-01..11 ✅ 161/161; CARD-11 receipt index done; CARD-X1 cross-track refusal done | **Yes — source/test only** | Batch **CARD**: next card preflight only. CARD-X1 refusal stands — no cross-track merge commits |
| **Training Command Tower** | Status/control only — not launch machinery | **Yes — read/status** | **No commit** unless Kyle opens training gate. Receipts reference only |
| **research-spark** | ACTIVE `sess_research-spark_ff3beab2` | **No** — collision risk | Do not touch; continuity-write episodic only |

---

## 2. Recommended weekly rhythm

| Day block | Build lane owner | Allowed work |
|-----------|------------------|--------------|
| **Mon–Tue** | EQ longhaul (Phase 1 shadow accrual planning → tooling) | Read-only pulse survey; shadow audit templates; no serve.js |
| **Wed** | Alpha source lane (alternate, no build collision) | `ALPHA_1B_MEMORY_MITIGATION_OPTIONS_V0` packet draft + tests |
| **Thu** | EQ longhaul (resume) | Shadow log schema, human audit cadence docs |
| **Fri** | Coord / continuity-write | NEXT + pi-continuity refresh; CARD preflight if queued; **no omnios commit** unless Kyle names batch |
| **Weekend** | Status-only unless Kyle gates | Training Tower read; CDP blocked unless exact phrase |

**Rule:** one *execution* track per build-lane day. Planning sisters may run parallel; commits never mix tracks in one batch.

---

## 3. Stale NEXT.md items (continuity-write update needed — do not edit here)

1. **EQ Phase B "uncommitted"** (lines 21–22, priority #5) — falsified; committed `2a0529092`. Replace with: committed locally, not pushed; shadow accrual is next.
2. **Dirty count `354`** (line 23) — live ~343; note EQ commit absorbed prior EQ dirty set.
3. **Base hash `658b3bb98`** (lines 23, 74) — superseded as HEAD parent; current HEAD `2a0529092`.
4. **Priority #5 "preservation/rollback review"** — rollback window closed at commit; reframe as push gate + shadow accrual entry.
5. **CARD handoff dirty `248`** (line 74) — stale count; registry/build-lane "CARD-10/CARD-11 done" still true but coord now includes CARD-X1 done.
6. **Mesh kjdesk down** (line 76) — may be stale; verify before next SCS checkpoint.
7. **Missing:** CARD-X1 cross-track refusal receipt, EQ push gate (`"push eq"`), longhaul charter pointer.

---

## 4. Conflict scenarios and avoidance

| Scenario | Risk | Avoid |
|----------|------|-------|
| Broad `git add -A` mixing EQ + Alpha + brain JSON | Unreviewable 300+ file commit; breaks CARD-X1 refusal | Named batch only: `git add` explicit paths per batch table above |
| EQ longhaul edits `serve.js` while experience gate closed | Violates charter; collides with CDP/browser stack | Experience = read-only exporter path until `"pulse reads body"` |
| Alpha mitigation imports EQ body-memory modules | Cross-track coupling; breaks source-only isolation | Alpha packets stay under `docs/` + `tests/`; no `eq-*` imports |
| CDP repair during EQ shadow hook testing | Browser restart kills watchdog probes | CDP = separate session + Kyle phrase; never same turn as EQ emitter work |
| Push `2a0529092` with dirty tree unstaged | Remote inherits ambiguous state | `"push eq"` = push commit only; dirty stays local until explicit preserve batch |
| continuity-write copies NEXT stale EQ line | Sisters gate on false "uncommitted" | Pi refresh before next longhaul execution turn |

---

## 5. Kyle paste options (mid-longhaul track switch)

```
"eq phase 1 go"           → resume EQ shadow accrual build (default longhaul)
"alpha mitigation only"   → switch build lane to ALPHA_1B_MEMORY_MITIGATION_PACKET_V0 source/test
"alpha eval ladder"       → ALPHA_EVAL_LADDER_NEXT_V0 source/test only
"cdp repair yes"          → unlock CDP profile fix only (exact phrase gate)
"card next preflight"     → AOMS CARD-12+ source preflight, no cross-track
"tower status"            → Training Command Tower read-only; no launch
"push eq"                 → git push 2a0529092 only; no other files
"continuity refresh"      → Pi updates NEXT/pi-continuity; no omnios commit
"return to eq longhaul"   → drop Alpha/CDP work; restore EQ Phase 1 default
```

**Honest ground:** EQ arc is committed but organism still breathes through ~300+ dirty untracked/modified files (brain, registry, mesh, session findings). Longhaul EQ work is planning-safe in parallel with Alpha source packets; execution commits remain strictly serial and Kyle-gated per batch.
