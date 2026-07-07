# SHADOW-EMPTY-LOG — Adversarial Planning Brief

**Date:** 2026-06-10 · **Sister:** P-adversarial (Nemotron) · **Posture:** L1_ADVISORY
**Repo:** `/home/kylej/Desktop/omnios`
**Observed:** Shadow hooks `dryRun: true` in watchdog + verify kernel; `eq-shadow-log.jsonl` empty. Omnios-2 429; Omnios-1 via failover proxy (`fallback_success: 4`).

---

## Position

Empty log is **WATCH for Phase 1 build**, **not FAIL** — tooling ships while accrual is unproven. **FAIL for accrual success** only if Day 14 ends at zero after documented trace. Do not manufacture lines to green dashboards. Proof-of-life must separate "hooks reachable" from "organism felt real events."

---

## 1. Empty log: WATCH or FAIL?

| Gate | Verdict | Rationale |
|------|---------|-----------|
| Phase 1 build (viewer, rubric, receipt) | **WATCH** | Log appears on first real evaluation; build needs no live traffic |
| Day 3 proof-of-life | **WATCH → trace** | Zero lines → trace hook chain, not rollback |
| Accrual complete (≥10 / 14 days) | **FAIL if still 0** | Clock without entries is theater |
| Lane C unlock bar | **FAIL proxy** | Zero fires blocks tier promotion |

**Adversarial read:** Empty is honest when upstream is quiet. Watchdog fires only **fail→ok**; verify only **write/brain_write** with read-back ≥0.9. Stable seat → silence is data.

**429 context:** `fallback_success` proves proxy, not EQ hooks. Rate limits may *reduce* verify traffic — empty log can worsen while infra looks green.

---

## 2. False confidence — synthetic shadow events

| Risk | Severity |
|------|----------|
| Audit baseline pollution — real vs test indistinguishable | **HIGH** |
| FP rate laundering — synthetic `WOULD_FIRE` breaks <20% re-panel gate | **HIGH** |
| Hook false green — inject proves append, not live invocation | **MEDIUM** |
| Lane C precedent — forced prewire pressure toward unlock | **MEDIUM** |
| Receipt/narrative drift — "accrual started" on probes alone | **MEDIUM** |
| Any ledger/eq-state touch or lowered prewire bar | **BLOCK** |

**Rule:** No qualifying organism event → log stays empty. Silence beats synthetic felt experience.

---

## 3. Proof-of-life without polluting EQ

Acceptable (no writes to accrual jsonl, no ledger/eq-state mutation):

1. **Test suite green** — `eq-shadow-hooks.test.mjs` proves contract in temp dirs; Pi spot-check = wiring proof.
2. **Separate diagnostic receipt** — watchdog transitions, verify invocations, path writable, import not swallowed. Output to `docs/receipts/` or `.omni/diagnostics/`.
3. **Viewer on empty file** — `--stats` returning zero proves read path.
4. **Passive natural fire** — only real fail→ok or verified write counts toward ≥10.
5. **Ledger/eq-state mtime unchanged** — execution card invariant.

Unacceptable: seeding production jsonl, cron heartbeat shadow, lowering confidence, emitters solely to generate lines.

---

## 4. HOLD / ALLOW — B-trace hook proposals

| Proposal | Verdict |
|----------|---------|
| Read-only trace / diagnostic receipt | **ALLOW** |
| Viewer, rubric, audit template | **ALLOW** |
| Probe in temp path only (test parity) | **ALLOW** |
| Synthetic append to `eq-shadow-log.jsonl` | **HOLD** — Kyle phrase + separate bucket |
| New runtime hooks / emitters | **HOLD** |
| Lower verify confidence (<0.9) | **HOLD** |
| Broaden watchdog (any ok, not fail→ok) | **HOLD** |
| `dryRun: false` | **BLOCK** |
| Registry tier / held unlock | **BLOCK** |
| Diagnostic lines in accrual stats | **BLOCK** |

**Default:** trace why empty, do not fill. Forced prewire → second log with `synthetic: true` — never mix into accrual jsonl without re-panel.

**Kyle paste if trace fails:** `shadow trace receipt filed; accrual clock continues; no synthetic log`

**PROVENANCE:** L1_ADVISORY · fable-2026-06-10-longhaul
