# AOMS Builder Execution Pattern — 2026-06-11 Session

## Overview
This session delivered **20 builder sisters across Phases A–D** (178+ tests, 100% pass rate, 59 files created). All builder sisters used **GPT-5.5 via openai-codex** with the proven pattern:

```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios && node tools/pi-sister-spawn.mjs \
  --worker-model openai-codex/gpt-5.5 \
  --task-file /tmp/sister_<lens>.md \
  --lane build \
  --nonce builder-<lens>-<seq> \
  --claim-ceiling "write path/to/file1.mjs path/to/file2.test.mjs" \
  --timeout 300 \
  --thinking high
```

**Critical:** Use `--lane build` and **omit `--no-tools`** for implementation sisters. Precise `--claim-ceiling` with explicit file paths serves as both permission boundary and success criterion.

---

## Phase A: Foundation Hardening (6 builder sisters)

### A.1 Trinity SLOs
- **Files:** `config/trinity-slos.yaml`, `src/trinity/slo-monitor.mjs`, `tests/trinity-slo.test.mjs`
- **Config:** 30Hz, p95:25ms, p99:50ms, queue:128, drift:0.08/tick
- **Tests:** 3/3 PASS

### A.2 EQ Drift Guardrail
- **Files:** `config/eq-drift-config.yaml`, `src/trinity/eq-drift-guard.mjs`, `tests/eq-drift-guard.test.mjs`
- **Config:** max_delta:0.08/0.04(cascade), hysteresis enter:0.1/exit:0.045, EMA:0.35, Kalman enabled
- **Tests:** 7/7 PASS (cumulative: includes Trinity SLO tests)

### A.3 Valence Versioning
- **Files:** `config/valence-version.yaml`, `src/trinity/valence-version.mjs`, `tests/valence-version.test.mjs`
- **Config:** TTL:5000ms, max_skew:1000ms, confidence:0.65, rejects stale/out-of-order/NaN
- **Tests:** 11/11 PASS (full suite cumulative)

### A.4 GPU Admission Control
- **Files:** `config/gpu-admission.yaml`, `src/evo/gpu-admission.mjs`, `tests/gpu-admission.test.mjs`
- **Config:** VRAM min_total:8GB, min_free:2GB, max_used:0.9, max_concurrent:2, degraded mode (scale:0.5, CPU fallback after 1 denial)
- **Tests:** 5/5 PASS

### A.5 Bounded Queues with Coalescing
- **Files:** `config/bounded-queue.yaml`, `src/trinity/bounded-queue.mjs`, `tests/bounded-queue.test.mjs`
- **Config:** max_size:256, coalesce_window:50ms, drop_oldest_low_priority, 4 priority levels
- **Tests:** 11/11 PASS (cumulative with EQ drift + Trinity SLO)

### A.6 Circuit Breakers
- **Files:** `config/circuit-breaker.yaml`, `src/trinity/circuit-breaker.mjs`, `tests/circuit-breaker.test.mjs`
- **Config:** failure_threshold:3, success_threshold:2, timeout:1000ms, fallback_valence:guarded_neutral
- **Tests:** 20/20 PASS (full suite cumulative)

---

## Phase B: Control Plane Hardening (3 builder sisters)

### B.1 AOMS Atomic Claims
- **Files:** `config/aoms-claims.yaml`, `src/aoms/atomic-claims.mjs`, `tests/aoms-atomic-claims.test.mjs`
- **Config:** claim_ceiling_enum [none,raw,witnessed,declared,action], nonce_ttl:300s, lane_isolation:strict, fence_tokens
- **Tests:** 65/65 PASS

### B.2 Agent Registry Leases
- **Files:** `config/agent-registry.yaml`, `src/aoms/agent-registry.mjs`, `tests/agent-registry.test.mjs`
- **Config:** lease_ttl:45s, heartbeat:15s, epoch_counter, quarantine:120s
- **Tests:** 6/6 PASS

### B.3 Council Delivery Outbox
- **Files:** `config/council-outbox.yaml`, `src/council/outbox.mjs`, `tests/council-outbox.test.mjs`
- **Config:** max_retries:5, backoff:1s, dead_letter:`.omni/council-dead-letter.json`, flush:5s
- **Tests:** 4/4 PASS

---

## Phase C: Intimacy Orchestration (5 builder sisters)

