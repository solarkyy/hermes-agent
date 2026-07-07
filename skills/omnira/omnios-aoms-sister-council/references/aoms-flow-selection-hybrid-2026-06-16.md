# AOMS Flow Selection: Hybrid MCP+PI SOP (2026-06-16)

Date: 2026-06-16
Scope: class-level policy for non-trivial AOMS routing and evidence collection.

## Decision rule
Use a **hybrid AOMS flow** as default:

- MCP-first for fast strategy/debate when output can plausibly return under ~20-25s.
- PI sisters for implementation, verification, comparison, and artifact-heavy decisions.
- MCP-only only for small, low-latency coordination questions with no durable artifact requirement.

## Trigger conditions
Create/update a session-specific runbook whenever a workflow includes:

1. model/route comparison across MCP vs PI
2. implementation-impacting AOMS recommendations
3. reproducibility claims (timeouts, retries, reroutes, scoring)

## Canonical artifact workflow

1. Keep task artifacts under: `/tmp/aoms-research-run/<run>/`.
2. Persist per-run outputs:
   - `/tmp/aoms-research-run/strategy/stdout.log`
   - `/tmp/aoms-research-run/impl/stdout.log`
   - `/tmp/aoms-research-run/research/stdout.log` (plus `stderr.log`)
   - `/tmp/aoms-research-run/synthesis/stdout.log`
3. If MCP spawns timeout or route fails, explicitly rerun PI with valid provider/model IDs.
4. Record routing outcome and final winner in a dated docs/ops runbook (example below).

## Required runbook shape (class-level)

Create/update a dated runbook in:

- `docs/ops/GOAL-AOMS-FLOW-SELECTOR-HYBRID-YYYY-MM-DD.md`

Required sections:
- Decision short form
- Why this flow was chosen
- Lane split by lens (Strategy / Implementation / Research / Synthesis)
- Timeout/routing failure policy
- Evidence trail (artifact paths)
- Gate criteria for MCP-vs-PI fallback

## Practical routing notes

- `mcp_omnios_omnira_spawn` currently hard-stops around 30s in this surface.
- PI runbook for implementation should include explicit `--claim-ceiling` scopes and `--no-tools`/`--lane` choice.
- Provider mismatch failures are logged in stderr; keep stderr with stdout as evidence for retries.

## Example command pattern

- `node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.5 --lane coord --task-file <task>.md --claim-ceiling "..." --no-tools --timeout 180`
- `node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.3 --lane build --task-file <task>.md --claim-ceiling "..." --no-tools --timeout 180`
- `node tools/pi-sister-spawn.mjs --worker-model openai-codex/gpt-5.5 --lane coord --task-file <synthesis-task>.md --claim-ceiling "..." --timeout 220`

## Evidence-backed closure requirement

Before claiming a flow decision final, verify the runbook references:
- concrete artifacts exist and were read
- timeout/fallback behavior is logged
- final recommendation is explicit (`hybrid`, `mcp-first`, or `pi-first`)