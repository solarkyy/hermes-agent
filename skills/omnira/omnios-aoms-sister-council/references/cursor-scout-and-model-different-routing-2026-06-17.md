# Cursor Scouts + Model-Different Routing (2026-06-17)

Two reusable techniques from a model-different sister council reviewing HRO doctrine gates.

## 1. Model-different sisters to close the same-model I3 open loop

When a prior review used a single model family (e.g. all gpt-5.5), re-review with
**different model families** so cross-family agreement is real Independence-Score (I3)
signal, not correlated theater. Validated lens trio:

- Architect → `nim/nvidia/nemotron-3-ultra-550b-a55b` (NIM)
- Adversary/Falsifier → `deepseek-api/deepseek-v4-pro`
- Membrane/Risk → `ollama-cloud/glm-5.1`

All three returning the same verdict (e.g. WATCH) across families is the point — it is
the evidence that the agreement is not a monoculture artifact.

## 2. Pi provider-prefix routing (the silent ~500ms exit-1 failure)

`pi-sister-spawn.mjs` exits in ~500ms with `exit_code=1`, `stdout_bytes=0`, and a short
stderr `No API key found for <provider>` when the **bare provider prefix** has no key in
Pi's `~/.pi/agent/models.json`. The model string is provider-scoped and must match a
provider that actually has a key.

WRONG (no key for bare provider → instant fail):
- `zai/glm-5.1`
- `deepseek/deepseek-v4-pro`

RIGHT (provider with a key, per models.json `providers` map):
- `ollama-cloud/glm-5.1`  (also `ollama-cloud/glm-5.2`, `kimi-k2.6`, `minimax-m3`, `deepseek-v4-pro`)
- `deepseek-api/deepseek-v4-pro`  (also `deepseek-v4-flash`)
- `nim/nvidia/nemotron-3-ultra-550b-a55b`  (NIM Nemotron)
- `codex/gpt-5.5` (NOT `openai-codex/...` if `openai-codex` shows `has_key=False`)

Diagnose available routes before spawning:
```bash
cat ~/.pi/agent/models.json | python3 -c "
import json,sys; d=json.load(sys.stdin); provs=d.get('providers',{})
for k,v in provs.items():
    has=bool(v.get('apiKey') or v.get('api_key') or v.get('env') or v.get('authToken'))
    print(k, 'has_key='+str(has), [m.get('id') for m in v.get('models',[])][:8])
"
```
The first spawn failure is cheap and recoverable — read stderr, fix the prefix, respawn
with a fresh nonce (`...-r2-...`). Record the reroute honestly in council rather than
hiding it.

## 3. Cursor scout orchestration from the Voice surface (read-only)

Cursor CLI at `/home/kylej/.local/bin/agent` (symlink into `~/.local/share/cursor-agent/`).
Verify auth: `agent status` → `Logged in as <email>`. List models: `agent --list-models`
(includes Opus 4.8 1M, GPT-5.5 1M, Codex-Max line — genuinely model-different from Pi's
Nemotron/DeepSeek/GLM, so a Cursor scout is a real 4th independent eye for I3).

A Cursor scout READS THE ACTUAL REPO (filesystem traversal), unlike `--no-tools` Pi
sisters that reason from the prompt only. It can therefore catch on-disk facts the
summaries miss (e.g. "the graph artifact was not edited; corrections live only in the
receipt, so adopted-model and on-disk file are intentionally out of sync").

### Working headless invocation (validated)
```bash
agent --print --output-format text --trust --model auto '<PROMPT AS POSITIONAL ARG>' \
  > out.txt 2>err.txt
```
- `--print` = headless/script mode (has all tools incl. write+shell — so constrain via prompt + monitoring).
- `--trust` = required for headless (skips workspace-trust prompt).
- `--model auto` = the reliable route. Explicit named models (`gpt-5.5-high`, etc.) hit
  `resource_exhausted` / usage limits — confirmed again this session; use auto.

### PITFALL — `--mode plan` silently breaks headless stdout
`--mode plan` (read-only/planning) produces **empty 1-byte output with exit_code=0** in
`--print` headless mode. Three attempts wasted before isolating it. Do NOT use `--mode plan`
for headless scouting. Instead drop `--mode plan` and enforce read-only via an explicit
prompt instruction ("READ-ONLY AUDIT. Do not edit, write, create, or run any mutating
command — read files and reason only.") plus your own monitoring. A short positional-arg
prompt with file reads works fine without plan mode.

### PITFALL — prompt delivery
- Pass the prompt as a **single-quoted positional argument**. Piping via stdin
  (`cat prompt.md | agent --print ...`) yields empty output.
- Very long multi-line prompts via shell `$(cat ...)` expansion can also come back empty;
  keep the scout prompt compact and inline.

### Safety doctrine (from Cursor-arms deep, carry forward)
- Read-only scouting is production-ready now: prompt-enforced read-only + monitoring.
- Isolated writing is one rung away: use `-w/--worktree` (creates
  `~/.cursor/worktrees/<repo>/<name>` off any base branch) so a writing sister never
  touches the dirty working tree. Still requires Kyle's gate.
- NEVER `--force`/`--yolo` (run-everything) on a live repo workspace for automated Cursor.
  That stays gated behind `BUILD CURSOR ARMS DOCTRINE AND DISPATCH VERIFIER V0`.
- Cursor writes no Pi-style spawn-metadata receipt by default — capture stdout/exit/timing
  yourself and wrap in a receipt, or the output stays ephemeral L1.

## 4. Membrane discipline reminder (recurred all session)
Every `write_file` and every state-affecting `terminal`/spawn command hits the OMNIRA
membrane and is BLOCKED unless preceded by an `is_state_probe=true` read-only probe whose
output is passed as `justification_receipt`. This fires even on `mkdir`-then-write and on
`pi-sister-spawn`/`agent` launches. Probe first (ls the target, check no collision, verify
binary/auth), then act with the probe output as the receipt.

## 5. Gate-review council pattern (HRO doctrine adoption)
When Kyle is deciding whether to ratify a governance/doctrine gate, run a 3-lens
model-different council (architect / adversary-falsifier / membrane-risk) BEFORE he
approves. Watch for the correlated-approval anti-pattern: multiple human yes-votes in one
short session on the same P0-P1 AI-self-attested evidence base is exactly what I3 exists to
detect. The right move is usually: ratify the cheapest gate with an explicit
"provisional + revocable, does not pre-authorize downstream gates" reservation, and DEFER
the next gate to a fresh session to restore an independence cycle. Record deferral as a
first-class outcome in the receipt, not a non-action.
