# Nemotron 3 Ultra — Verified Routes (2026-06-14)

## Three distinct routes

| Route | Slug | Context | Cost | Auth | Verified |
|---|---|---|---|---|---|
| Nous inference free | `nvidia/nemotron-3-ultra:free` | 32K (model self-report) | `cost: None` | Nous OAuth `agent_key` from `~/.hermes/auth.json` | Yes — completion works, cost None, latency 2–15s |
| OpenRouter free | `nvidia/nemotron-3-ultra-550b-a55b:free` | 128K (model self-report) | $0 | `OPENROUTER_API_KEY` from `~/.hermes/.env` | Yes — completion works, cost 0, latency 80ms–15s |
| NIM/catalog paid | `nvidia/nemotron-3-ultra-550b-a55b` | advertised 1M | consumes NVIDIA credits | `NVIDIA_API_KEY` from `~/.hermes/.env` | Yes — `tools/nvidia-nim-resident-smoke.mjs` live OK |

## What the model actually reports

When asked "What is your context window in tokens? Answer with a number only." the free endpoints returned:
- Nous free `nvidia/nemotron-3-ultra:free`: `32768`
- OpenRouter free `nvidia/nemotron-3-ultra-550b-a55b:free`: `128000`

The paid NIM/catalog route is the one associated with the advertised 1M-token context. Plan Alpha observer around 32K/128K free context, not raw 1M ingestion.

## Existing tooling

- `config/nvidia-nim-residents.json` — resident profile `nemotron_systems_adversary` already maps to `nvidia/nemotron-3-ultra-550b-a55b`.
- `tools/adapters/nvidia-nim-api.mjs` — direct NIM adapter to `https://integrate.api.nvidia.com/v1/chat/completions`.
- `tools/nvidia-nim-resident-smoke.mjs` — dry-run/live smoke test with circuit-breaker and quota ledger.

No new OpenRouter client is needed; use existing NIM resident infrastructure for paid Ultra work.

## Hermes config status (as of 2026-06-14)

The `openrouter` provider in `~/.hermes/config.yaml` still pointed to the older `nvidia/nemotron-3-super-120b-a12b:free`. Updating it to Ultra free is a pending action requiring Kyle gate.

## Verification checklist

1. List models on the endpoint and grep `nemotron-3-ultra`.
2. Run a tiny exact-output completion and confirm cost.
3. Ask the model for its context window in tokens.
4. Test a ~25K-token prompt to confirm it processes within reported context.
5. Run 5 rapid calls to sample latency distribution.
6. For paid route, run `tools/nvidia-nim-resident-smoke.mjs --run --resident nemotron_systems_adversary` and check quota ledger.

## Pitfalls

- `nvidia/nemotron-3-ultra:free` (Nous) and `nvidia/nemotron-3-ultra-550b-a55b:free` (OpenRouter) are different slugs with different context windows.
- Nous `agent_key` is a JWT for `inference-api.nousresearch.com`; it is not an OpenRouter key.
- Ultra free has variable latency; use it for batch/background work, not interactive routing.
- Super 120B free leaks reasoning and ignores exact-output instructions; prefer Ultra free for structured Alpha outputs.
