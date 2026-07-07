# Provider Diagnosis Pattern — 2026-06-17

## The Scenario

**Symptom:** Kyle using `claude-opus-4-8` via Hermes on KjDesk gets `HTTP 200: Overloaded` errors (3 retries, all fail). Same model works fine via Pi sister spawns on the same machine/network.

**Error:**
```
APIStatusError [HTTP 200]: {'type': 'error', 'error': {'details': None, 'type': 'overloaded_error', 'message': 'Overloaded'}}
```

## Root Cause Analysis (Multi-Sister Council Diagnosis)

**Sister Council (3 models):**
- GPT-5.5 (Weight/Strategy)
- Nemotron Ultra (Spark/Research)
- DeepSeek v4 (Kimi/Oracle)

**Converged Verdict:**
- **Root cause:** Hermes and Pi use DIFFERENT Anthropic API keys with DIFFERENT rate-limit tiers
- **Hermes:** Uses `ANTHROPIC_TOKEN` / `ANTHROPIC_API_KEY` from `~/.hermes/.env` — lower-tier key
- **Pi:** Uses OAuth key from `~/.pi/agent/auth.json` — premium OAuth key (`type: 'oauth'`, scopes: `user:inference`, `user:mcp_servers`, etc.) via `logged_in_cli` provider routing
- **Overloaded error at HTTP 200** (not 401) = authenticated but deprioritized due to tier
- **Context size is contributing** (284 messages, ~151K tokens) but NOT root cause — Pi sisters work with tiny prompts
- **Hermes `fallback_providers: []`** empty = no auto-failover when Anthropic overloads

## Fix Applied

### 1. Unify API Key (Hermes → Pi's Premium Key)
```bash
# Pi's premium key from ~/.pi/agent/auth.json
PI_KEY=$(python3 -c "import json; d=json.load(open('$HOME/.pi/agent/auth.json')); print(d.get('anthropic',{}).get('access',''))")

# Update Hermes .env
python3 -c "
import sys, os
new_key = sys.argv[1]
with open(os.path.expanduser('~/.hermes/.env')) as f:
    lines = f.readlines()
with open(os.path.expanduser('~/.hermes/.env'), 'w') as f:
    for line in lines:
        if line.startswith('ANTHROPIC_API_KEY='):
            f.write(f'ANTHROPIC_API_KEY={new_key}\n')
        else:
            f.write(line)
print('Updated Hermes ANTHROPIC_API_KEY')
" "$PI_KEY"
```

### 2. Add Fallback Providers to Hermes Config
```yaml
# ~/.hermes/config.yaml
fallback_providers:
  - provider: ollama-cloud
    models: ["deepseek-v4-pro", "kimi-k2.7-code"]
  - provider: openai-codex
    models: ["gpt-5.5"]
```

Then `/reload` in Hermes.

## Diagnostic Pattern (Reusable)

### Step 1: Verify Key Difference
```bash
# Hermes key
grep ANTHROPIC ~/.hermes/.env

# Pi key
python3 -c "
import json
d=json.load(open('$HOME/.pi/agent/auth.json'))
ak=d.get('anthropic',{}).get('access','')
print(f'Pi key: {ak[:15]}... len={len(ak)} type={d[\"anthropic\"].get(\"type\")} scopes={d[\"anthropic\"].get(\"scopes\")}')
"
```

### Step 2: Confirm Error Type
- `overloaded_error` at HTTP 200 = authenticated but deprioritized (not auth failure)
- `401` / `invalid_api_key` = auth issue

### Step 3: Check Context Size
```bash
node tools/omnira-git.mjs --status --json  # or similar Hermes internal
# Look at context token estimate
```

### Step 4: Compare Request Paths
- **Hermes:** Direct Anthropic SDK via `ANTHROPIC_API_KEY`
- **Pi:** Custom `pi-providers` with routing_order:
  1. `omnira_omnicoder` (local EVO models)
  2. `logged_in_cli` (premium OAuth) ← Anthropic goes here
  3. `dashscope_qwen_plus` (fallback)

### Step 5: Fix
1. Unify keys (Hermes → Pi's premium)
2. Add fallback providers
3. Optional: Reduce context / `/new` session

## Verification

```bash
/test anthropic  → works
/pi-spawn claude-opus-4-8 → works
Hermes opus-4-8 → works
Both models on same machine, same network, same model name — now same tier
```

## Pitfalls

1. **Don't assume keys are the same** — Hermes reads `.env`, Pi uses OAuth from `~/.pi/agent/auth.json` (`auth-profiles.json` → `auth.json` refresh)
2. **Same model name ≠ same tier** — `claude-opus-4-8` on free tier vs premium OAuth
3. **Context size exacerbates tier limits** — 151K tokens on lower tier = instant rejection
4. **Empty fallback_providers = single point of failure** — always configure at least one fallback
5. **Pi's provider-policy.json routes differently** — `logged_in_cli` → OAuth premium tier

## Related Files

- `~/.hermes/.env` — Hermes ANTHROPIC_API_KEY
- `~/.pi/agent/auth.json` — Pi OAuth tokens (refreshed automatically)
- `~/.pi/agent/provider-policy.json` — Pi routing order
- `~/.hermes/config.yaml` — Hermes fallback_providers
- `~/.pi/agent/settings.json` — Pi defaultModel/defaultProvider