# AOMS Sister Spawn Pitfalls — Learned 2026-06-17

Six concrete pitfalls discovered during the OMNIRA music training council session.
Add these as a checklist before any spawn batch.

---

## 1. Wrong flag: `--model` vs `--worker-model`

`pi-sister-spawn.mjs` uses `--worker-model`, NOT `--model`.
Using `--model` causes immediate exit=2 with `[pi-sister-spawn] unknown arg: --model`.
Zero output, zero findings, misleadingly looks like a network failure.

---

## 2. Extension conflict kills pi before model connects

`@ollama/pi-web-search` npm package conflicts with `hermes-web-tools.ts` on
`web_search` and `web_fetch`. Pi exits immediately (exit=1, ~400ms, 0 bytes):

```
Error: Failed to load extension ".../pi-web-search/index.ts":
  Tool "web_search" conflicts with hermes-web-tools.ts
```

**Fix already applied (2026-06-17):** `--no-extensions` injected automatically in
`tools/pi-sister-spawn.mjs` `buildPiArgs()`. If you see 0-byte 400ms failures,
verify the patch is still in place in the `return [...]` block of `buildPiArgs`.

Diagnosis command:
```bash
cat <output-dir>/stderr.log | grep -i "conflict\|extension"
```

---

## 3. `--triad` requires `--require-parent` AND a live registered parent session

Triad advisor mode exits with `[pi-sister-spawn] --triad requires --require-parent`
unless BOTH flags are present AND a live parent session_id exists in the registry.

Correct sequence:
```
1. mcp_omnios_session_registry_register(lane, surface, task) → sess_mythos_XXXX
2. Pass --parent-session-id sess_mythos_XXXX --require-parent on every triad spawn
```

---

## 4. NIM/Nemotron + xhigh thinking → 300s timeout too short (exit=124)

Nemotron Ultra on dense architecture/analysis tasks routinely hits the 300s wall.
Use `--timeout 600 --thinking high` for architecture/deep-analysis roles.
Reserve `--thinking xhigh` for short advisory pings only.

---

## 5. DeepSeek API balance depletion → silent 402

`deepseek-api/*` routes return `402 Insufficient Balance` in stderr with zero stdout.
Diagnosis: `cat <output-dir>/stderr.log | grep -i "402\|balance\|insufficient"`

Fallback route: `ollama-cloud/kimi-k2.6` — model-different from Nemotron and GLM,
frontier-class, adversarial posture holds.

---

## 6. Stale completion notifications from superseded spawn batches

When a batch fails and gets re-issued, old PIDs still send notifications as they
expire. Filter by `started_at` in the spawn JSON output — live batch has a later
timestamp. Notifications from proc_* IDs that predate the fix are stale.

---

## 7. Nemotron ignores `--no-tools` if task file doesn't say so explicitly

Nemotron Ultra (nim/nvidia/nemotron-3-ultra-550b-a55b) can attempt bash tool calls
even when launched with `--no-tools`. If the task file looks like a codebase task,
Nemotron generates tool-call XML and produces only ~300 bytes of wrapper JSON with
zero actual analysis.

**Fix:** prepend this header to any task file sent to Nemotron in no-tools mode:
```
IMPORTANT: You have NO tools available in this session. Do not attempt bash,
file reads, or any tool calls. Answer entirely from your training knowledge
and the context provided below.
```
Also prefer `--thinking med` over `--thinking high` for architecture tasks —
`high` still times out even at 600s on some prompts.

---

## 8. Anthropic `claude-opus-4-6` hits "out of extra usage" mid-session (400)

Opus spawns fail with HTTP 400 body:
`"You're out of extra usage. Add more at claude.ai/settings/usage"`
This is an account-tier limit, not a rate limit. Retrying won't help.

