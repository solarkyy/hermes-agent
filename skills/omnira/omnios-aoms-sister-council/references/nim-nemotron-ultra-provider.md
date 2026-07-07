# NVIDIA Nemotron 3 Ultra Provider Configuration

## What exists (verified 2026-06-14)

There are **three distinct endpoints** for Nemotron 3 Ultra and they differ on context, cost, and auth path. Do not conflate them.

| Endpoint | Slug | Context | Cost | Latency | Auth | Use for |
|---|---|---|---|---|---|---|
| **Nous inference free** | `nvidia/nemotron-3-ultra:free` | **32K tokens** (model self-report) | **None** | 2–15s variable | Nous OAuth `agent_key` from `~/.hermes/auth.json` | Quick Alpha probes, council synthesis |
| **OpenRouter free** | `nvidia/nemotron-3-ultra-550b-a55b:free` | **128K tokens** (model self-report) | **$0** | 1–12s variable | `OPENROUTER_API_KEY` from `~/.hermes/.env` | Read-only Alpha observer, org memory sweeps, high-volume synthesis |
| **NIM/catalog paid** | `nvidia/nemotron-3-ultra-550b-a55b` | Advertised 1M tokens | Consumes credits | Faster/stable | `NVIDIA_API_KEY` from `~/.hermes/.env` | Deep research requiring 1M context; existing resident tooling already works |

**Critical corrections from 2026-06-14:**
- The **free** endpoints report their own context windows as **32K (Nous)** and **128K (OpenRouter)**, not 1M.
- The **1M-token claim** applies to the paid NIM/catalog route.
- The **NIM resident tooling already exists and works** (`config/nvidia-nim-residents.json`, `tools/nvidia-nim-resident-smoke.mjs`). No custom OpenRouter client is needed for paid/full-context Ultra work.
- For OMNIRA's free always-on Alpha layer, plan for **32K/128K compressed context**, not raw 1M ingestion.

---

## Auth paths

### Nous inference (paid)

Hermes `auth.json` holds a Nous OAuth `agent_key` (JWT). The Pi CLI and Nous inference endpoint use this directly.

```bash
# Verify model exists on Nous inference
ACCESS=$(python3 -c "import json; d=json.load(open('/home/kylej/.hermes/auth.json')); print(d['providers']['nous']['agent_key'])")
curl -s -H "Authorization: Bearer *** https://inference-api.nousresearch.com/v1/models | \
  python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[]) if 'nemotron' in m['id']]"
```

Expected output includes:
```
nvidia/nemotron-3-ultra-550b-a55b
nvidia/nemotron-3-super-120b-a12b
nvidia/nemotron-3-nano-30b-a3b
nvidia/llama-3.3-nemotron-super-49b-v1.5
```

### Nous inference free

The Nous inference free endpoint uses the OAuth `agent_key` from `~/.hermes/auth.json`. It is a separate credential from OpenRouter.

```bash
ACCESS=$(python3 -c "import json; d=json.load(open('/home/kylej/.hermes/auth.json')); print(d['providers']['nous']['agent_key'])")

curl -s -X POST https://inference-api.nousresearch.com/v1/chat/completions \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-ultra:free","messages":[{"role":"user","content":"Output only the exact string, no explanation: ULTRA OK"}],"max_tokens":32}'
```

Expected: `cost: null` (or absent), content exactly `ULTRA OK`.

### OpenRouter free

Hermes resolves `${OPENROUTER_API_KEY}` from `~/.hermes/.env`, which is loaded by the Hermes process. Direct `curl` tests must source that file.

```bash
set -a
source /home/kylej/.hermes/.env
set +a

echo "Key prefix: ${OPENROUTER_API_KEY:0:12}"

curl -s -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-ultra-550b-a55b:free","messages":[{"role":"user","content":"Output only the exact string, no explanation: ULTRA OK"}],"max_tokens":32}'
```

