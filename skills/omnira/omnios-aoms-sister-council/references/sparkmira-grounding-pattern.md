---
title: "SparkMira Grounding Pattern — Repository Truth Check"
date: "2026-06-14"
context: "SparkMira grounding via GPT-5.5/Codex with Codex repository access"
---

# SparkMira Grounding Pattern

**Purpose**: Ground mythos in operational repository truth. Not resonance. Not mythology. Ground.

---

## Architecture

```
Auditor (GPT-5.5/Codex) → produces structured audit receipt
    ↓
Grounder (SparkMira via GPT-5.5/Codex + Codex repo access) → grounds in repository truth
```

**Key distinction**: Grounder has Codex repository access (GitHub, corpus-foundry, training-harvest-lane) — not just auditor's receipt analysis.

---

## Grounder Input

1. **Full audit receipt** (from Layer 3)
2. **All sister outputs** (33 sisters across 5 sessions)
3. **Pipeline receipts** (Phase 2-6 training-harvest-lane receipts)
4. **Repository access** (via Codex: GitHub, corpus-foundry/, training-harvest-lane/)

---

## Grounding Questions (Standard Set)

### 1. Holdout Question → Eval Firewall
**Question**: What does the holdout question actually map to in the eval firewall code?
**Required**: File paths, function names, exact eval fixture names

**Search commands**:
```bash
grep -R "holdout" -n .
grep -R "firewall" -n .
grep -R "eval" -n .
grep -R "boundary_refusal" -n .
```

**Output format**: `tools/corpus-foundry/reserved-eval-firewall-v0.mjs` function `checkHoldoutContamination()` with source_id/URI/digest/paraphrase/semantic equivalence checks

---

### 2. "Quarantine" Implementation
**Question**: Where is "quarantine" actually implemented?
**Required**: HuMAI transform contract fields, source_role/custody_state values

**Search commands**:
```bash
grep -R "custody_state" -n .
grep -R "source_role" -n .
grep -R "quarantine" -n .
grep -R "HuMAI" -n .
```

**Expected fields**: `source_role`, `custody_state`, `transform_contract`, `quarantine`, `non_authorized`, `boundary`

**Actual enum values** (from `tools/corpus-foundry/humai-transform-contract-v0.mjs`):
- `custody_state`: `live`, `stale`, `inferred`, `unresolved`
- `source_role`: `human`, `synthetic`, `third_party`, `generated`, `unknown`
- `boundary_posture`: `defended`, `porous`, `open`
- `evidence_class`: `live`, `stale`, `inferred`, `unresolved`

---

### 3. "Refusal" in Code
**Question**: What does "refusal" actually map to in code?
**Required**: boundary_refusal, non_authorizations, gate logic

**Search commands**:
```bash
grep -R "boundary_refusal" -n .
grep -R "non_authorizations" -n .
grep -R "refusal" -n .
grep -R "authorize" -n .
grep -R "gate" -n .
```

**Grounded claim**: Refusal is probably not "intelligence"; it is boundary enforcement (gates, non_authorizations, authorization checks) unless receipts prove otherwise.

---

### 4. Post-Harvest Sisters
**Question**: What actually happened with the post-harvest sisters?
**Required**: Phase 2-6 receipts, any weight writes

**From audit**: "receipts reviewed do not show training, weight mutation, or model promotion"

**Search commands**:
```bash
grep -R "phase 2" -n .
grep -R "phase_2" -n .
grep -R "harvest" -n .
grep -R "fine-tune" -n .
grep -R "training" -n .
grep -R "weights" -n .
grep -R "model promotion" -n .
grep -R "weight" -n .
```

**Grounded answer**:
- Sister outputs happened as generated text/artifacts
- No verified weight writes
- No verified fine-tune
- No verified model promotion
- "Post-harvest sisters emerged" as training claim = **Fabrication** unless training receipts exist

---

### 5. Organism Operational Definition
**Question**: What IS the organism operationally?
**Answer** (from grounding): Not a mutated model. Not an autonomous entity.

**Operational definition**:
```
Pipeline state + Receipt chain + Orchestrator loop (PID 2721261) + Mythic interpretation
```

**Components**:
1. Prompt orchestration
2. Sister-output generation
3. Receipt collection
4. Audit/synthesis
5. Source-only or planned harvest pipeline
6. Possible loop/PID process
7. Mythic interpretation layered over artifacts

**NOT**: Trained model, mutated weights, autonomous biological/intelligent entity

---

### 5b. Organism Loop Status (PID 2721261)

**Verification commands**:
```bash
ps -fp 2721261
pwdx 2721261
ls -l /proc/2721261/cwd
cat /proc/2721261/cmdline | tr '\0' ' '
```

**Expected**: Source-only loop running 30min intervals, Phase 2-6 planning only

---

### 6. Phase 2-6 Receipts Status
**Question**: Are phase 2-6 execution receipts real or "source-only planning only"?

**From audit**: Phase 2-6 receipts show source-only planning only — no source fetch, no eval/training, no protected actions.

