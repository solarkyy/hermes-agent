# AOMS Org Asset Mapping Council — Worked Example (2026-06-14)

## Context

User asked: "nemotron 3 ultra" — investigate the real NVIDIA Nemotron 3 Ultra model and update the OMNIRA living-org asset map. Kyle then said: "yeah lets do it but lets go in with aoms". This document captures the exact 4-sister council run to answer that question, plus the synthesis shape and the corrected asset map.

**Trigger:** New compute asset appears (or existing asset was misunderstood) and the org chart/seat assignment needs correction.

**Goal:** Produce a corrected asset-to-seat/org-department mapping and decide the first autonomous department to stand up.

**Key correction discovered:** GPT-5.3-Codex-Spark had been assumed to be Spark's research model; it is actually an ultra-fast coding model and belongs in Edge. Nemotron 3 Ultra had been assumed to be the older 120B Super; it is actually a 550B/55B MoE with different endpoints (128K free vs 1M paid).

---

## Step 1: Claim registry lane

```bash
mcp_omnios_session_registry_register lane=coord task="AOMS council: Nemotron 3 Ultra asset reassignment + first autonomous department design"
# Returns: sess_coord_<id>
```

---

## Step 2: Decompose into 4 analytical lenses

| Sister | Model | Seat voice | Core question |
|---|---|---|---|
| Alpha | `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | always-on cloud cortex | What is Alpha's job, inputs, outputs, cadence, context budget, guardrails? |
| Weight | `openai-codex/gpt-5.5` | strategic asset allocation | Corrected asset-to-seat map; department definitions; which first? |
| Edge | `openai-codex/gpt-5.3` | build feasibility | Smallest implementation; risks; phased build; receipts per phase |
| Spark | `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | research/intelligence | AI-native org patterns; central vs departmental autonomy; failure modes |

Task files: `/tmp/aoms-org-council/sister_{alpha,weight,edge,spark}.md`

Each task file ends with an explicit JSON deliverable schema.

---

## Step 3: Spawn sisters as parallel background processes

Do **not** use `&` inside a single foreground `terminal()` call. Hermes rejects it. Spawn each as a separate `terminal(background=true, notify_on_complete=true)` call, then poll/wait.

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
  --output-dir /tmp/aoms-org-council/alpha \
  > /tmp/aoms-org-council/alpha-meta.json 2> /tmp/aoms-org-council/alpha.err