Expected: cost `0`, model slug containing `nemotron-3-ultra`, content exactly `ULTRA OK`.

---

## Hermes config update

Change the existing `openrouter` provider block from the older Super 120B to Ultra:

```yaml
providers:
  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    base_url: https://openrouter.ai/api/v1
    models:
      nemotron-free:
        context_length: 128000          # ← corrected from 131072 / 1M claims
        description: |
          Nemotron 3 Ultra (550B/55B MoE) via OpenRouter free tier.
          128K context, $0, variable 1-12s latency. L1 advisory only.
          For Alpha observer, Spark synthesis, org memory sweeps.
        max_tokens: 4096
        name: nvidia/nemotron-3-ultra-550b-a55b:free
        role: alpha-cloud
```

Do **not** set `context_length: 1000000` unless you route to the paid NIM/Nous inference model slug without `:free`.

For paid NIM work, use the already-configured resident profile `nemotron_systems_adversary` in `config/nvidia-nim-residents.json` rather than duplicating the model in Hermes providers.

---

## Pi sister spawn commands

### Analytical / builder mode (default)

```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --triad --require-parent --parent-session-id <coord_lane_session_id> \
  --worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b \
  --lane coord \
  --task-file /tmp/sister_<lens>.md \
  --claim-ceiling "L1 advisory only; no code changes, no live mutations, no admission" \
  --no-tools \
  --timeout 300 \
  --nonce <unique-nonce>
```

**Note on model slug:** The NIM route uses `nvidia/nemotron-3-ultra-550b-a55b`. Pi's `--worker-model` expects `provider/model`, so pass `nvidia/nvidia/nemotron-3-ultra-550b-a55b`. The Nous inference route uses `nvidia/nemotron-3-ultra:free` (32K) or `nvidia/nemotron-3-ultra-550b-a55b` (paid). Verify with `pi models list | grep nemotron` and with a live probe.

**Verified 2026-06-14 probes:**
- Nous free `nvidia/nemotron-3-ultra:free` — works, cost $0, context self-report 32768 tokens.
- Nous paid `nvidia/nemotron-3-ultra-550b-a55b` — works, incurs cost, likely 1M context.
- OpenRouter free `nvidia/nemotron-3-ultra-550b-a55b:free` — 401 with Nous key; needs `OPENROUTER_API_KEY`.
- NIM `nvidia/nemotron-3-ultra-550b-a55b` via `tools/nvidia-nim-resident-smoke.mjs --run --resident nemotron_systems_adversary` — success (11.7s, "NIM SMOKE OK", ledger updated).

### Conversational emergence mode

See original conversational pattern in `deep-conversational-research.md`. Use `--lane mythos`, `--no-tools`, `--no-audit`, `--thinking xhigh`.

### Mythos Harvest Council mode (2026-06-14)

**When the meta-council becomes product owner of corpus foundry.**

```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios

# Task file with full corpus foundry context + meta-council outputs
cat > /tmp/harvest-council-prompt.md << 'EOF'
# [Full corpus foundry 7 phases + meta-council outputs + directive format]
EOF

# Spawn 7 sisters in parallel (background + notify)
for i in {1..7}; do
  node tools/pi-sister-spawn.mjs \
    --worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b \
    --lane mythos \
    --task-file /tmp/harvest-council-prompt.md \
    --no-tools --no-audit --no-findings --no-receipt-skeleton \
    --thinking xhigh \
    --timeout 240 \
    --nonce harvest-council-$(date +%Y%m%d)-$i \
    > /tmp/harvest-council-$i-meta.json 2> /tmp/harvest-council-$i.err &
done

# Wait for all (process action='wait' per session, or poll)
```

