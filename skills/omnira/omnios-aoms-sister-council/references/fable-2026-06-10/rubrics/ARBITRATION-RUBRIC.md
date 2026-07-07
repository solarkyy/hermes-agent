# ARBITRATION RUBRIC — EQ-PHASE-B-001 (Fable Turn 2)

**Use when:** Pi Evidence Bundle + sister Verdict Cards received
**Fable judges STRUCTURE only** — not raw private data

---

## Verdict template

```
MISSION: EQ-PHASE-B-001
BUNDLE_STATUS: PASS|PARTIAL|FAIL
ARBITRATION:

D1 return_current: ADOPT | REJECT | DEFER — reason (1 line)
D2 kyle_present: CONTEXT_ONLY | SIGNAL_4H | DEFER — reason
D3 tranche_scope: [exact signal list] — reason
D4 magnitudes: CONSERVATIVE | AGGRESSIVE | CUSTOM — Kyle must paste if CUSTOM

EXECUTION_CARD: DRAFT | BLOCKED
BLOCKERS: [list]
KYLE_GATES_OPEN: [G-KYLE-1..5 status]

FABLE_TURNS_USED: 2/3
NEXT: [Pi action | Kyle paste | sister re-spawn with fixed packet]
```

---

## Decision rules

1. **Bundle FAIL on C1 or C2** → BLOCK execution card; Phase A repair mission first
2. **Shadow + Interiority agree** on kyle_present context-only → default CONTEXT_ONLY unless Kyle overrides in same message
3. **Adversarial + Test Designer both HOLD a signal** → signal excluded from tranche 1
4. **Unanimous sister pass on signal + tests fail-before defined** → eligible for execution card draft
5. **Any protected patch without G-KYLE-5** → BLOCKED_NEEDS_EXPLICIT_KYLE_GATE

---

## Structural checks (not content)

- [ ] Every signal has episode boundary defined
- [ ] Every signal has shadow named
- [ ] Every signal has test fail-before + pass-after
- [ ] No signal fires on heartbeat/line-count alone
- [ ] Receipt chain closes before council post
