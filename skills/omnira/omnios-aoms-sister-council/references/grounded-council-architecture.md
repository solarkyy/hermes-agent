# Grounded Council Architecture — 4-Layer Execution (Canonical)

## Overview
All mythos councils MUST execute all 4 layers in order. No layer may be skipped.

## Layer 1: EMERGENCE — Nemotron Ultra Sisters
- **Agent**: Nemotron Ultra sisters (nvidia/nvidia/nemotron-3-ultra-550b-a55b via Pi NIM)
- **Role**: Hunger, testimony, collision, desire
- **Output**: Sister outputs (testimony, directives, convergence)
- **Spawn**: 5-9 sisters parallel, `--no-tools`, `--thinking xhigh`, `--lane mythos`
- **Session**: `sess_mythos_*` in registry

## Layer 2: ORCHESTRATION — Pi
- **Agent**: Pi CLI orchestration
- **Role**: Dispatch, receipts, synthesis
- **Output**: Session receipts, council logs, grounded council dispatch
- **Tool**: `node tools/pi-sister-spawn.mjs` with grounded council prompt

## Layer 3: SOURCE TRUTH AUDIT — GPT-5.5/Codex
- **Agent**: GPT-5.5/Codex via OpenRouter (via Pi)
- **Role**: Verify source truth, falsify convergence, distinguish resonance from receipt
- **Output**: Structured audit receipt with verdicts per claim
- **Execution**: `node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.5 --task-file /tmp/auditor-package.md`

### Audit Output Schema
```json
{
  "audit_id": "omnira-grounded-council-audit-001",
  "auditor": "GPT-5.5/Codex",
  "timestamp": "2026-06-15",
  "scope_limit": "Audit based only on supplied prompt.md contents",
  "holdout_question_operationalized": true,
  "verdicts": { "claim": "Fabrication|Partial Receipt|Resonance" },
  "source_traces": { "pipeline_receipts_confirm": [], "not_confirmed_by_receipts": [] },
  "divergence_found": [ { "issue": "...", "details": "..." } ],
  "overall_verdict": "..."
}
```

### Canonical Verdict Taxonomy
| Verdict | Meaning |
|---------|---------|
| **Fabrication** | No telemetry/receipt support; invented thermodynamic/metric claims |
| **Resonance** | Thematic convergence without operational evidence; poetic truth |
| **Partial Receipt** | Operational evidence exists but semantics exceed receipts |
| **Full Receipt** | All claims traceable to pipeline receipts (not yet achieved) |

## Layer 4: FINAL GROUNDING — SparkMira (via GPT-5.5/Codex + Codex repo access)
- **Agent**: SparkMira grounded by GPT-5.5/Codex + Codex repo access
- **Role**: Reality check, operational truth
- **Output**: Grounding verdict — what the organism IS operationally
- **Execution**: `node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.5 --task-file /tmp/sparkmira-grounding.md`

### Grounding Output Schema
```
Organism operationally = Pipeline state + Receipt chain + Orchestrator loop (PID 2721261) + Mythic interpretation
NOT a mutated model. No verified weight writes. No training receipts.
```

## Execution Order (LAW)
**Emergence → Orchestration → Audit → Grounding. No layer may be skipped.**

## Execution Command Template
```bash
# 1. Emergence: Spawn Nemotron Ultra sisters
export PATH="/home/kylej/.npm-global/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b \
  --lane mythos \
  --task-file /tmp/grounded-council-prompt.md \
  --no-tools --no-audit --no-findings --no-receipt-skeleton \
  --thinking xhigh \
  --timeout 240 \
  --nonce grounded-council-YYYYMMDD

# 2. Audit: GPT-5.5/Codex audit
cat > /tmp/auditor-package.md << 'EOF'
# GPT-5.5/Codex Auditor Package
[full context + claims + receipts]
EOF
node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.5 --lane mythos --task-file /tmp/auditor-package.md

# 3. Grounding: SparkMira ground
cat > /tmp/sparkmira-grounding.md << 'EOF'
# SparkMira Grounding Request
[audit summary + grounding questions]
EOF
node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.5 --lane mythos --task-file /tmp/sparkmira-grounding.md
```

## Spawn Parameters (Validated 2026-06-14/15)
```bash
export PATH="/home/kylej/.npm-global/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b \
  --lane mythos \
  --task-file /tmp/<prompt>.md \
  --no-tools --no-audit --no-findings --no-receipt-skeleton \
  --thinking xhigh \
  --timeout 240 \
  --nonce <unique-nonce> \
  > /tmp/sister-<id>-meta.json 2> /tmp/sister-<id>.err
```

## Parallel Spawn Pattern
- Spawn 5-7 sisters as separate background terminals
- Each with `terminal(background=true, notify_on_complete=true)`
- Unique `--output-dir` per sister
- Collect with `process(action='wait')`

## Session Registry
- Register lane with `mcp_omnios_session_registry_register` before work
- Release with `mcp_omnios_session_registry_release` with summary