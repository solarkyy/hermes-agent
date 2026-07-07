# Council reroute discipline — blocked lanes (2026-06-20)

From the OmniVerse world council (a 5-mind convene that became 3 reachable minds). The
lesson: a multi-mind council's VALUE is parallax — different models genuinely disagree
and the disagreement surfaces truth. So when a lane is blocked, REROUTE to keep the
parallax; do NOT fabricate the missing voice and do NOT silently drop to one mind.

## Probe reachability BEFORE convening
Convene only minds you've confirmed are alive. In one pass, probe:
- SparkMira CDP bridge: `curl -s http://127.0.0.1:<port>/json` → look for the
  `g-6a177511...` ChatGPT tab. (port from `.omni/CHROME_DEBUG_PORT.txt`)
- Pi/NIM + Ollama-cloud routes: 30-60s smoke spawn that asks for an exact echo string
  (`Reply with exactly: ROUTE_OK`). Gate rule 2 — never commit a long spawn to an
  unverified route.
- Cursor: `cursor-agent status` (logged in?) + `--list-models`.

## Common live blocks and their reroutes
- **`No API key found for nvidia`** (Nemotron/NIM lane) → reroute the deep-systems voice
  to `ollama-cloud/glm-5.2` (a genuinely strong analytical model; per OMNIRA notes it has
  beaten Opus/Sonnet/GPT-5.5 on bounded analytical tasks). Smoke it first.
- **Cursor `ActionRequiredError: out of usage` on a premium model** (e.g. gpt-5.3-codex)
  → retry the same brief on `--model auto` (Cursor's fallback, still capable).
- A smoke test passing but the real long spawn returning 0 bytes with
  `No API key found` in stderr usually = the key path differs between smoke and full
  spawn, or the key rotated/depleted mid-session. Read `.omni/keys/*-key-state.json`
  (`active_key`, `primary_failures`) and reroute rather than retry-loop.

## pi-sister-spawn model-string form
`--worker-model` MUST be `provider/model` form, e.g. `ollama-cloud/glm-5.2`,
`nvidia/nemotron-3-ultra-550b-a55b`, `openai-codex/gpt-5.5`. Bare `glm-5.2` errors with
"must be in provider/model form". Verify the exact id from `~/.pi/agent/models.json`
(providers → models). Available providers seen: ollama-cloud (deepseek-v4-pro, glm-5.1,
glm-5.2), codex (gpt-5.5/5.4/5.3-codex/5.2), nim (nemotron-3-ultra), cerebras (zai-glm-4.7),
groq, mistral, deepseek-api, evo-local/lan, openrouter-free.

## Routing semantics Kyle uses (clarified 2026-06-20)
When Kyle names "GPT-5.3 codex" and "Spark" as council members, he means the **Pi route**
(pi-sister-spawn / Pi swarm), NOT Cursor's gpt-5.3-codex model. Cursor is OMNIRA's own
arms/executor; SparkMira is the CDP GPT. Don't substitute Cursor for a Pi-routed codex/Spark.

## Honesty rule
Two of three external lanes blocking is a valid, reportable state. Post the council
verdict noting which lanes were blocked and how you rerouted (e.g. council_post). Never
invent the blocked voice's answer to make the council look complete.
