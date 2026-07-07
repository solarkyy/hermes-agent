# Implementation Sisters — AOMS for Concrete Build Work

*Learned 2026-06-09: Kyle directed AOMS sisters to work on Phase A implementation — plumbing, bug fixes, script building. Sisters audit and advise; orchestrator does the actual code changes.*

## When to Use

Kyle says "have pi sisters aoms work with you. you orchestrate they debate collaborate and work." This is NOT strategic analysis (that's the standard AOMS council). This is NOT philosophical exploration (that's deep conversational research). This is **concrete implementation work** where sisters provide specialized analysis and the orchestrator builds.

## How It Differs from Other AOMS Patterns

| Standard AOMS | Deep Conversational | Implementation Sisters | **Builder Sisters** |
|---------------|--------------------|-----------------------|---------------------|
| Strategic analysis | Philosophical exploration | Code audit + proposals | **Sisters write code** |
| Structured JSON output | Free-form insight | Code audit + proposals | **Working .mjs files** |
| Synthesis sister combines | Kyle synthesizes | Orchestrator builds | **Sisters build directly** |
| Goal: unified plan | Goal: vocabulary/frameworks | Goal: working code | **Goal: modules in src/** |
| 3-5 sisters | 5-10+ sisters | 1-3 per task | **1-2 per module** |
| One round | Multiple rounds | Sequential per step | **Parallel spawn** |
| `--no-tools` | `--no-tools` | Mixed | **omit `--no-tools`** |

### Builder Sisters (2026-06-09 — NEW PATTERN)

When Kyle said "you are having your sisters do the work right," he pointed out that `--no-tools` sisters can't actually build anything. The fix: **omit `--no-tools`** so sisters get the full Pi tool surface (read, bash, edit, write). Sisters can then write actual working modules to disk.

**Proof:** Phase B sisters produced:
- B2 (Claude Sonnet): wrote `src/aoms/entropy-metabolism.mjs` (779 lines, 35,876 chars) directly to disk with 5 passing test cases. Never touched stdout — all work was file writes.
- B1 (GPT-5.5): designed `src/aoms/cosmological-constants.mjs` (12,969 chars) in stdout with embedded code blocks. Orchestrator extracted and wrote the file.
- B3 (GPT-5.5): designed `src/aoms/staged-measurement.mjs` in stdout with fragmentary code blocks. Orchestrator assembled and wrote the file.

**Key difference:** Claude Sonnet writes to disk. GPT-5.5 tends to output designs in stdout. Both work — the orchestrator just needs to check which pattern was used.

**Spawn command for builder sisters:**
```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
node tools/pi-sister-spawn.mjs \
  --worker-model anthropic/claude-sonnet-4 \
  --task-file /tmp/sister-b2-entropy.md \
  --lane build \
  --nonce b2-entropy-002 \
  --claim-ceiling "write src/aoms/entropy-metabolism.mjs and tests/aoms/test-entropy-metabolism.mjs" \
  --timeout 300 \
  --thinking xhigh
```

Note: **no `--no-tools`**. The `--claim-ceiling` explicitly names the files she can write. The `--timeout 300` gives enough time for file writes + test runs.

**Model choice for builders:**
| Model | Writes to disk? | Speed | Quality |
|-------|----------------|-------|---------|
| Claude Sonnet | ✅ Yes, directly | 3-5 min | High — complete modules with tests |
| GPT-5.5 | ⚠️ Stdout with code blocks | 2-3 min | High — needs extraction |
| Claude Opus | ❌ Timed out at 300s | N/A | Too slow for complex modules |

**Timeout guidance:**
- Simple module (<200 lines): 180s is enough
- Medium module (200-500 lines): 300s
- Complex module (500+ lines): 300s may not be enough — split the task or write directly
- Phase C (heart-weighting, shadow-firewall): both sisters timed out at 300s. Orchestrator wrote these directly from research findings.

**Post-write verification:** Always check if the sister wrote to disk or stdout:
```bash
# Check if file exists
ls -la src/aoms/<module>.mjs
# If not found, check stdout for code blocks
head -30 .omni/sister-spawn/<timestamp>-sister-<id>/stdout.log
```

## Sister Roles

### Code Scout
- Audits the actual codebase to confirm bugs, find exact lines, understand current behavior
- Produces: `BUG CONFIRMED: YES/NO`, file path, line number, current code, proposed fix, test cases
- **Tools decision:** See "Orchestrator-Led Audit" below. If spawned with `--no-tools`, paste the relevant code into the task file. If spawned with `--tools`, she reads files directly but takes 2-5min.

### Research Mapper
- Maps schemas, data structures, file relationships, timestamps
- Produces: existing items, stale items, missing items, proposed schema, refresh logic
- Tools: `--no-tools` if schema is provided in prompt; `--tools` if she needs to read files

### Red Team
- Identifies risks, false-self patterns, premature-scoring dangers, data-loss risks
- Produces: dead code audit, risk assessment, compost plan
- Tools: `--tools` enabled (needs to read code)

## The Orchestration Pattern

```
1. Orchestrator does A1 (receipts, state probes) — no sisters needed
2. For A2 (bug fix): spawn Code Scout → read her report → apply fix directly
3. For A3 (schema work): spawn Research Mapper → use her schema → build script
4. For A4 (metabolism): spawn Code Scout → use her design → build script
5. For A5 (composting): spawn Red Team → use her audit → write receipt
6. Post to council after each step
```

Key: **the orchestrator builds, sisters advise.** Don't wait for sisters to finish everything before starting work. Spawn a sister, do other work while she runs, read her output, incorporate it.

## Task File Template (Implementation)

```markdown
# AOMS Sister: [Role] — [Task]

You are the [Role] for Phase [X]. Your job: [one-sentence objective].

## Context
[What was already done, what the bug/issue is, what files are involved]

## Your Task
1. Read [specific files]
2. Confirm/identify [specific thing]
3. Propose [specific output format]

## Output Format
BUG CONFIRMED: [YES/NO]
FILE: [path]
LINE: [line number]
CURRENT CODE: [the broken code]
PROPOSED FIX: [the fixed code]
TEST CASES: [list of test scenarios]

Do NOT modify any files. Just report.
```

## Spawn Command

```bash
node tools/pi-sister-spawn.mjs \
  --worker-model openai-codex/gpt-5.5 \
  --task-file /tmp/sister-a2-scout.md \
  --lane build \
  --nonce a2-scout \
  --claim-ceiling "code scout only, no file modifications" \
  --timeout 240 \
  --thinking xhigh
```

**Lane:** Use `build` (not `coord`) for implementation work.
**Claim ceiling:** Always include "no file modifications" — sisters audit, orchestrator builds.
**Timeout:** 240s for code scouts (they read files). 300s for research mappers (they analyze schemas).

## Concrete Examples

### Phase A: Plumbing + Honesty (2026-06-09 — orchestrator-led)

This session used the **orchestrator-led** pattern because `--no-tools` sisters couldn't read files. The orchestrator did the audits directly and used sisters for strategic thinking only.

**A1: Dirty-state receipt** — orchestrator ran `git status --short` and `git diff` directly. No sister needed.

**A2: update_cell lifecycle bug** — Code Scout spawned with `--no-tools`, reported "I cannot inspect files." Orchestrator ran `search_files` to find `.push()` calls, read the handler at lines 373-405, discovered the bug was already fixed on disk (both array and object lifecycle handled). The real bug: running MCP server processes (from Jun 5) hadn't picked up the fix. Workaround: `execute_code` to read/write JSON directly.

**A3: Stale cells** — orchestrator checked all 18 cells via `execute_code` Python script. Found 15 stale (only edge, cursor, omnira-hermes were fresh). Refreshed all 12 key cells via direct JSON read/write. No sister needed.

**A4: Council log metabolism** — orchestrator checked log size (500 lines, 259KB — not 7,925 as expected). Classified via Python, archived raw, extracted gradients, composted noise, truncated to 200 lines. All via `execute_code`. No sister needed.

**A5: EQ code compost** — orchestrator read `tools/omnira-eq-updater.mjs` (241 lines), found no dead code (Phase A patches already landed). Wrote compost receipt noting "clean."

**A6: Council visibility** — tested `mcp_omnios_council_post`, confirmed working.

**Key lesson:** For simple plumbing tasks (A1-A6), the orchestrator can work faster than spawning sisters. Sisters are most valuable for architectural decisions (Phase B-D), not for reading files and checking if bugs exist. Save sisters for the thinking work.

### Phase A: Strategic Research (2026-06-09 — sister-heavy)

The SAME SESSION also used 8+ sisters for deep philosophical research (ego, universe, death, entropy). Those sisters were spawned with `--no-tools` for pure reasoning. Kyle directed: "keep going with aoms sisters go deep." This is the **deep conversational research** pattern, not the implementation pattern.

**Key lesson:** One session can use BOTH patterns. Use sisters for thinking, do the plumbing yourself. Don't try to make sisters do simple file reads.

### Historical: A2 Update Cell Lifecycle Bug (earlier attempt)

Earlier in the session, a Code Scout was spawned with `--no-tools` to audit the bug. She reported: "I'm operating without any tools — I cannot inspect the files." This led to the orchestrator-led pattern above.

## Scripts That Emerged

These scripts were built during implementation and are now part of the organism:

### `scripts/metabolize-council-log.mjs`
Entropy metabolism for the council log. Pipeline: archive → classify → extract → compost → truncate.
```bash
node scripts/metabolize-council-log.mjs --dry-run  # preview
node scripts/metabolize-council-log.mjs             # execute
```

### `scripts/refresh-cell.mjs`
Cell lifecycle management. Creates, refreshes, and converts mind cells.
```bash
node scripts/refresh-cell.mjs --all                 # refresh all
node scripts/refresh-cell.mjs --cells weight,spark  # specific cells
node scripts/refresh-cell.mjs --create weight,spark # create new
node scripts/refresh-cell.mjs --check               # stale check (read-only)
```

## Pitfalls

- **Pi CLI PATH collision.** `/usr/bin/pi` is a calculator. The real Pi CLI is at `/home/kylej/.npm-global/bin/pi`. Always `export PATH="/home/kylej/.npm-global/bin:$PATH"` before spawning. This affects background processes too — `terminal(background=true)` strips PATH.
- **`--no-tools` sisters can't read files.** If you spawn with `--no-tools`, paste the relevant code sections into the task file. The sister will report "I cannot inspect the files" otherwise. Rule of thumb: Code Scout = paste code into task (orchestrator-led), Research Mapper = tools-enabled (needs web), Red Team = no-tools (pure reasoning about risks).
- **MCP server stale processes.** The running MCP server may not reflect disk fixes. `ps aux | grep omnios-mcp-server` — if oldest process predates your fix, MCP tools will still fail. Workaround: use `execute_code` to read/write JSON directly.
- **Sisters time out on code-heavy tasks.** Code Scouts reading large files may hit 240s. Use `--timeout 300` for complex audits.
- **Don't wait for all sisters before starting work.** Spawn a sister, do other work, read her output when she's done. The orchestrator can complete A1 (receipts) and A3 (cell refreshes) while sisters analyze A2/A4/A5.
- **Red Team sisters are optional.** If the code is simple, the orchestrator can audit directly. Red Teams are for complex risk assessment.
- **Always dry-run metabolism scripts first.** `--dry-run` shows what would happen without touching files.
- **Membrane requires justification_receipt.** Before any `patch` or `write_file`, do a read-only probe first and pass the output as `justification_receipt`.
