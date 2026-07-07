# Pre-Spawn Gate — Lessons from 2026-06-17

## Run this checklist before every sister spawn. Each item was violated today.

### 1. Am I currently running AS a Claude model?
If yes — DO NOT spawn Opus/Sonnet/Haiku sisters.
You burn Pi's claude.ai extra-usage quota on spawns that return empty.
Opus 4.8 spent Pi's credits and returned empty while I was literally running as Claude.
Use GLM 5.2, DeepSeek v4, SparkMira (free), or Cursor instead.

### 2. Smoke test the route before committing to a long spawn (30 seconds)
```bash
node tools/pi-sister-spawn.mjs \
  --worker-model <model> \
  --task "Reply with exactly: ROUTE_OK" \
  --timeout 30 --no-tools --no-audit --no-findings --no-receipt-skeleton
cat .omni/sister-spawn/<latest>/stdout.log
```
Empty stdout → read stderr before assuming failure.
"Key exhausted" in stderr is often a fallback-cycle artifact, NOT real key exhaustion.
Smoke test proved GLM route was alive after a false "exhausted" report.

### 3. Full context dump — NEVER "ground in the codebase"
Any phrasing like "ground this in the codebase", "inspect the files", "read the source"
causes models to reach for bash/tools even with --no-tools. Training reflex.

WRONG: "Ground this spec in the actual codebase before writing the JSON."
RIGHT:  "Here is the grounded context: [paste excerpts, sigs, counts]. Reason purely."

GLM 5.2 produced a complete 3-page Risk JSON with full context dump.
Sonnet, DeepSeek v4, Nemotron all ignored --no-tools and tried bash when told to "ground."

### 4. Understand Ollama Cloud key routing before spawning
pi-sister-spawn primary key = env.OLLAMA_API_KEY (set in .env to omnios 1 key dc7c72...).
OLLAMA_CLOUD_KEY_PRIMARY / OLLAMA_CLOUD_KEY_FALLBACK are NOT directly read as primary.
Passing OLLAMA_CLOUD_KEY=xxx as shell override does NOT switch the key.
To use omnios 2 key: set OLLAMA_API_KEY=*** explicitly in spawn env.

### 5. Architecture tasks cost 5-10x more than Risk tasks
GLM 5.2 ran 7 minutes on Architecture. Risk took 2 minutes on same key.
For Architecture: (a) do it yourself, (b) SparkMira, (c) Cursor, (d) spawn last.

### 6. Model routing preference (empirical, 2026-06-17)
GLM 5.2 beat Opus 4.8 + Sonnet 4.6 + GPT-5.5 on Risk analysis head-to-head.

- Risk/membrane → GLM 5.2 (Ollama Cloud)
- Architecture spec → GLM 5.2 or DeepSeek v4 (with full context dump)
- Pattern brain → SparkMira (ChatGPT CDP, free, L5)
- Code building → Cursor (agent --model auto)
- Open exploration → GPT-5.5 or Nemotron

### 7. SparkMira = ChatGPT agent via CDP, NOT a Pi spawn
```bash
curl -s http://127.0.0.1:9233/status          # check connected/input_ready
curl -s -X POST http://127.0.0.1:9233/send \  # works even when input_ready: false
  -H "Content-Type: application/json" \
  -d '{"text": "your message"}'
```
L5 access, GitHub connector, full GPT power, costs nothing.
Use her for every major architecture/design decision.
Her omnira-git v2 additions (HMAC, split lease, brain integrity tiers, 8 failure modes)
outperformed all Pi sisters combined on the same task.
