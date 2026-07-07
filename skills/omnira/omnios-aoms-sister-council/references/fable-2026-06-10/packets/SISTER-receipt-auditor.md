# TASK PACKET — Receipt Auditor

**packet_id:** panel-receipt-audit-eq-phase-b-001
**role:** Receipt Auditor
**model_default:** mimo or nemotron (utility tier)
**posture:** L1_ADVISORY
**deadline_turns:** 1

---

## Objective

Audit provenance chain from 2026-06-09 Phase A through 2026-06-10 sister debate. Spot-check 10% of audit claims. Flag verb discipline violations and missing receipts.

---

## Bounded scope (Pi provides paths + snippets)

Verify existence and internal consistency ONLY — Pi reads, sister grades shape:

| Artifact | Expected verb | Check |
|----------|---------------|-------|
| Phase A receipt | committed | hash cited? |
| eq-trinity debate 2026-06-09 | written locally / committed | smoking guns have file:line? |
| eq embodied debate 2026-06-10 | written locally | 3 spawn ids cited? |
| Sister spawn metadata | spawned ok | ok:true in metadata? |

Flag if any doc says "deployed" / "pushed" / "GREEN" without matching proof type from operating manual.

---

## Output schema (Verdict Card)

```
RECEIPT_CHAIN: COMPLETE | GAPPED | LAUNDERED
GAPS: [list]
VERB_VIOLATIONS: [list]
SPAWN_PROVENANCE_OK: true|false
RECOMMENDATION: proceed_to_arbitration | fix_receipts_first
PROVENANCE: L1_ADVISORY
```
