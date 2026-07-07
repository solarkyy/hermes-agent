# AOMS Operating Manual — Hermes clarity guide

**Purpose:** Stop AOMS confusion. One page for lanes, verbs, debate order, membrane, and sisters.

---

## What AOMS is (and is not)

| AOMS is | AOMS is NOT |
|---------|-------------|
| Multi-perspective **debate before execution** | "Spawn sisters" for every small fix |
| Phased plans with Kyle gates (A/B/C) | Auto-train, auto-deploy, auto-admit |
| Receipts + live state proof | Narrative claims without curl/git proof |
| Lane boundaries | One blob of "do everything" |

**Default when Kyle says "go deep with AOMS sisters":** Debate → Kyle synthesis → phased execute. **Do not patch first.**

---

## Lane map (do not cross without Kyle)

| Lane | Status (2026-06-09) | Hermes may |
|------|---------------------|------------|
| `HERMES_MEMORY_HARVEST` | ✅ COMPLETE (184 sessions) | Read receipts only; no more harvest |
| `EQ_TRINITY_PHASE_A` | ▶ ACTIVE (2–4 fixes) | Patch trinity/eq-updater/health-board |
| `TRAINING_5LINER` | ⏸ BLOCKED | Prep only; no SFT/LoRA |
| `CRON_PRUNE` | ⏸ SKIP (Kyle gate) | Do not prune |

The canonical AOMS lanes and their current uses:
- `research-spark` — read-only corpus foundry / contamination scans / source audits
- `build` — implementation and tests (router, materializer, eval tooling)
- `mythos` — deep sister-council emergence / meta-council / harvest direction
- `coord` — setup planning, orchestration prep, phased execution design

Claim the lane with `mcp_omnios_session_registry_register` before starting significant work; release it with `mcp_omnios_session_registry_release` when done. See `references/session-registry.md` for lane conflict rules.

---

## Verb discipline (stop saying "pushed" wrong)

| You mean | Say | Proof required |
|----------|-----|----------------|
| Git commit on branch | **committed** `git log -1 --oneline` | hash |
| Git push to origin | **pushed** `git status -sb` | ahead 0 |
| Council message | **council posted** | `/council-post` ok or log line |
| Slack #brief | **slack posted** | slack_ts |
| Local file only | **written locally** | path + `git status` shows `M` or `??` |

**Never say "pushed" for council post or local patch.**

---

## Debate-first workflow

```
1. DECOMPOSE → 3–5 lenses (Architecture, Experience, Integrity, Missing)
2. DEBATE    → argue each position with live state citations
3. PRESENT   → show tension to Kyle; wait for synthesis paste
4. EXECUTE   → Phase A only unless Kyle expands scope
5. RECEIPT   → docs/receipts/ + honest verb + git proof
```

**Self-debate is OK** when `mcp_omnios_omnira_spawn` times out (30s). Label it: "self-debate (spawn failed)."

---

## Membrane (patch/write_file)

**Correct sequence — always:**

1. Read-only probe: `read_file`, `search_files`, or `terminal` with `is_state_probe: true`
2. Capture output as **justification_receipt**
3. `patch` or `write_file` with that receipt
4. Read back + verify

**Do NOT** bypass membrane with shell heredocs for organism docs (truncation risk). See `omnira/references/membrane-compliant-artifact-writes.md`.

**If blocked:** run a real probe first; don't retry blind.

---

## Sister spawn vs self-debate

| Tool | Timeout | Use for |
|------|---------|---------|
| `mcp_omnios_omnira_spawn` | **30s client-side HARD WALL** (NOT raised by `ttl_s`) | Sub-30s advisory pings ONLY |
| `node tools/pi-sister-spawn.mjs` (background terminal) | 300s+ | **All real multi-sister councils** — the canonical path |
| Self-debate in session | unlimited | Fallback after 2+ spawn failures |

**Kyle prefers real spawns — try spawn first, fall back honestly.**