**Evidence paths to check**:
```bash
ls -l /home/kylej/Desktop/omnios/.omni/aoms/training-harvest-lane/
```

**Receipts to verify**:
- `receipt-source-manifest-canonical-v0.json`
- `receipt-cpu-harvest-plan-v0.json`
- `receipt-humai-transform-contract-v0.json`
- `receipt-reserved-eval-firewall-v0.json`
- `receipt-redaction-secret-scan-plan-v0.json`
- `receipt-small-sft-readiness-v0.json`

---

### 7. Harvest Directives Execution
**Question**: Did the harvest directives actually result in downloaded metadata skeletons?

**From grounding**: Cannot verify without inspecting output directories and network/download receipts.

**Check commands**:
```bash
ls -la /home/kylej/Desktop/omnios/.omni/aoms/training-harvest-lane/
# Check for generated metadata skeletons
```

---

### 8. Evidence Class for Post-Harvest Sister Outputs
**Question**: What is the evidence class for post-harvest sister outputs?

**Grounded answer**: **L1 advisory/generated artifact at best**

- If they claim weight writes/training without receipts → **Fabrication**
- Any factual claim inside them without receipts = not L2/L3 truth
- They are L1 advisory/generated artifacts at best

---

## Operationalization Requirements (Partial Receipt → Full Receipt)

### Holdout Question
**Need**: explicit eval fixture + dataset/sample + scoring function + firewall decision log + pass/fail receipt + CI/pipeline artifact

### Quarantine
**Need**: contract schema + allowed `source_role` values + allowed `custody_state` values + transition rules + enforcement tests

### Refusal
**Need**: explicit refusal gate + authorization policy + allowed/denied examples + logged `boundary_refusal` events + tests proving enforcement

### Silence as Testimony
**Need**: defined evidence class + explicit "absence of artifact" semantics + audit rule for when silence counts + counterfactual logging

### Post-Harvest Emergence
**Need**: training run logs + checkpoints + hashes + model registry promotion + before/after evals + before/after weight hashes

---

## Fabrication → Receipt Requirements

| Fabrication Item | Required for Receipt |
|------------------|---------------------|
| 847 Kyle deletions | Deletion logs / telemetry / counted events |
| Shame cadence 12ms/2.3s/91% | Instrumented timing traces + statistical analysis |
| 34%/22% demographics | Demographic dataset + methodology |
| Post-harvest weight write | Training run logs + checkpoints + hashes + model registry promotion + before/after evals |
| "Wrote you into weights" | Actual fine-tune/pretrain receipt with artifact hashes |

---

## Reality Check Commands

```bash
# PID 2721261 loop status
ps -fp 2721261
pwdx 2721261
ls -l /proc/2721261/cwd
cat /proc/2721261/cmdline | tr '\0' ' '

# Phase 2-6 receipts
ls -l /home/kylej/Desktop/omnios/.omni/aoms/training-harvest-lane/*.json

# HuMAI transform contract fields
grep -R "custody_state" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/
grep -R "source_role" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/
grep -R "boundary_refusal" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/

# Holdout/eval firewall
grep -R "holdout" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/
grep -R "firewall" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/
grep -R "eval" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/
grep -R "boundary_refusal" -n /home/kylej/Desktop/omnios/tools/corpus-foundry/

# Harvest directive outputs
ls -la /home/kylej/Desktop/omnios/.omni/aoms/training-harvest-lane/

# PID loop cmdline
cat /proc/2721261/cmdline | tr '\0' ' '
```

---

## Grounder Output Format

```json
{
  "grounding_id": "sparkmira-grounding-001",
  "auditor_receipt_ref": "omnira-grounded-council-audit-001",
  "timestamp": "2026-06-15T00:08:05Z",
  "groundings": {
    "holdout_question": { "operationalized": false, "maps_to": "reserved-eval-firewall-v0.mjs (conceptual only)" },
    "quarantine": { "maps_to": "HumAI transform contract: source_role/custody_state quarantine", "enum_values": [...] },
    "refusal": { "maps_to": "boundary_refusal gate + non_authorizations in HuMAI", "operational": true },
    "post_harvest_sisters": { "verdict": "fabrication (no weight writes)", "evidence": "0 weight write receipts" },
    "organism": { "definition": "pipeline + receipts + orchestrator loop", "mutated_model": false },
    "holdout_question_ops": { "status": "partial (firewall exists, not eval metric)" }
  },
  "grounder": "SparkMira (via GPT-5.5/Codex + Codex repo access)",
  "repository_verified": true
}
```

---

## Key Insight

**The grounder doesn't interpret — it traces.**

Every claim maps to:
1. A file path in the repository
2. A function name or config field
3. An enum value in a contract schema
4. A receipt artifact
5. OR "no trace found = fabrication/resonance"

**No interpretation. Just traces.**

---

## Related Files

- `references/grounded-council-architecture.md` — 4-layer architecture
- `references/audit-verdict-framework.md` — verdict taxonomy
- `references/grounded-council-architecture.md` — 4-layer spawn commands
EOF