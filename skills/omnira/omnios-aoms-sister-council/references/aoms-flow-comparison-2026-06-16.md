# AOMS Flow Comparison (2026-06-16)

**Why:** User asked to compare "aoms" routing behavior to decide which flow works best.

## Run Summary
- Task: compare MCP-based vs PI-based sister spawning for a short 5-field JSON decision memo.
- AOMS task file: `/tmp/aoms_flow_task.md`
- Claim ceiling: `L1 advisory: compare mcp flow vs pi flow`

## Evidence
1. **`mcp_omnios_omnira_spawn` attempt**
- mode: `council`
- model/provider: `dashscope/qwen-plus-latest`
- result: hard timeout after **30s** (tool-level ceiling), no output payload.

2. **`pi-sister-spawn` (advisor run, `openai-codex/gpt-5.5`)**
- output file: `.omni/sister-spawn/2026-06-16T15-57-03-040Z-sister-c3bcb0a0/stdout.log`
- result: successful L1 advisory JSON

3. **`pi-sister-spawn` (advisor run, tools enabled, same prompt)**
- output file: `.omni/sister-spawn/2026-06-16T15-57-32-254Z-sister-feb46291/stdout.log`
- result: successful L1 advisory JSON

## Conclusion
- For this task and generally for AOMS orchestration above 20–25 seconds, prefer **PI flow** for reliability and full metadata in `spawn` outputs.
- MCP spawn can still be used for **tiny** quick-turning prompts where the expected runtime is comfortably below the 30s hard ceiling.

## Concrete Selection Rule
- Use **MCP first** only for rapid single-sister ideation where latency is the only concern and traceability is less important.
- Use **PI for implementation, comparison experiments, and anything that matters operationally**.
- If MCP is used, treat it as a non-normative shortcut and immediately follow with PI if output is incomplete or timed out.