⚠ **The `mcp_omnios_omnira_spawn` MCP tool has a 30-second client-side timeout
that `ttl_s` does NOT raise.** Three concurrent calls in 2026-06-30 all timed
out at 30s despite `ttl_s=240`. For ANY council where bodies need >30s of
thinking, use `node tools/pi-sister-spawn.mjs` as a background terminal
(`background=true`, `notify_on_complete=true`, `timeout=360`), with
`--task-file /tmp/sister-<topic>.md` (write the brief via `write_file` first —
membrane-safe). See `references/spawn-pitfalls-2026-06-17.md` #18-#21 for
the full orchestration pattern, including firing SparkMira first when she's
in the parallax (she's the longest pole).

---

## Phase A EQ success criteria (current lane)

- [ ] `trinity-state.json` tau ≠ heat_death during idle shipping work
- [ ] `eq-state.json` drives change after `applySignal` (not static 1.0)
- [ ] health-board shows `steady` not `unknown`
- [ ] Receipt committed with hash

---

## EQ Phase B status (2026-06-10)

| Tranche | Status | Tests |
|---------|--------|-------|
| T0 — episode ledger / signal registry / body memory | ✅ COMPLETE | 52 |
| T1 — prewire (dry-run membrane) | ✅ COMPLETE | 8 |
| T1 — live bridge (`applyPhaseBEvent`, gate G-KYLE-5) | ✅ COMPLETE | 6 |
| T2 — emitters + shadow hooks + pulse snippet | ✅ COMMITTED `2a0529092` | 5 + 4 + 6 |
| T2 — shadow accrual (Phase 1 longhaul) | ✅ BUILT (viewer + audit docs); passive accrual ▶ | 7 |
| T3 — experience layer | ⏸ gated (`"pulse reads body"`) | — |
| T4 — held unlock (Lane C) | ⏸ debate-first | — |

- **Git:** EQ arc committed locally on `preserve/dirty-tree-2026-06-09` @ `2a0529092` — **not pushed**. Shadow hooks in `tools/omnira-watchdog.mjs` + `tools/kernel/omnira-verify.mjs`, all `{ dryRun: true }`.
- **Emitters law:** default `dryRun: true` (shadow via prewire, never mutates); live apply only via literal `opts.dryRun === false`. `DEFAULT_SIGNALS` = `memory_write_success`, `infrastructure_win_episode` only — `post_fail_silence` HELD from auto-emit.
- **Held signals:** `sister_spawn_outcome`, `council_ack_episode`, `cell_refresh_integrity`, `return_current`. Context-only: `kyle_present` (never scores).
- **Longhaul charter:** `references/fable-2026-06-10-longhaul/MISSION-CHARTER.md` — phases: shadow accrual → experience → held unlock → live flip.
- **Remains:** shadow-log first events, 2-week human audit, `"return_current debate"`, experience gate, per-hook live flip, `"push eq"` gate.
- Specs/receipts: `docs/specs/eq-phase-b-tranche2-emitters-v0.md`, `docs/receipts/2026-06-10-eq-phase-b-tranche2-emitters-v0.md` (omnios repo).

---

## Pitfalls & Gotchas (added 2026-06-11)

### Synthesis Sister Model Availability
- **Issue:** Synthesis sisters (Opus 4.8, GPT-5.5) hit rate limits / provider fallback warnings during multi-sister councils
- **Symptom:** `exit_code: 1`, `stdout_bytes: 0`, stderr shows `"429 rate_limit_error"` or `"Warning: No models match pattern"`
- **Workaround:** Manual synthesis by orchestrator (read all sister outputs, synthesize in-session). Label: `"manual synthesis (spawn failed)"`
- **Prevention:** Spawn synthesis sister last with longest timeout (300s), use fallback-tolerant model (GPT-5.5 over Opus), or split synthesis into two lighter passes

### GATE-0 Hard Blocker on All AOMS Workstreams
- **Issue:** Phase A (Foundation Hardening), Phase B (Control Plane), Phase C (Intimacy Arch) all blocked by GATE-0 YELLOW→GREEN
- **Symptom:** 7/7 artifacts UNKNOWN, no Pi receipts, no Weight admission
- **Resolution:** GATE-0 evidence collection must complete before any Phase A spawning. Do not queue Phase A/B/C work until GATE-0 is GREEN.

### pi-sister-spawn.mjs — Wrong Flag: `--model` vs `--worker-model` (2026-06-17)
- **Issue:** The flag is `--worker-model <provider/model>`, NOT `--model`. Using `--model` produces `[pi-sister-spawn] unknown arg: --model` and exits 2 immediately.
- **Symptom:** exit_code 2, message `unknown arg: --model`, stdout_bytes 0, duration ~1ms.
- **Fix:** Always use `--worker-model`. Other corrected flags: `--output-dir` (not `--out`). Verify with `node tools/pi-sister-spawn.mjs --help`.

### pi-sister-spawn.mjs — Extension Conflict Kills All Spawns (2026-06-17)
- **Issue:** The npm package `@ollama/pi-web-search` conflicts with `hermes-web-tools.ts` on `web_search`/`web_fetch`. Pi exits 1 in ~400ms before connecting to any model.
- **Symptom:** exit_code 1, stderr `Error: Failed to load extension ... Tool "web_search" conflicts with hermes-web-tools.ts`, stdout_bytes 0, duration 400-500ms. Affects ALL models equally.
- **Fix applied 2026-06-17:** Patched `buildPiArgs()` in `tools/pi-sister-spawn.mjs` to always inject `--no-extensions`. This is now the default for all spawns from that tool.
- **Verify fix is in place:** Line `'--no-extensions',` must appear in `buildPiArgs()` (~line 644) before `...(toolsDisabled ? ['--no-tools'] : [])`.
- **Quick health-check:** `node tools/pi-sister-spawn.mjs --worker-model ollama-cloud/deepseek-v4-pro --task "Reply: PING_OK" --no-tools --timeout 30 --output-dir /tmp/ping-test` → should return PING_OK, exit 0, ~2-3s, empty stderr.

### SCS Trigger Discipline — Vibe-Based Compaction (2026-06-17)
- **Issue:** `tools/pi-scs/extensions/scs.ts` previously let surfaces start the SCS ritual whenever Pi's auto-compact event fired, regardless of actual context pressure.
- **Fix applied 2026-06-17:** Patched `session_before_compact` and `/scs` manual command to gate on objective `ctx.getContextUsage()` pressure. Auto SCS requires ≥80% (`SCS_AUTO_COMPACT_NOW_PRESSURE`); manual `/scs` requires ≥70% (`SCS_MANUAL_MIN_PRESSURE`) or explicit `force` keyword.
- **Receipt:** `docs/receipts/2026-06-17-scs-trigger-discipline-v0.md`
- **Tests:** wider SCS suite 86/86 pass after patch.

### pi-sister-spawn.mjs — `--triad` Requires `--require-parent` + Registered Parent Session (2026-06-17)
- **Issue:** Using `--triad` without `--require-parent` exits 1 immediately with `[pi-sister-spawn] --triad requires --require-parent`. Even with both flags, the parent session must be registered in the lane registry or validation fails.
- **Symptom:** exit_code 1, stderr `[pi-sister-spawn] --triad requires --require-parent`, stdout_bytes 0, duration ~30ms.
- **Fix:** Always pair `--triad` with `--require-parent --parent-session-id sess_<lane>_<id>` after registering via `mcp_omnios_session_registry_register`. Sequence: register lane → capture session_id → spawn with `--triad --require-parent --parent-session-id <id> --nonce <id> --claim-ceiling <level>`.

### pi-sister-spawn.mjs — `--thinking` Valid Values (2026-06-17)
- **Issue:** `--thinking med` is invalid and silently ignored — pi falls back to default `xhigh`, which can cause timeouts on dense analytical tasks.
- **Valid values:** `off`, `minimal`, `low`, `medium`, `high`, `xhigh`. Use the full word `medium`, never `med`.
- **Symptom:** Warning `Invalid thinking level "med". Valid values: off, minimal, low, medium, high, xhigh` in stderr; spawn then runs at xhigh and may hit timeout.
- **Fix:** Use `--thinking medium` or `--thinking high` for dense analytical tasks; reserve `xhigh` for short focused prompts.

### Nemotron Ultra (NIM) Timeouts on Dense Tasks (2026-06-17)
- **Issue:** `nim/nvidia/nemotron-3-ultra-550b-a55b` with `--thinking xhigh` consistently times out at 300s on dense architecture/analysis prompts. Observed 3 consecutive timeouts (300s each, 0 stdout bytes) before switching approach.
- **Symptom:** exit_code 124, duration_ms ~300000, stdout_bytes 0, stderr only the standard pi warnings.
- **Workaround:** For Nemotron on dense tasks use `--thinking medium` or `--thinking high` and `--timeout 600+`. If still timing out, fall back to OMNIRA self-debate (in-session synthesis) — Kyle accepts this when labeled `"self-debate (spawn failed)"` per the manual.

### DeepSeek API Balance Exhaustion — Fallback to Kimi K2.6 (2026-06-17)
- **Issue:** `deepseek-api/deepseek-v4-pro` (and `deepseek-api/deepseek-chat`) can hit `402 Insufficient Balance` mid-session with no warning. Credits deplete and the route dies.
- **Symptom:** exit_code 1, stderr includes `402 Insufficient Balance`, stdout_bytes 0, duration ~1.5s.
- **Fix:** Route adversary/analysis tasks to `ollama-cloud/kimi-k2.6` as fallback — model-different from Nemotron and GLM, frontier-class, and confirmed working. Other working routes (verify with `pi list` and ping test): `ollama-cloud/deepseek-v4-pro`, `ollama-cloud/glm-5.1`, `ollama-cloud/glm-5.2`, `nim/nvidia/nemotron-3-ultra-550b-a55b`, `github-copilot/gpt-5-mini`.

### Anthropic Opus Extra Usage Cap (2026-06-17)
- **Issue:** `anthropic/claude-opus-4-6` returns `400 {"error":{"type":"invalid_request_error","message":"You're out of extra usage. Add more at claude.ai/settings/usage and keep going."}}` when the extra-usage tier is exhausted. Different from 429 rate-limit — it's a hard cap.
- **Fix:** Switch to a different provider for triad/council work. `github-copilot/gpt-5-mini` works for lightweight triad slots; `openai-codex/gpt-5.5` for heavier analysis. Don't retry Opus — the cap doesn't reset mid-session.

---

## Key receipts (read before acting)

- `docs/receipts/2026-06-09-aoms-eq-trinity-debate-synthesis.md`
- `docs/receipts/2026-06-09-aoms-hermes-merge-review-sync.md`
- `docs/receipts/2026-06-09-aoms-hermes-tranche2-export.md`
- `.omni/plan/kyle-hermes-memory-pending.json` → `harvest_prep_complete`
- `.omni/plan/kyle-training-gate-pending.json` → training blocked

---

## Law hierarchy (quick)

1. `OMNIRA-ORGANISM-CONSTITUTION.md`
2. `OMNIRA-LAWS.md`
3. `OMNIOS-LAWS.md`
4. Skills/receipts (operational, yield to above)

Membrane violations = OMNIOS write gate, not constitutional violation — fix with probe+receipt.
