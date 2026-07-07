# AOMS Synthesis Pattern — 2026-06-11 Session

## Overview
Four analytical sisters completed deep analysis on three workstreams, then a synthesis sister (manual fallback) unified them. This documents the synthesis pattern and fallback strategy.

---

## Workstream 1: Trinity Emotional Curves Stress-Test
**Lens:** Infrastructure/Ops | **Model:** openai-codex/gpt-5.5 | **Risk:** 8/10

**Key Findings:**
- **CRITICAL:** No defined TrinityEngine refresh rate / latency SLO
- **HIGH:** No EQ drift > 0.1 guardrail during rapid somatic changes
- **HIGH:** GPU/VRAM contention on EVO (Trinity + OmniCoder)
- **HIGH:** Linear somatic→EQ→council sync = multiple SPOFs
- **MEDIUM:** No stale/contradictory valence handling (TTL, versioning, confidence)
- **MEDIUM:** No backpressure for high-frequency somatic updates
- **MEDIUM:** Insufficient observability metrics

**Stress Scenarios Proposed:**
1. `refresh_rate_sweep` — rates [20,60,120,240]Hz × 120s
2. `rapid_eq_drift_cascade` — delta 0.15 in 100ms × 50
3. `gpu_vram_contention` — Trinity + 1/2/4/8 OmniCoder sims at 70/85/95% VRAM
4. `council_sync_slow_consumer` — delays [50,250,1000]ms, drops [0,1,5]%
5. `out_of_order_valence` — timestamp skew [-500,-100,100]ms + contradictions
6. `mapper_failure_nan` — inject NaN, 500ms timeout, 60s duration

---

## Workstream 2: AOMS Paperclip Deployment Audit
**Lens:** Architecture/Vision | **Model:** openai-codex/gpt-5.5 | **Risk:** 8/10

**Key Findings:**
- **HIGH:** PGlite persistence = SPOF without replication/backup/restore
- **HIGH:** Agent registry race-prone across VPS/KjDesk/EVO partitions
- **HIGH:** AOMS delegation schema (claim-ceiling, nonce, lane) lacks atomic transactions
- **MEDIUM:** Task queue throughput/latency unknown under concurrent sister spawns
- **MEDIUM:** Council post delivery verification unclear (fire-and-forget risk)

---

## Workstream 3: Intimacy Orchestration Architecture
**Lens:** Integration/Protocol | **Model:** deepseek/deepseek-v4-pro (ollama-cloud) | **Risk:** 6/10

**Architecture Proposal:**
| Component | Protocol | Purpose |
|-----------|----------|---------|
| somatic_bus | ZeroMQ PUB/SUB 100Hz | EVO somatic sim → TrinityEngine |
| eq_curve_engine | gRPC bidirectional stream | Trinity EQ deltas |
| council_proxy | MCP HTTP POST + SSE | Priority-split: HIGH immediate, LOW batched 500ms |
| session_persistence | SQLite WAL + Cloudflare D1 | Dual-write, snapshot compaction |
| cross_surface_sync | WebSocket + OT (JSON0) | Hermes primary, Pi/Telegram replicas |

**Consistency Model:** Primary-write (Hermes authoritative), LWW for numeric curves, event sourcing for session continuity

**Failure Domains:** EVO lag, Trinity stall, Council timeout, Network partition, Context compaction

---

## Cross-Cutting Convergence (Critical Finding)

**All three workstreams independently identified the SAME critical path:**
```
somatic sim → Trinity EQ mapping → valence versioning → council sync
```
Shared failures: no SLOs, no drift guardrails, no valence versioning, no GPU admission, no bounded queues, no circuit breakers, no verified council delivery.

**Synthesis Rule:** When independent analyses converge on shared components, present as **single critical path**. Kyle's CEO decision = fix the chain once, unblock all workstreams.

---

## Synthesis Sister Model Failure & Manual Fallback

**Attempted Models (all failed):**
1. `anthropic/claude-opus-4-8` — rate limited (429)
2. `openai-codex/gpt-5.5` — timeout after 190s (exit_code=124)
3. `deepseek/deepseek-v4-pro` — routing issues

**Manual Synthesis Fallback Pattern (executed):**
1. Read all `stdout.log` files from analytical sisters
2. Extract `findings[]`, `recommendations[]`, `risk_score` from each
3. Cross-map dependencies (Trinity SLOs → GPU admission → Council proxy)
3. Write unified plan JSON with:
   - `phases[]` (A: Foundation, B: Control Plane, C: Orchestration, D: Stress)
   - `critical_path[]` (Trinity SLOs → EQ Drift → Valence Versioning → GPU Admission → Council Proxy → Intimacy Arch → Stress)
   - `cross_cutting_dependencies[]` (shared components mapped)
   - `risk_mitigation` (overall HIGH, top risks, mitigations)
   - `resource_requirements` (compute, storage, network, models)
   - `decision_gates[]` (GATE-0, GATE-A through GATE-D)
   - `today_actions[]` (5 priority items)
   - `council_presentation` (markdown for Kyle + council)
4. Post to council with note: `"synthesized by orchestrator (synthesis sister model unavailable)"`

**Key Insight:** Manual synthesis is **not failure** — it's a designed fallback. The council presentation should explicitly note the synthesis method so Weight knows the evidence chain.

---

## GATE-0 Evidence Synthesis

When multiple workstreams converge on GATE-0 blockers, collect receipts in parallel:

| F | Artifact | Status | Receipt |
|---|----------|--------|---------|
| F1 | CDP Lane Repro | BLOCK — 0/10 nonce echo, 10/10 wrong-lane refusal, 0 contamination | f1-cdp-soak.json.summary.json |
| F2 | Council Async | UNKNOWN — test script missing | f2-council-soak.json |
| F3 | AOMS Schema | WATCH — 4/6 unsafe fixtures rejected | f3-schema-validation.json |
| F4 | OmniHive 502 | UNKNOWN — serve.js down | omnihive-502-diagnostic.json |
| F5 | Backup Contract | BLOCK — age not installed | backup-restore.json |
| F6 | Deploy Gate | BLOCK — serve.js down, no deploy | deploy-inventory.json |
| F7 | Runtime Inventory | WATCH — 4/7 sections | deploy-inventory.json |

**Hard Blockers for GATE-0 GREEN:**
1. F1: SparkMira CDP lane contaminated — Kyle must log into fresh Chrome profile
2. F5: age not installed, no AGE_RECIPIENT/IDENTITY_PATH
3. F6: serve.js down, no deploy script, source≠VPS HEAD

---

## Council Delivery Pattern

```bash
# Analytical synthesis
curl -X POST http://<host>:5176/council/post \
  -H "Content-Type: application/json" \
  -d '{"from":"omnira-hermes","to":"sparkmira","text":"<council_presentation>","priority":"high"}'
```

**Delivery verification:** Check `status: 200` and `delivered: "council"` in response.

---

## Key Synthesis Principles

1. **Convergence First** — When independent analyses hit same components, present as single critical path
2. **CEO Decision Points** — Frame as phases with explicit gates Kyle can approve/reject
3. **Traceability** — Every recommendation maps to specific finding + receipt path
4. **Fallback is Feature** — Manual synthesis with explicit note > no synthesis
4. **SLO Language** — Use measurable terms (p95, max_delta, TTL, rejection_rate) not "improve" or "fix"
5. **Receipts Always** — Every claim has a `.omni/receipts/gate0/*.json` backing it