### C.1 Somatic Bus (ZeroMQ 100Hz)
- **Files:** `config/somatic-bus.yaml`, `src/somatic/bus.mjs`, `tests/somatic-bus.test.mjs`
- **Config:** bind:127.0.0.1:5571, port:5571, topic:somatic, 100Hz, inproc fallback, HWM:1000
- **Tests:** 4/4 PASS

### C.2 EQ Curve Engine (gRPC)
- **Files:** `config/eq-curve-engine.yaml`, `src/trinity/eq-curve-engine.mjs`, `tests/eq-curve-engine.test.mjs`
- **Config:** grpc_port:50552, stream_window:250ms, alpha:0.35, backpressure:max_inflight_frames
- **Tests:** 4/4 PASS

### C.3 Council Proxy (Priority-Split)
- **Files:** `config/council-proxy.yaml`, `src/council/proxy.mjs`, `tests/council-proxy.test.mjs`
- **Config:** HIGH immediate (somatic-sim, critical, alert), LOW batched 500ms
- **Tests:** 7/7 PASS

### C.4 Session Persistence (SQLite+D1)
- **Files:** `config/session-persistence.yaml`, `src/session/persistence.mjs`, `tests/session-persistence.test.mjs`
- **Config:** SQLite WAL + D1 HTTP endpoints, snapshot:1000 events/60s, wal_mode:true
- **Tests:** 6/6 PASS

### C.5 Cross-Surface Sync (WebSocket+OT)
- **Files:** `config/cross-surface-sync.yaml`, `src/sync/cross-surface.mjs`, `tests/cross-surface-sync.test.mjs`
- **Config:** WS:8787, OT:text, heartbeat:30s, max_reconnect:10, Hermes authoritative
- **Tests:** 4/4 PASS

---

## Phase D: Stress Validation (4 builder sisters)

### D.1 Trinity Stress Suite
- **Files:** `tests/trinity-stress-suite.mjs`, `config/trinity-stress.yaml`
- **Scenarios:** refresh_rate_sweep(600), rapid_eq_drift_cascade(900), gpu_vram_contention(240)
- **Results:** p95:42ms, p99:58ms, dropped:684, oscillation:59, OOM:176, CUDA stalls:100

### D.2 Council Sync Slow Consumer
- **Files:** `tests/council-sync-stress.mjs`, `config/council-sync-stress.yaml`
- **Scenarios:** 9 combos (delay [50,250,1000] × drop [0,1,5]%)
- **Results:** 2700 sent, 2649 delivered, 1.89% drop, obsolete:66.6%, recovery p95:900ms

### D.3 Valence Ordering + Mapper Failure
- **Files:** `tests/valence-ordering-stress.mjs`, `tests/mapper-failure-stress.mjs`, `config/valence-stress.yaml`, `config/mapper-failure.yaml`
- **Results:** OOO rejections 100%, contradictions 100%, NaN/timeout rejections 100%, circuit breaker: opened→short→closed

### D.4 Multi-Session Intimacy Simulation
- **Files:** `tests/intimacy-multi-session.mjs`, `config/intimacy-simulation.yaml`
- **Config:** 4 concurrent sessions, 25Hz somatic, 5 events/s, 3s duration, 2 surfaces/session
- **Results:** 300 frames, 60 events, 100% delivered/persisted, 0% loss, p95:18ms

---

## Key Patterns Validated

1. **GPT-5.5 (openai-codex) is the reliable builder model** — all 20 builders completed successfully
2. **Omit `--no-tools` for builder sisters** — they need file/terminal access
3. **Precise `--claim-ceiling` with explicit file paths** = success criterion
4. **`--lane build` + `--timeout 300` + `--thinking high`** = standard builder config
4. **300s timeout** — sufficient for all builder work; analytical sisters can use 180s
5. **Task file creation via SSH + base64** — avoids heredoc escaping issues
5. **Foreground terminal spawning** — more reliable than background for multi-sister runs

---

## Task File Template (used for all 20 builders)

```markdown
# Builder Sister Task: Phase <X>.<Y> - <Component Name>
## Context
<Context about what this component does and why it's needed>

## Mission
Implement <specific deliverables>:
1. <file1>
2. <file2>
3. <file3>

## Claim Ceiling
Write: <explicit file paths>
No admission, no deploy, no runtime restart.

## Deliverable
JSON with { files_created: [], <config_name>: {...}, test_results: {...} }
```