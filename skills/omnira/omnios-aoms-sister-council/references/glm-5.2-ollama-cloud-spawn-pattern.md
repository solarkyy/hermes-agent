## Working Spawn Template

```bash
node tools/pi-sister-spawn.mjs \
  --worker-model ollama-cloud/glm-5.2 \
  --lane coord \
  --nonce <unique-nonce-YYYYMMDD> \
  --claim-ceiling "<scope> only; no admission, no authorization, no code changes" \
  --forbidden-actions "claim local state, authorize protected actions, execute tools, write files, modify config, mutate secrets" \
  --no-tools --no-audit --no-receipt-skeleton \
  --task-file /tmp/<task>.md \
  --timeout 300 \
  --thinking xhigh \
  --output-dir /tmp/spawn-<lens>-<nonce>
```

## Pitfalls to Avoid

1. **Don't use `--model`** — pi-sister-spawn uses `--worker-model`
2. **Ensure `--no-extensions`** is in buildPiArgs (auto since 2026-06-17 patch)
3. **Prepend no-tools header to task file** for Nemotron/GLM:
   ```
   IMPORTANT: You have NO tools available in this session. Do not attempt bash,
   file reads, or any tool calls. Answer entirely from your training knowledge
   and the context provided below.
   ```
3. **Set adequate timeout** — 300s minimum, 600 for dense GLM 5.2 analysis
4. **Use `xhigh` thinking** for GLM 5.2 dense analysis (not `high` or `med`)
5. **GLM 5.2 via Ollama Cloud needs omnios 2 key** — verify env var resolves correctly

## When to Use GLM 5.2

| Scenario | Model |
|----------|-------|
| Risk analysis (membrane, failure modes, invasion boundaries) | **GLM 5.2** (best) |
| Deep analysis with structured output | GLM 5.2 or Nemotron Ultra |
| Architecture/synthesis | GPT-5.5 (or Nemotron) |
| VPS integration / code tasks | Cursor + DeepSeek v4 Pro |
| Always-on / monitoring | Nemotron 3 Ultra |
| Free capacity sweeps | Nex-N2-Pro / Nemotron |

## Verification Checklist

Before spawning GLM 5.2 sister:
- [ ] `OLLAMA_CLOUD_KEY_FALLBACK` in .env is the Omnios 2 key (962020...)
- [ ] `ollama-cloud/glm-5.2` model available via `curl -s http://127.0.0.1:11435/v1/models`
- [ ] `--worker-model ollama-cloud/glm-5.2` (not `--model`)
- [ ] `--timeout 300` minimum, `300-600` for dense analysis
- [ ] `--thinking xhigh` for dense analysis
- [ ] Task file prepended with no-tools header if `--no-tools`
- [ ] `--no-tools --no-audit --no-receipt-skeleton` for advisory sisters