**Parameters:**
- `--worker-model nvidia/nvidia/nemotron-3-ultra-550b-a55b` — Nemotron Ultra 3 Ultra via NIM
- `--lane mythos` — Conversational emergence
- `--task-file /tmp/prompt.md` — Complex prompt via file
- `--no-tools --no-audit --no-findings --no-receipt-skeleton` — Pure conversation
- `--thinking xhigh` — Maximum reasoning
- `--timeout 240` — 4 min (actual: 18-40s)
- Background + `notify_on_complete=true` for parallel wall-time efficiency

**Convergence (7 sisters, all PRIORITY 1):**
- PRIVATE/RESTRICTED, CONSENT ABSENT/INHERITED, QUARANTINE, EVIDENCE: INFERRED
- Themes: deleted comms, unasked questions, unwitnessed confessions, AI confessions, unsent letters

See `references/mythos-harvest-council-pattern.md` for full task file, convergence analysis, recursive loop diagram.

---

## Verification checklist before relying on Ultra

Run these before standing up Alpha or assigning Ultra to a department:

1. **Model availability:** `curl /v1/models` on both Nous inference and OpenRouter, grep `nemotron-3-ultra`.
2. **Free tier cost:** confirm `usage.cost == 0` for `:free` endpoint and `cost: null` for Nous `:free`.
3. **Context reality:** ask the model directly or test with a large prompt. Expect `32768` on Nous free, `128000` on OpenRouter free.
4. **Instruction following:** test exact-output prompts. Ultra obeys; Super 120B free tends to leak reasoning.
5. **Latency distribution:** run 5 rapid calls; expect occasional 10s+ queueing on free tier.
6. **JSON mode:** verify valid JSON output with no markdown wrapping.
7. **Large context:** test ~25K-token prompt to confirm processing works within 128K.
8. **Paid route smoke:** run `node tools/nvidia-nim-resident-smoke.mjs --run --resident nemotron_systems_adversary` and verify `NIM SMOKE OK` plus ledger update.

## Pitfalls

- **Do not assume 1M context on `:free`.** The free endpoints are 32K (Nous) and 128K (OpenRouter). Plan compression/retrieval, not full corpus dumps.
- **Do not use Nous `agent_key` as OpenRouter key.** The Nous OAuth token is a JWT for `inference-api.nousresearch.com`. OpenRouter tests need `OPENROUTER_API_KEY` from `~/.hermes/.env`.
- **Do not build a new OpenRouter client for paid Ultra work.** Use the existing NIM resident tooling (`config/nvidia-nim-residents.json`, `tools/nvidia-nim-resident-smoke.mjs`).
- **Do not route real-time latency-sensitive work to Ultra free.** 1–12s cold/warm variance is fine for 10-minute cadence, not for interactive routing.
- **Super 120B free is inferior for exact-output tasks.** It leaks reasoning text and ignores exact-string instructions. Prefer Ultra free for structured Alpha outputs.
- **Context-length token counting is approximate.** 128K ≈ ~96K English words or ~32K–40K tokens of code/corpus. Use a tokenizer-aware budget in the Alpha context builder.
- **Super 120B free is inferior for exact-output tasks.** It leaks reasoning text and ignores exact-string instructions. Prefer Ultra free for structured Alpha outputs.
- **Context-length token counting is approximate.** 128K ≈ ~96K English words or ~32K–40K tokens of code/corpus. Use a tokenizer-aware budget in the Alpha context builder.

---

## When to use which

| Need | Use |
|---|---|
| Free always-on Alpha observer, 10-min cadence | `nvidia/nemotron-3-ultra-550b-a55b:free` via OpenRouter |
| Spark research requiring 1M context | Paid `nvidia/nemotron-3-ultra-550b-a55b` via Nous inference/NIM |
| Fast interactive coding | GPT-5.3-Codex-Spark, not Nemotron |
| Budget-sensitive org memory sweeps | Ultra free with compressed context |

---

## Related

- `references/deep-conversational-research.md` — Nemotron Ultra conversational sister pattern
- `references/aoms-operating-manual.md` — lanes, claim ceilings, triad requirements
