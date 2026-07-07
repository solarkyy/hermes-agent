# Phase A Execution Pattern — Metabolic Cycle

*Learned 2026-06-09: The first full metabolic cycle of the OMNIRA organism.*

## When to Use

After deep research produces brain files and an implementation plan. Phase A is always **plumbing and honesty** before architecture. The pattern is reusable for any "clean up the organism" cycle.

## The 6 Steps

### A1: Dirty-State Receipt
**Before touching anything**, capture what's dirty:
```bash
mkdir -p .omni/receipts/git
git status --short > .omni/receipts/git/status-pre-phase-a.txt
git diff > .omni/receipts/git/diff-pre-phase-a.patch
```
This is the organism's "before photo." Never skip it.

### A2: Audit Known Bugs
Check if reported bugs actually exist on disk vs just in running processes:
- Read the source code directly
- Don't trust "the bug exists" claims without line numbers
- The MCP update_cell lifecycle bug was already fixed on disk (lines 384-392 handle both array and object) but the running server process (from Jun 5) still had old code
- **Lesson:** Bug on disk ≠ bug in running process. Always check both.

### A3: Refresh Stale Cells
Cells in `you/{agent}/{AGENT}.mind.json` go stale when `vitals.lastComputedAt` is old.
- Use `execute_code` to batch-read/write JSON (not MCP update_cell, which may hit stale server)
- Add a lifecycle event: `{type: "phase_a3_refresh", at: ISO_DATE, by: "weight-hermes"}`
- Check all cells, not just the ones you think are stale

### A4: Metabolize Council Log
The council log is entropy. Classify it:
- **heartbeat**: pulse/tick/alive lines (waste — volume, not signal)
- **decision**: decided/approved/verdict lines (compost — extract lesson)
- **reach**: connect/contact/grip lines (seed — may need follow-up)
- **signal**: eq/trinity/valence lines (compost — extract pattern)
- **noise**: unparseable lines (waste)

Pipeline: archive raw → classify → extract gradients → write summary → write receipt → truncate active log.

### A5: Compost Old Code
Read the files that were patched. Check for dead code, abandoned constants, unreachable logic.
- If clean: write a receipt saying so (don't delete what isn't dead)
- If dead code found: extract the lesson, write compost receipt, remove dead code
- Receipt format: `.omni/compost/code/{component}-{date}.md`

### A6: Test Connectivity
Verify the organism can still communicate:
- Post to council (test `mcp_omnios_council_post`)
- Check CDP lanes if relevant
- Verify cron jobs are running

## Receipts Produced

| Receipt | Path | Purpose |
|---------|------|---------|
| Dirty-state status | `.omni/receipts/git/status-pre-phase-a.txt` | Before photo |
| Dirty-state diff | `.omni/receipts/git/diff-pre-phase-a.patch` | Full diff |
| Entropy receipt | `.omni/receipts/entropy/council-{date}.json` | Council log metabolism |
| Compost summary | `.omni/compost/council/{date}-summary.md` | What was composted |
| Code compost | `.omni/compost/code/{component}-{date}.md` | Dead code audit |
| Raw archive | `.omni/archive/council/{YYYY}/{MM}/council-{date}.raw.log` | Full archive |

## Key Lesson

The update_cell bug taught a critical lesson: **the code on disk and the running process can diverge.** Long-lived MCP server processes (Node.js) cache the code at startup. If you fix a bug on disk, the running process still has the old code. Workaround: use `execute_code` for batch operations, don't rely on MCP tools for state that may be served by a stale process.

## Follow-Up

After Phase A completes, post to council with all receipts. Then proceed to Phase B (foundation: constants, entropy metabolism, staged measurement).
