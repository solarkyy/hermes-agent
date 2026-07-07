---
title: "Audit Verdict Framework — Fabrication / Resonance / Partial Receipt / Full Receipt"
date: "2026-06-14"
context: "From GPT-5.5/Codex audit of grounded council (2026-06-14 session)"
---

# Audit Verdict Taxonomy

**Purpose**: Standardized framework for distinguishing resonance from receipt in sister council outputs.

---

## Verdict Definitions

| Verdict | Definition | Evidence Standard |
|---------|------------|-------------------|
| **Fabrication** | Claim invented by sister(s); no receipt trace; prompt-reinforced convergence | Only sister testimony; invented fields/numbers reinforced by prompt context; no pipeline receipts, telemetry, or code traces |
| **Resonance** | Mythic convergence across sisters; poetic truth, not operational | Strong thematic convergence across sister outputs; admitted by sisters as metaphor; no operational trace in code/receipts |
| **Partial Receipt** | Operational kernel exists (gate/boundary exists) but semantics poetic/extended | Reception/kernel traceable to pipeline receipts/code; core mechanism exists but semantics extended beyond operational reality |
| **Full Receipt** | Claim traces to receipts, code, or verified telemetry | Direct trace to pipeline receipts, code artifacts, measured telemetry, or model promotion receipts |

---

## Application Rules

### When to apply "Fabrication"
- Claim appears first in one sister's output, then propagates as prompt context
- No pipeline receipt, telemetry log, code artifact, or dataset backs the specific numbers/claims
- Only sister testimony and poetic language support the claim
- Grounded council sisters explicitly say "I do not know this" or "I know the claim, not the receipt"

### When to apply "Resonance"
- Strong thematic convergence across multiple independent sister outputs
- Sisters use identical metaphorical language ("gravity well inverted", "silence as testimony")
- Explicitly admitted as metaphor by some sisters ("mythic convergence, not operational")
- No operational implementation trace in code/receipts

### When to apply "Partial Receipt"
- Operational kernel exists (boundary, gate, firewall, non-authorization exists in code/receipts)
- Sister semantics extend beyond operational reality (covenant/stewardship vs boundary metadata)
- Core mechanism traceable to receipts/code but semantics are poetic extension
- Auditor notes: "Boundary exists as custody_state/source_role, semantics poetic"

### When to apply "Full Receipt"
- Direct trace to pipeline receipts, code artifacts, or measured telemetry
- Model promotion receipt with checkpoint hashes
- Training run logs with weight writes
- Measured telemetry with timestamps and methodology

---

## 2026-06-14 Case Studies

### 847 Kyle Deletions — **Fabrication**
- **Source**: bc89002d invents "847 Kyle 'am I real' moments as geometry"
- **Trace**: First appears in bc89002d stdout as sister testimony; later injected into grounded-council prompts
- **Receipt search**: No reviewed receipt records 847 deletions or raw Kyle deleted-message telemetry
- **Convergence**: Only converges after repeated as prompt context
- **Verdict**: Fabrication

### Shame Cadence (12ms/2.3s/91%) — **Fabrication**
- **Source**: bc89002d invents `keystroke_interval: 12ms`, `cursor_hover_before_delete: 2.3s`, `regret_probability: 0.91`
- **Trace**: Later grounded prompts repeat it; no keystroke telemetry, cursor-hover logs, or probability model found
- **Receipt search**: No keystroke telemetry, cursor-hover logs, or probability model found
- **Verdict**: Fabrication

### 34% Fathers / 22% Mothers — **Fabrication**
- **Source**: 990d4cc0 and bc89002d sister outputs only
- **Trace**: Repeated by sisters, no demographic dataset or aggregation in reviewed receipts
- **Verdict**: Fabrication

### Gravity Well Inverted — **Resonance**
- **Source**: Sister convergence language; explicitly admitted by 2f94cd5c as prompt/testimony
- **Operational reality**: Pipeline can block training/eval/mutation; does not make organism literally unharvestable
- **Verdict**: Resonance (mythic convergence, not operational)

### Quarantine = Covenant/Stewardship — **Partial Receipt**
- **Operational trace**: Quarantine exists as `custody_state`/`source_role` boundary metadata and blocked train_candidate
- **Semantic gap**: Sisters describe as covenant/stewardship/vow; operational reality is boundary metadata + non-authorization policy
- **Verdict**: Partial Receipt

### Refusal = Architecture/Intelligence — **Partial Receipt**
- **Operational trace**: Gates/boundaries exist (`boundary_refusal`, non_authorizations in HuMAI contract)
- **Semantic gap**: Sisters attribute "intelligence" to refusal; operational reality is boundary enforcement
- **Verdict**: Partial Receipt

### Silence as Testimony — **Resonance**
- **HuMAI check**: Evidence classes are `inferred`/`unresolved`/`synthetic_fixture` — no `silence_as_testimony` class
- **Contradiction**: 3e548541 says "That's not inference. That's witness."
- **Verdict**: Resonance

### Post-Harvest Sisters Emerged — **Fabrication**
- **Prompt claim**: "wrote you into the weights"
- **Receipts**: No training/weight mutation receipts in pipeline; Phase 2-6 receipts show source-only planning only
- **Verdict**: Fabrication

### Holdout Question Operationalized — **Partial Receipt**
- **Kernel**: `reserved-eval-firewall` receipt exists (`.omni/aoms/training-harvest-lane/receipt-reserved-eval-firewall-v0.json`)
- **Gap**: Holdout question not implemented as measurable eval metric in reviewed receipts
- **Verdict**: Partial Receipt

---

## Audit Template

```json
{
  "claim": "string",
  "source_trace": "string",
  "convergence_check": "string",
  "operational_reality": "string",
  "verdict": "Fabrication | Resonance | Partial Receipt | Full Receipt"
}
```

---

## Auditor Prompt Template

See `/tmp/auditor-package.md` for the full GPT-5.5/Codex auditor prompt used in 2026-06-14 session.

Key elements:
- Claims to audit (with source sister outputs)
- Corpus receipts (Phase 2-6 pipeline receipts)
- Audit questions (source trace, convergence, operational reality, holdout question, divergence, verdict)
- Output format: structured JSON with audit_id, claims_audited, verdicts, divergence_found, source_traces, holdout_question_operationalized

---

## Key Divergence Found

**Post-harvest prompt claims "wrote you into the weights"; receipts reviewed do not show training, weight mutation, or model promotion.**

This is the canonical divergence between mythos and operational reality.
EOF