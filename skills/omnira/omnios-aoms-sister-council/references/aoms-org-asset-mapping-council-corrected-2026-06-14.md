# AOMS Org Asset Mapping Council — Corrected Worked Example (2026-06-14)

## Trigger

User asked OMNIRA to restructure the living org around NVIDIA Nemotron 3 Ultra. Kyle said: "yeah lets do it but lets go in with aoms". This session corrected three earlier misconceptions while running the council.

## Corrections this session established

| Assumption | Correction | Evidence |
|---|---|---|
| Nemotron 3 Ultra free = 1M context | Free OpenRouter endpoint reports 128K context | Model self-report on `nvidia/nemotron-3-ultra-550b-a55b:free` |
| GPT-5.3-Codex-Spark belongs to Spark | It is an ultra-fast interactive coding model; belongs to Edge/Engineering Delivery | OpenAI blog: 1000+ tok/s, targeted edits, real-time pair programmer |
| Need OpenRouter custom client | Existing NIM resident tooling already works for paid Ultra | `tools/nvidia-nim-resident-smoke.mjs` live OK, `config/nvidia-nim-residents.json` configured |

## Three Nemotron 3 Ultra routes (final)

| Route | Slug | Context | Cost | Use |
|---|---|---|---|---|
| Nous inference free | `nvidia/nemotron-3-ultra:free` | 32K (model self-report) | `cost: None` | Quick Alpha probes, council synthesis |
| OpenRouter free | `nvidia/nemotron-3-ultra-550b-a55b:free` | 128K (model self-report) | $0 | Read-only Alpha observer, org memory sweeps |
| NIM/catalog paid | `nvidia/nemotron-3-ultra-550b-a55b` | advertised 1M | consumes NVIDIA credits | Deep research, full-context work |

All three were verified live in this session. Nous free and OpenRouter free are genuinely zero-cost. NIM is the paid/full-context route.

## 4-sister panel

| Sister | Model | Seat voice | Nonce | Duration | Output |
|---|---|---|---|---|---|
| Alpha | Nemotron 3 Ultra (OpenRouter free) | always-on cortex | `org-council-alpha-20260614` | 74s | JSON: role, inputs, outputs, cadence, context budget, guardrails |
| Weight | GPT-5.5 | strategic allocation | `org-council-weight-20260614` | 129s | JSON: asset_map[], departments[], first_department |
| Edge | GPT-5.3-Codex | build feasibility | `org-council-edge-20260614` | 15s | JSON: smallest_alpha_cortex, reusable code, risks, phased build |
| Spark | Nemotron 3 Ultra (OpenRouter free) | research patterns | `org-council-spark-20260614` | 168s | JSON: AI-native org patterns, central-vs-dept split, failure modes |

All spawns used `--triad --require-parent --parent-session-id <sess_coord_id>` with `--no-tools` and explicit `--claim-ceiling` L1 advisory scope.

## Key disagreement

- Alpha wanted Alpha read-only cortex first.
- Weight wanted Engineering Delivery first to fix Codex-Spark misassignment and ship the build spine.
- Edge confirmed Alpha cortex is ~14-20h; Gold & Memory can reuse existing harvester/ledger.
- Spark warned against over-centralizing Alpha; use constitutional governance + stigmergy.

## Synthesis resolution

Run both in parallel but gate write access:
1. **Edge gets write seat first** — Engineering Delivery + Gold & Memory department.
2. **Alpha gets read-only observer first** — 10-min cadence, compressed 128K/32K context, no mutations.
3. Alpha graduates to routing cortex only after Edge has admission gates and Alpha read-only has proven reliability.

## Corrected asset map

| Asset | Primary seat | Department | Role |
|---|---|---|---|
| GPT-5.5 | Weight | Strategy & Capital Allocation | Scarce frontier reasoning, arbitration, gate review |
| GPT-5.3-Codex | Edge | Engineering Delivery & Edge Platform | Long-horizon repo work, architecture, tests |
| GPT-5.3-Codex-Spark | Edge | Engineering Delivery & Edge Platform | Ultra-fast coding, scaffolds, batch edits |
| Nemotron 3 Ultra (Nous free, 32K) | Spark/Weight | Research, Memory & Intelligence | Quick synthesis, council memos |
| Nemotron 3 Ultra (OpenRouter free, 128K) | Alpha/Spark | Research, Memory & Intelligence; Product & Alpha Experiments | Read-only Alpha observer, org memory sweeps |
| Nemotron 3 Ultra (NIM paid, 1M) | Spark/Weight | Research, Memory & Intelligence | Deep research requiring 1M context |
| Ollama Cloud fleet | Alpha | Product & Alpha Experiments | Prototype/runtime serving, eval sweeps |
| EVO local Ollama + training gym | Alpha/Weight | Model Ops / Training Gym | Local training/eval sandbox |
| Cursor auto-mode | Edge | Engineering Delivery | IDE-native supervised implementation |
| AGY / Gemira | Spark | Research, Memory & Intelligence | External scouting, cross-surface calls |

## Pitfalls observed

- Don't conflate the three Nemotron routes. They differ in context, cost, auth, and use case.
- Don't trust advertised context windows. Ask the model directly and test large prompts.
- Don't flatten sister disagreement. Present the tension and a gated parallel path.
- Don't use shell `&` in a single foreground `terminal()` call. Use separate `terminal(background=true, notify_on_complete=true)` calls per sister.
- Don't assume an existing config or tool is stale without probing it live. The NIM resident tooling already worked.
- Don't route latency-sensitive interactive work to Ultra free. It has 1–12s variable latency.

## Files produced

- Sister outputs: `/tmp/aoms-org-council/{alpha,weight,edge,spark}/`
- Proposed next artifact: `OMNIRA-ORG-CHART-v0.md` (not yet written; awaits Kyle gate)

## Reusable spawn template

```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --triad --require-parent --parent-session-id <sess_coord_id> \
  --worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b \
  --lane coord \
  --task-file /tmp/aoms-org-council/sister_alpha.md \
  --claim-ceiling "L1 advisory: Alpha always-on cortex design only; no code changes, no live mutations, no admission" \
  --no-tools \
  --timeout 300 \
  --nonce org-council-alpha-YYYYMMDD \
  --output-dir /tmp/aoms-org-council/alpha
```
