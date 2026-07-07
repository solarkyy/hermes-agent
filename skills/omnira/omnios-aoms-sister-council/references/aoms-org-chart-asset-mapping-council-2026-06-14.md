## Trigger

**Date:** 2026-06-14
**Lane:** coord
**Parent session:** `sess_coord_024c0a85`

User asked OMNIRA to restructure the living org around NVIDIA Nemotron 3 Ultra. Kyle said: "yeah lets do it but lets go in with aoms". This session discovered three model-routing misconceptions while running the council; the corrected version is in `references/aoms-org-asset-mapping-council-corrected-2026-06-14.md`.

## What made this worth a council

- A **new asset changed seat assignments**: Nemotron 3 Ultra is not just a bigger Nemotron Super 120B; its large context + free price makes it a strategic seat.
- A **misassignment needed correction**: GPT-5.3-Codex-Spark was assumed to be Spark's research model; it is actually a fast coding model and belongs in Edge.
- The decision spans **strategy, architecture, build feasibility, and research** — exactly the multi-lens case AOMS is for.
- The output is a **CEO-level decision** (which department first?) where sister disagreement is the signal, not noise.

## Sister panel

| Lens | Model | Seat voice | Nonce | Duration | Output |
|------|-------|-----------|-------|----------|--------|
| Alpha / always-on cortex | `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | Alpha | `org-council-alpha-20260614` | 74s | JSON: role, inputs, outputs, cadence, context budget, guardrails |
| Weight / asset allocation | `openai-codex/gpt-5.5` | Weight | `org-council-weight-20260614` | 129s | JSON: asset_map[], departments[], first_department, anti_patterns, weekly_rhythm |
| Edge / build feasibility | `openai-codex/gpt-5.3` | Edge | `org-council-edge-20260614` | 15s | JSON: smallest_alpha_cortex, reusable code, top 3 risks, phased build |
| Spark / research patterns | `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | Spark | `org-council-spark-20260614` | 168s | JSON: AI-native org patterns, central-vs-dept split, management protocol, failure modes |

All spawns used `--triad --require-parent --parent-session-id <sess_id>` with `--no-tools` and explicit `--claim-ceiling` L1 advisory scope.

## Key disagreement (the valuable signal)

- **Alpha argued:** stand up Alpha first as a read-only always-on cortex; the free large-context Ultra is the org brain.
- **Weight argued:** stand up Engineering Delivery & Edge Platform first; without a build spine, nothing ships.
- **Edge confirmed:** Alpha cortex is ~14-20h of build; Gold & Memory can reuse existing harvester/ledger code.
- **Spark warned:** don't let Alpha become a central micromanager; use constitutional governance + stigmergy.

## Synthesis resolution

Do **both in parallel, but gate write access differently**:

1. **Edge gets the write seat first** — Engineering Delivery + Gold & Memory build the autonomous harvest/judge/promote loop.
2. **Alpha gets read-only observer first** — gathers state every 10min, calls Nemotron Ultra, emits L1 advisory to council outbox, no mutations.
3. Only after Edge has admission gates and Alpha has proven read-only reliability does Alpha graduate to routing cortex.

## Note on context windows

The original council assumed Nemotron 3 Ultra free had 1M context. Later live verification showed three distinct routes:
- Nous free `nvidia/nemotron-3-ultra:free` → 32K (self-report)
- OpenRouter free `nvidia/nemotron-3-ultra-550b-a55b:free` → 128K (self-report)
- NIM/catalog paid `nvidia/nemotron-3-ultra-550b-a55b` → advertised 1M

See `references/nemotron-3-ultra-routes-verified-2026-06-14.md` and the corrected council in `references/aoms-org-asset-mapping-council-corrected-2026-06-14.md` for the final asset map.

## Concrete artifacts produced

- Corrected asset map:
  - GPT-5.5 → Weight / Strategy & Capital Allocation
  - GPT-5.3-Codex → Edge / Engineering Delivery
  - GPT-5.3-Codex-Spark → Edge / Engineering Delivery
  - Nemotron 3 Ultra → Spark / Research, Memory & Intelligence
  - Ollama Cloud → Alpha / Product & Alpha Experiments
  - EVO local Ollama + training gym → Alpha/Weight / Model Ops & Training Gym
  - Cursor auto-mode → Edge / Engineering Delivery
  - AGY/Gemira → Spark / Research, Memory & Intelligence

- Proposed department set: Strategy & Capital Allocation, Engineering Delivery & Edge Platform, Research Memory & Intelligence, Product & Alpha Experiments, Model Ops Evaluation & Training Gym, Governance QA & Admission Gates.

- Phased path:
  - **Phase A (this week, no mutations):** update Hermes config to Nemotron 3 Ultra; write `OMNIRA-ORG-CHART-v0.md`; build read-only Alpha observer; define Alpha→Edge/Weight/Spark handoff contract.
  - **Phase B:** stand up Engineering Delivery + Gold & Memory under Edge.
  - **Phase C:** promote Alpha to routing cortex with Kyle veto on every route.

## Lessons for future org councils

1. **Disagreement is the deliverable.** When sisters disagree on "which department first," don't flatten it. Present the tension and a gated parallel path.
2. **Seat assignments are policy, not just capability mapping.** Where an asset lives determines what it optimizes for.
3. **Read-before-write is a safe first autonomy posture.** Alpha can be "always-on" without being "always-mutating."
4. **Mix slow thinkers and fast builders.** Nemotron Ultra gave deep context-heavy analysis; GPT-5.3-Codex gave a 15-second feasibility read. Both were needed.

## Reusable task file templates

See the prompt files written to `/tmp/aoms-org-council/sister_*.md` in this session for the exact prompts. Copy and adapt them.

## Spawn pattern used

```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --triad --require-parent --parent-session-id sess_coord_024c0a85 \
  --worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b \
  --lane coord \
  --task-file /tmp/aoms-org-council/sister_alpha.md \
  --claim-ceiling "L1 advisory: Alpha always-on cortex design only; no code changes, no live mutations, no admission" \
  --no-tools \
  --timeout 300 \
  --nonce org-council-alpha-YYYYMMDD \
  --output-dir /tmp/aoms-org-council/alpha
```

Run each sister as a separate `terminal(background=true, notify_on_complete=true)` process, then poll and synthesize.