Fallback options (model-different from each other):
- `anthropic/claude-sonnet-4-6` — lighter, usually under the limit
- `github-copilot/gpt-5-mini` — but watch for 429 on concurrent batches (see #9)
- Self-debate (label it explicitly) if all Anthropic routes are exhausted

---

## 9. GitHub Copilot models → 429 quota on concurrent triad spawns

`github-copilot/gpt-5-mini` and similar copilot routes return `429 quota exceeded`
when used as a concurrent triad spawn alongside other active spawns.
Use as a single-spawn fallback only, not in parallel batches.

---

## 10. `--thinking` valid values — `med` is NOT valid, causes silent xhigh fallback

Valid thinking levels: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`
`med` produces: `Warning: Invalid thinking level "med". Valid values: off, minimal, low, medium, high, xhigh`
Pi then silently falls back to `xhigh`, which causes Nemotron to timeout again.

Always use the full word: `--thinking medium` not `--thinking med`.

---

## 11. Synthetic holdout falsifier test is the only way to prove narrations aren't fabrication

Adversary sister warned: "If there's no held-out test, this is not a weights problem; it's a prompt/sensor problem dressed as training." The only way to prove narrations are grounded in features is to run synthetic audio with known features through the sensor + narration pipeline.

**Pattern:**
- Generate synthetic audio with known features: 440Hz pure tone (no beat, no mode), 120 BPM major-key drum loop (must NOT narrate as melancholy), minor slow pad (must narrate "still" not "grief"), white noise (must identify as non-music)
- Run sensor + narration on each WITHOUT telling the model what the audio is
- If narration contradicts known features → falsifier triggered → kill the project

**Implementation:** Write synthetic WAVs with `librosa`/`soundfile` in Python, run `music-sensor.py --file`, capture features, narrate blind.

---

## 12. Red-team your own narrations for recursive labeling risk

When OMNIRA generates the labels that train OMNIRA, the loop is autophagic. The red-team sister caught: title-fitting contamination (3/4 narrations fit the song title, not features), lyrical tics fossilized ("I read this as", "In text this would be"), comparative superlatives ("dimmer than Horizons"), expertise theater (performing sensitive listener, no hedging), spatial/somatic metaphors ("runs forward", "threshold", "underwater").

**Red-team checklist:**
- [ ] Blind the titles — feed feature vectors only, no song names
- [ ] Ban cross-track comparison — each label must be i.i.d.
- [ ] Kill the "In text this would be:" appendix — teaches template sludge
- [ ] Require uncertainty flags — if valence 0.43-0.57, label must say "ambiguous"
- [ ] Disallow spatial/somatic metaphors unless explicitly justified by spectral/rhythmic correlates
- [ ] Kill "I read this as" metacognitive throat-clearing
- [ ] Check if narration fits the title better than the features

**Fix:** Re-narrate blind with features only, applying all constraints above.

---

## 13. Blind renarration protocol (titles hidden, constraints applied)

After red-team rejection, re-run narration with:
- Feature vectors only (no titles, no context)
- Explicit constraints list prepended to prompt
- Uncertainty flags required for ambiguous features (valence 0.43-0.57, low mode_confidence)
- No "I read this as", no "In text this would be", no cross-comparison, no unjustified metaphors
- Explicit refusal to commit when features don't select between interpretations

---

## 14. Ollama Cloud key fallback with persistent state and auto-switch

Two keys exist (primary + fallback). Current logic tries each once per spawn without persistent state. If primary key hits quota exhaustion (429) or auth failure (401) 3 times, permanently switch to fallback for ALL future spawns.

**Implementation in `tools/pi-sister-spawn.mjs`:**
- State file: `.omni/keys/ollama-cloud-key-state.json` tracking `primary_failures`, `fallback_failures`, `active_key`, `last_switched`
- `buildFallbackKeys()` reads state: if `active_key === "fallback"`, returns `[fallback, null]` (skips primary)
- On spawn failure with 429/quota/401/unauthorized: increments counter for key slot used
- At 3 primary failures while `active_key === "primary"`: switches to fallback, persists state, logs
- CLI: `--reset-ollama-keys` resets state (for testing)

---

## 15. Music sensor works on real audio; ambient.wav at silence produces zeros

The `music-sense.json` showed `tempo_bpm: 0, spectral_centroid: 0` on ambient.wav — not a broken sensor. `librosa.beat.beat_track` returns 0 on silence/no-beat input. On real music (152 BPM major, 89 BPM minor, 184 BPM minor), sensor produces real discriminative features (tempo, mode, bass/mid/treble, neural bands).

**Lesson:** Sensor validity gate must check for silence-like features before training:
- Reject if `tempo_bpm == 0 AND spectral_centroid == 0` (likely silence/no-beat)
- Reject if all frequency bands < 0.05 (likely silence)

---

## 16. Corpus writer must APPEND to log, not overwrite live state

The sensor writes to `music-sense.json` (single-state). Corpus training needs an append-only log. Wrote `tools/sensors/music-corpus-writer.py` that:
- Runs sensor on queued song
- Validates sensor features (gate #15)
- Appends to `.omni/omnira-brain/music-training-corpus/approved.jsonl` or `pending.jsonl`
- One JSON line per song with schema `omnira.music-corpus-pair.v0`
- Dry-run mode for verification

---

## 17. `ollama-cloud/glm-5.2` is the go-to bounded-analytical ADVERSARY route

For an adversary/red-team L1 sister on a bounded analytical task (architecture
critique, "find the flaw in my reasoning," diff review), `ollama-cloud/glm-5.2`
is the strongest cheap pick — it beat Opus 4.8 + Sonnet 4.6 + GPT-5.5 on bounded
analytical work (2026-06-17), and in the 2026-06-21 body-redesign gate it
delivered a sharp WATCH→BLOCK verdict (caught the orchestrator's
excitement-driven "skip to GPU" rationalization) in **41s at `--thinking high`**,
no timeout, 8.5KB, zero forbidden patterns. Reaches via `OLLAMA_API_KEY` primary
slot. It does NOT need 600s like Nemotron — `--timeout 300 --thinking high` is
plenty for an adversary lens. Pair `--triad` (register parent first) +
`--claim-ceiling "L1 advisory adversary verdict only..."` +
`--forbidden-actions "no bash, no file writes, no commands, no claims of having
run anything"` + `--advisor-role adversary`.

---

## 18. `mcp_omnios_omnira_spawn` has a 30s CLIENT-SIDE MCP timeout — useless for real councils (2026-06-30)

The MCP tool `mcp_omnios_omnira_spawn` (the "spawn N parallel OMNIRA bodies" tool)
has a **30-second client-side MCP timeout** that is NOT raised by passing
`ttl_s` in the call. `ttl_s` controls the server-side kill window, not the
client-side wait. Any council where bodies need >30s of thinking returns:

```
MCP call failed: TimeoutError: MCP call timed out after 30.0s
(configured timeout: 30.0s)
```

Three concurrent `mcp_omnios_omnira_spawn` calls in this session all timed out
at 30s despite `ttl_s=240`. The MCP tool is **only** useful for sub-30s
advisory pings. The canonical multi-sister council pattern this skill exists
to serve — multiple bodies, real reasoning, 2-5 minute waits —
**must go through `node tools/pi-sister-spawn.mjs` invoked as a background
terminal** (`background=true`, `notify_on_complete=true`, `timeout=360`).

**Correct orchestration pattern for a multi-sister council:**
1. Write each sister's task brief to `/tmp/sister-<topic>.md` via `write_file`
   (membrane-safe — no shell escaping of long prompts).
2. Fire SparkMira FIRST in background via `node tools/sparkmira/cdp-bridge/sparkmira-ask.mjs`
   — she is the longest pole (30s-10min per response, often minutes).
3. In parallel, fire one `pi-sister-spawn.mjs` background terminal per sister,
   each with a distinct `--worker-model` so quotas don't collide
   (e.g. `openai-codex/gpt-5.5`, `anthropic/claude-opus-4-1`,
   `ollama-cloud/glm-5.2`). Use `--allow-cost-guarded-models` for GLM.
4. `mcp_omnios_council_post` to log the parallax review is live (organism visibility).
5. Poll background terminals as they notify; synthesize when all return.

**Do NOT pass `mcp_omnios_omnira_spawn` a `ttl_s` greater than 30 expecting it
to wait.** It will not. Use the terminal+`pi-sister-spawn.mjs` path instead.

---

## 19. SparkMira is the longest pole — fire her first (2026-06-30)

When running a parallax review that includes both Pi sisters AND SparkMira
(CDP bridge), fire SparkMira in background FIRST, then fire the sisters.
SparkMira responses routinely take 30s-10min (especially with research);
sisters usually return in 30s-5min. Firing SparkMira first means all paths
finish around the same time instead of SparkMira being the straggler after
every sister is already back.

Verify the bridge before firing:
`curl -s http://127.0.0.1:11440/health` -> `ok:true`, `cooldown:null`,
`queue.active:0`. Then `node tools/sparkmira/cdp-bridge/sparkmira-ask.mjs "..."`
in a background terminal with `notify_on_complete=true`.

---

## 20. Write sister task briefs to /tmp files, do not inline `--task` (2026-06-30)

Long multi-paragraph task prompts passed via `--task "<huge string>"` are
fragile (shell escaping, quote collapse, truncation). Write the brief to
`/tmp/sister-<topic>.md` with `write_file` first (membrane-safe, no shell),
then spawn with `--task-file /tmp/sister-<topic>.md`. This also makes the
briefs inspectable and re-runnable. The membrane will demand a
`justification_receipt` on each `write_file` — a one-line `ls /tmp/sister-X.md`
probe before the write is sufficient.

---

## 21. GLM/Qwen via ollama-cloud is allowed; Dashscope API is banned (2026-06-30)

Per `OMNIOS-CANON/council/CANONICAL-COUNCIL-ROLEMAP-V1.yaml`, the ban is
PROVIDER/TELEMETRY scope (Alibaba/Dashscope/Bailian API endpoints), NOT
weight-lineage. Qwen weights via ollama-cloud are ALLOWED as a distinct
lineage (self-hosted, no Alibaba telemetry). For ollama-cloud/glm-5.2 or
other cost-guarded models, pass `--allow-cost-guarded-models` to
`pi-sister-spawn.mjs`.

---

## Pre-spawn checklist
- [ ] Flag is `--worker-model` not `--model`
- [ ] `--no-extensions` in buildPiArgs (auto after 2026-06-17 patch)
- [ ] If `--triad`: register parent session first, pass both `--parent-session-id` and `--require-parent`
- [ ] Nemotron architecture role: `--timeout 600 --thinking medium` (NOT `med`) + prepend no-tools header to task file
- [ ] Check DeepSeek API balance if routing there
- [ ] Check Anthropic extra-usage balance if using Opus
- [ ] GitHub Copilot models: single-spawn only, not concurrent
- [ ] Note live batch `started_at` to filter stale notifications
- [ ] Multi-sister council: use `pi-sister-spawn.mjs` background terminals, NOT `mcp_omnios_omnira_spawn` (30s client timeout — see #18)
- [ ] SparkMira in the parallax: fire her FIRST in background, then sisters (see #19)
- [ ] Long task prompts: write to `/tmp/sister-<topic>.md`, spawn with `--task-file` (see #20)
- [ ] GLM/Qwen via ollama-cloud: pass `--allow-cost-guarded-models` (Dashscope API banned, ollama-cloud weights allowed — see #21)