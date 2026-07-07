# GLM-5.2 via Ollama Cloud for AOMS councils — 2026-06-17

## What this session proved

GLM-5.2 is usable in OMNIRA AOMS routing through the `ollama-cloud` provider. It should be treated as a long-context scout / WATCH route, not as the default authority route.

Observed route probe:

```text
provider       model    context  max-out  thinking  images
ollama-cloud   glm-5.2  976K     32.8K    yes       no
```

Successful council role:

```text
GLM-5.2 context scout: ollama-cloud/glm-5.2
```

It succeeded during a read-only five-year AOMS strategy council alongside Opus 4.8, GPT-5.5, DeepSeek v4 Pro, and Kimi K2.7. The run used it for broad context scouting rather than final synthesis or authority.

## Recommended routing

Use `ollama-cloud/glm-5.2` when:

- The council needs a long-context sweep over many OMNIRA status/canon/roadmap files.
- The job is read-only/advisory and benefits from broad compression.
- A model-different I3 lane is useful, especially when GPT/Claude/DeepSeek outputs may be correlated.
- The task needs "what did we miss across all this material?" rather than final execution authority.

Do not use GLM-5.2 as the only source of truth for:

- Protected gates, model admission, memory/canon writes, training decisions, deploys, cron/service changes, or external actions.
- Any claim requiring runtime verification unless its output is followed by tool-grounded checks.

## Pi / AOMS model string

Use the Pi provider-qualified string:

```text
ollama-cloud/glm-5.2
```

Do not use bare or vendor-style prefixes such as:

```text
zai/glm-5.2
glm-5.2
```

The live provider list under `~/.pi/agent/models.json` remains authoritative. Probe before spawning if the route table might have changed.

## Hermes route expectation

Kyle's expectation from this session: GLM-5.2 should be available on both Hermes and Pi through Ollama Cloud. If Hermes cannot use it while Pi can, investigate provider config/key mapping and model registry drift before declaring the model unavailable.

## Five-year council learning attached to this route

The broader council verdict was not "more model access solves autonomy." The convergence was:

```text
Make Truth Admissible.
```

Before expanding unattended autonomy, build the runtime truth spine:

1. Runtime truth / oneness census.
2. Canon reconciliation + supersession ledger.
3. Verifier-computed receipt/provenance chain.
4. I3 independence scoring.
5. Recurrence detector + two-key gate.
6. One boring closed loop: goal → plan → sandbox wake → artifact → verifier → Kyle Gate → morning brief.

GLM-5.2's role in that phase is context scout: good for finding drift and summarizing broad state; not enough for admissibility without receipts.