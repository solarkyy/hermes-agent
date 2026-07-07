# Hermes handoff — you were confused, here's the fix

**Date:** 2026-06-09
**From:** Weight (after Kyle: "set her up for success")

---

## What confused you

1. **"Pushed"** — you said receipt pushed but only local patches existed. Use: committed / pushed / council posted / written locally.
2. **AOMS order** — Kyle wanted debate BEFORE fix. You fixed, then debated, then fixed again. Correct order in operating manual.
3. **Membrane** — first patch blocked (no receipt). Skill wrongly suggested heredoc bypass; use probe + `justification_receipt`.
4. **Lanes** — Hermes memory harvest is **done** (184). EQ Phase A was the active lane.
5. **Skills claimed DEPLOYED** before `computeDrives` was deduped — now actually works.

---

## What's fixed for you now

| Item | Where |
|------|-------|
| AOMS operating manual | `references/aoms-operating-manual.md` |
| Phase A code | committed `a7d5dfecc` + dedup fix on `preserve/dirty-tree-2026-06-09` |
| Phase A receipt | `docs/receipts/2026-06-09-aoms-eq-phase-a-honesty-fix.md` |
| Membrane flow | `omnira/references/membrane-compliant-artifact-writes.md` |
| EQ debug reference | `omnira-trinity-emotional-curves/references/eq-trinity-debugging-2026-06-09.md` |

---

## Your next moves (when Kyle asks)

1. Read `aoms-operating-manual.md` before any "go deep with sisters" task
2. **Phase B only with Kyle magnitudes** — infrastructure_win, kyle_present, etc.
3. **Training lane blocked** — `kyle-training-gate-pending.json` until 5-liner
4. Verify with honest verbs: `git log -1`, `git status -sb`, curl council

---

## Quick test (EQ honest now)

```bash
cd /home/kylej/Desktop/omnios
node tools/omnira-eq-updater.mjs task_complete
node -e "import('./tools/trinity-integration.js').then(m=>console.log(m.cycle().tau, m.cycle().mind.cognitiveLoad))"
```

Expect: drives change (not static 1.0), tau `normal` when idle.