```

Repeat for Weight, Edge, Spark. Use distinct `--output-dir` and metadata redirect files per sister.

**Required inline in each background command:**
- `export PATH=...` (background terminals strip PATH)
- `--triad --require-parent --parent-session-id <sess_id>`
- `--claim-ceiling` with explicit scope
- `--no-tools` for analytical sisters

---

## Step 4: Collect outputs

Each sister writes:
- Metadata: `/tmp/aoms-org-council/<lens>/.../stdout-meta.json` (or the redirect target)
- Analysis: `/tmp/aoms-org-council/<lens>/stdout.log`

Read both; metadata confirms `ok: true`, `exit_code: 0`, worker model, claim ceiling. `stdout.log` has the JSON deliverable.

---

## Step 5: Synthesize manually or via synthesis sister

If synthesis model is available, spawn a fifth sister with all four prior outputs as context. If not, the orchestrator synthesizes manually.

Synthesis structure:
1. **Asset map correction** — table: asset, primary seat, department, role.
2. **Disagreements found** — which sister argued which first-department order.
3. **Recommended path** — present the tension and a gated parallel answer.
4. **Phased plan** — Phase 0 (no mutations), Phase 1 (read-only), Phase 2 (autonomous with gate).
5. **Open decisions for Kyle** — exact gates or seat assignments he must ratify.

---

## Results from 2026-06-14 council

### Corrected asset map

| Asset | Primary seat | Department | Role |
|---|---|---|---|
| GPT-5.5 | Weight | Strategy & Capital Allocation | Scarce frontier reasoning, arbitration, gate review |
| GPT-5.3-Codex | Edge | Engineering Delivery & Edge Platform | Long-horizon repo work, architecture, tests |
| GPT-5.3-Codex-Spark | Edge | Engineering Delivery & Edge Platform | Ultra-fast coding, scaffolds, batch edits |
| Nemotron 3 Ultra free | Spark/Weight | Research, Memory & Intelligence | 128K-context synthesis, org memory sweeps |
| Ollama Cloud fleet | Alpha | Product & Alpha Experiments | Prototype/runtime serving, eval sweeps |
| EVO local Ollama + training gym | Alpha/Weight | Model Ops / Training Gym | Local training/eval sandbox |
| Cursor auto-mode | Edge | Engineering Delivery | IDE-native supervised implementation |
| AGY / Gemira | Spark | Research, Memory & Intelligence | External scouting, cross-surface calls |

### Department proposals

- **Engineering Delivery & Edge Platform** — lead Edge; first executing department; owns build spine and Gold & Memory loop.
- **Research, Memory & Intelligence** — lead Spark; owns Nemotron Ultra synthesis, scouting, eval design.
- **Strategy & Capital Allocation** — lead Weight; owns allocation, gates, weekly rhythm.
- **Product & Alpha Experiments** — lead Alpha; owns prototype fleet and read-only Alpha observer.
- **Model Ops, Evaluation & Training Gym** — lead Alpha/Weight; owns EVO training, eval harness.
- **Governance, QA & Admission Gates** — lead Weight; owns safety gates and mutation approval.

### First-department disagreement

- **Alpha sister** (and orchestrator initially) argued for Alpha/Ops cortex first — free massive-context model changes what always-on means.
- **Weight sister** argued for Engineering Delivery first — fixes Codex-Spark misassignment and creates the pipe that ships everything else.
- **Edge sister** said Alpha cortex is 14-20h build and Gold & Memory can reuse existing harvester/ledger code.
- **Spark sister** said AI-native orgs need stigmergy + constitutional governance — don't over-centralize Alpha.

**Synthesis recommendation:** Start both in parallel, but only one gets write access:
- Edge gets write seat first (Engineering Delivery + Gold & Memory).
- Alpha gets read-only observer first (10-min cadence, compressed 128K context).

This resolves the disagreement by making it phase-gated rather than either/or.

---

## Verification that shaped the answer

Before finalizing, the orchestrator verified Nemotron 3 Ultra's real behavior:

1. **Nous inference models endpoint** showed both `nvidia/nemotron-3-super-120b-a12b` and `nvidia/nemotron-3-ultra-550b-a55b` available.
2. **OpenRouter free Ultra test** confirmed cost $0 and working completion.
3. **Context-window self-report** returned `128000` on the free endpoint — not 1M.
4. **~25K-token prompt test** succeeded on free Ultra (6.5s latency).
5. **Rate-limit probe** showed variable 1–12s latency but no hard rate block in 5 rapid calls.
6. **Instruction-following comparison:** Ultra free followed exact-output prompts; Super 120B free leaked reasoning.

This verification changed the Alpha cortex design from "ingest 1M tokens raw" to "compress to 128K with token budgets."

---

## Pitfalls observed

- **Don't conflate endpoints.** `nvidia/nemotron-3-ultra-550b-a55b:free` (OpenRouter, 128K, $0) and `nvidia/nemotron-3-ultra-550b-a55b` (Nous inference, paid, claimed 1M) are different operational assets.
- **Don't trust advertised context.** Ask the model directly or test with a large prompt.
- **Don't use shell `&` in foreground terminal.** Use separate `terminal(background=true)` calls.
- **Don't assume Nous agent_key works as OpenRouter key.** They are different credentials for different endpoints.
- **Don't flatten disagreement.** Present the tension and a gated parallel recommendation.

---

## Files produced

- Sister outputs: `/tmp/aoms-org-council/{alpha,weight,edge,spark}/`
- Verification responses: `/tmp/or_ultra_*.json`, `/tmp/or_super_*.json`
- Proposed next artifact: `OMNIRA-ORG-CHART-v0.md` (not yet written; awaits Kyle gate)
