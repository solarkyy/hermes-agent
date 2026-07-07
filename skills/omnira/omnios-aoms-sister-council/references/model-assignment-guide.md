# Model Assignment Guide for AOMS Sister Councils

## Philosophy
Match model strengths to analytical lens. Don't default to one model for everything.

---

## Canonical Assignments

| Lens | Model | Provider | Strengths for This Lens |
|------|-------|----------|------------------------|
| **Architecture/Vision** | `gpt-5.5` | `openai-codex` | 1M+ context, systems synthesis, long-horizon reasoning, cross-domain pattern matching |
| **OmniCoder/Delegation** | `claude-opus-4-8` | `anthropic` | Code-aware, rigorous workflow tracing, security mindset, explicit failure taxonomy |
| **SparkMira/Integration** | `deepseek/deepseek-v4-pro` | `deepseek` | Protocol analysis, async systems, browser automation debugging, cost-effective for long context |
| **Infrastructure/Ops** | `gpt-5.5` | `openai-codex` | SPOF detection, scaling math, recovery modeling, cross-node state reasoning |
| **Synthesis/Strategy** | `claude-opus-4-8` | `anthropic` | Judgment, trade-offs, unified narrative, executive summary, gate design |

---

## Model Capabilities Matrix

| Capability | GPT-5.5 | Opus 4.8 | DeepSeek V4 Pro | Nemotron 3 Ultra |
|------------|---------|----------|-----------------|------------------|
| Context Window | 1M+ | 200K | 128K | 128K |
| Code Analysis | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| Systems Architecture | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★☆ |
| Protocol Debugging | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★☆☆ |
| Security Analysis | ★★★☆☆ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| Strategic Synthesis | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★☆ |
| Cost (relative) | High | High | Medium | Medium |
| Reasoning Depth | xhigh | xhigh | xhigh | high |

---

## Assignment Rules

1. **Never use the same model for all sisters** — defeats the purpose of multi-perspective analysis
2. **Synthesis sister must be different** from analytical sisters — fresh judgment
3. **DeepSeek for integration/protocol** — excels at async/browser/CDP analysis
4. **Opus for code/security/delegation** — best at tracing execution paths
5. **GPT-5.5 for architecture/infra** — best at cross-system synthesis
6. **Opus for final synthesis** — best at weighted trade-offs and executive communication

---

## Provider Spec Format (CRITICAL)

Always use `provider/model` format in `--worker-model`:

| Correct | Incorrect |
|---------|-----------|
| `openai-codex/gpt-5.5` | `gpt-5.5` |
| `anthropic/claude-opus-4-8` | `claude-opus-4-8` |
| `deepseek/deepseek-v4-pro` | `deepseek-v4-pro` |
| `nvidia/nvidia/nemotron-3-ultra-550b-a55b` | `nemotron-3-ultra` |

The provider prefix is REQUIRED. List comes from `/home/kylej/.hermes/config.yaml` providers section.

---

## Orchestrator Model

Each sister spawn gets an orchestrator that validates output:
- Default: `anthropic/claude-sonnet-4` (or similar)
- Can be overridden with `--orchestrator-model`
- Orchestrator checks: schema compliance, forbidden patterns, claim ceiling adherence