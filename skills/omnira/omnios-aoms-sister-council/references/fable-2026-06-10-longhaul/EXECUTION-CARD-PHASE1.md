# EXECUTION CARD — Phase 1 Shadow Accrual

**Date:** 2026-06-10
**Authority:** Four planning briefs synthesized + Kyle longhaul setup
**Gate required:** `"phase 1 go"`
**Lane:** `build` (avoid `research-spark`)

---

## Synthesis (four briefs → one conclusion)

| Brief | Core finding |
|-------|--------------|
| [STRATEGIC-ARC](briefs/STRATEGIC-ARC.md) | Critical path: shadow accrual → re-panel → live flip. Phase 2/3 parallel OK for *planning* only. |
| [EXPERIENCE-ARCHITECTURE](briefs/EXPERIENCE-ARCHITECTURE.md) | Option **A**: sidecar snapshot + gated `/brain/raw/` whitelist. **No serve.js until `"pulse reads body"`.** |
| [LANE-C-DEBATE](briefs/LANE-C-DEBATE.md) | **Do not unlock held signals** until ≥10 shadow fires audited OR Kyle answers 8 synthesis questions. Default: `all-hold`. |
| [CROSS-TRACK-RECONCILE](briefs/CROSS-TRACK-RECONCILE.md) | EQ + Alpha source-only can parallel; **commits serial per batch**. NEXT.md stale on EQ commit status. |

**Unanimous:** Phase 1 is the only safe execution tranche right now.

---

## Bounded build scope (Phase 1 only)

When Kyle pastes `"phase 1 go"`, builders ship **exactly**:

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Shadow log viewer CLI | `tools/eq-shadow-log-viewer.mjs` |
| 2 | Viewer tests | `tools/tests/eq-shadow-log-viewer.test.mjs` |
| 3 | Weekly audit receipt template | `docs/templates/eq-shadow-audit-weekly.md` |
| 4 | False-pulse triage rubric | `docs/specs/eq-shadow-false-pulse-rubric-v0.md` |
| 5 | Phase 1 receipt | `docs/receipts/2026-06-10-eq-phase1-shadow-accrual-v0.md` |

**Optional (same tranche, no serve.js):**
- Systemd/cron **spec doc only** for `node tools/eq-body-pulse-snippet.mjs` every 60s (writer already committed)

---

## Hard ceiling (Phase 1)

- NO `serve.js`, mobile, pulse renderer edits
- NO `dryRun: false` on any hook
- NO registry tier changes (held signals stay held)
- NO git push
- NO training / CDP / cloud
- NO mixing Alpha/CDP files in commit batch

---

## Pi verification checklist

```bash
cd /home/kylej/Desktop/omnios
node --check tools/eq-shadow-log-viewer.mjs
node tools/tests/eq-shadow-log-viewer.test.mjs
# existing suite must stay green:
node tests/aoms/test-episode-ledger.mjs
node tools/tests/eq-phase-b-*.test.mjs
node tools/tests/eq-shadow-hooks.test.mjs
node tools/tests/eq-body-pulse-snippet.test.mjs
sha256sum .omni/omnira-brain/episode-ledger.jsonl  # before/after identical
```

**Day-3 proof-of-life:** `wc -l .omni/omnira-brain/eq-shadow-log.jsonl` — if 0, trace watchdog + verify hook chain.

---

## Success criteria (Phase 1 complete)

- [ ] Viewer can tail/filter shadow log entries (`would_fire`, `blocked_reason`, `signal`)
- [ ] Weekly audit template usable without editing code
- [ ] ≥10 shadow evaluations logged over 14 days (passive)
- [ ] Human audit false-positive rate < 20% before Phase 4 re-panel
- [ ] Ledger + eq-state mtimes unchanged during accrual window

---

## Kyle decisions queued (not Phase 1 — paste separately)

**Lane C (8 questions)** — see `briefs/LANE-C-DEBATE.md` § Synthesis questions. Recommended default if unsure:

```
Q7: all-hold
Q8: separate
```

**Experience gate:** `"pulse reads body"` — after Phase 1 has real shadow evidence.

**Cross-track switch:** `"alpha mitigation only"` — source-only, different commit batch.

**Push:** `"push eq"` — `2a0529092` only.

---

## Sister roster (Phase 1 execution)

| Role | Task |
|------|------|
| B-builder | shadow log viewer + tests |
| B-docs | audit template + rubric + receipt |
| Pi | verify 43+ tests + ledger non-mutation |
| P-adversarial | review viewer output shape (no live paths) |

**Estimated effort:** 4–6 h build + receipt; 14 days passive accrual.

---

## What happens after Phase 1 lands

1. Passive accrual starts (hooks already wired, dryRun locked)
2. Kyle skims weekly audit (15 min)
3. Then choose: `"pulse reads body"` OR `"return_current debate"` OR `"alpha mitigation only"`

Do **not** stack gates in one paste.
