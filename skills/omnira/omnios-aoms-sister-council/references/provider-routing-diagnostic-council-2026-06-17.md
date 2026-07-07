# Provider Routing Diagnostic Council — 2026-06-17

## Trigger
Kyle: "why am i getting this suddenly it works fine on pi and was working fine"
Symptom: claude-opus-4-8 via Hermes → `HTTP 200: Overloaded` (3 retries, all fail).
Same model via Pi sister spawns → works fine. Same machine, same network.

## Council Shape
3 model-different sisters, parallel background spawns, 240s timeout, L1 advisory only.

### Evidence Package (shared)
- Hermes .env: `ANTHROPIC_TOKEN` + `ANTHROPIC_API_KEY` on same line (line 55)
- Error: HTTP 200 `overloaded_error` (not 401, not 529) — authenticated but deprioritized
- Pi auth.json: `anthropic: {type: 'oauth', access: 'sk-ant...'}` — premium OAuth
- Pi provider-policy.json: routes Anthropic through `logged_in_cli` (premium tier)
- Hermes fallback_providers: [] (empty)
- Hermes context: 284 msgs, ~151K tokens
- Pi sisters: fresh spawns, ~2-5K tokens
- Ollama Cloud proxy: healthy (24h+ uptime, 200 requests, 0 failures)

### Lenses
| Lens | Model | Role |
|------|-------|------|
| Architecture/Strategy | openai-codex/gpt-5.5 | Is this key-tier, context-size, or networking? |
| Infrastructure | nim/nvidia/nemotron-3-ultra-550b-a55b | Provider routing, fallback chains, rate-limit mechanics |
| Adversary/Falsifier | ollama-cloud/deepseek-v4-pro | Challenge the obvious answer, find what others missed |

### Spawn Commands
```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --worker-model openai-codex/gpt-5.5 \
  --lane coord --nonce provider-diag-gpt55-20260617 \
  --claim-ceiling "provider routing diagnostic analysis only" \
  --forbidden-actions "claim local state, authorize protected actions, execute tools, write files, modify config, mutate secrets" \
  --no-tools --no-audit --no-receipt-skeleton \
  --task-file /tmp/sister-provider-diag.md --timeout 240 --thinking xhigh \
  --output-dir /tmp/spawn-diag-gpt55
```
(Repeat for Nemotron with `nim/nvidia/nemotron-3-ultra-550b-a55b` and DeepSeek with `ollama-cloud/deepseek-v4-pro`)

### Convergence
All three sisters converged on root cause: **different API keys on different rate-limit tiers.**

| Sister | Verdict | Key Insight |
|--------|---------|-------------|
| GPT-5.5 | WATCH | Hermes likely sending large request with lower-tier key; Pi uses premium path |
| Nemotron | BLOCK | Hermes key tier mismatch + no fallback = hard failure; fix before retrying |
| DeepSeek | WATCH | Same diagnosis; emphasized fallback_providers as immediate mitigation |

### Durable Fix
1. Unify Anthropic keys between Hermes and Pi
2. Add `fallback_providers` to Hermes config (Ollama Cloud models)
3. Context hygiene: summarize/compact at ~100K tokens
4. Provider health monitoring with circuit breaker

### Pitfall Learned
The `overloaded_error` at HTTP 200 (not 529) is the tell that it's a tier-deprioritization
issue, not a server outage. HTTP 200 = authenticated; overloaded = deprioritized. If it were
a real outage, Pi would fail too. If it were a bad key, it would be HTTP 401.
