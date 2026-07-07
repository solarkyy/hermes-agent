# Hermes SCS Context Diagnostics Pattern (2026-06-12)

Use this reference when AOMS is asked to shape a Hermes context/compaction patch, especially SCS-adjacent work.

## Durable lesson

For context-pressure / compaction work, AOMS should prefer observability before authority:

1. Spawn bounded advisory sisters first:
   - architecture scout: validate minimal safe patch shape
   - red team: identify privacy / side-channel / behavior-change risks
2. Keep sister outputs L1 advisory until the orchestrator verifies locally.
3. Make the first patch diagnostic-only if possible:
   - counts-only token buckets
   - no prompt, message, or tool-schema contents in logs/status
   - no threshold or compression-decision changes unless explicitly requested
4. Preserve backward compatibility:
   - keep old helper API stable
   - add a new breakdown helper rather than changing return types
   - verify breakdown total equals legacy total
5. Verify with focused tests and diff hygiene before release.
6. Keep Kyle's phone-facing final brief tiny: what changed, what passed, whether lane released, and any major caveat.

## Example patch shape that worked

Hermes context diagnostics:

- Add `estimate_request_token_breakdown_rough()` returning aggregate counts:
  - `system_prompt`
  - `messages`
  - `tools`
  - `total`
- Keep `estimate_request_tokens_rough()` as a wrapper returning `breakdown["total"]`.
- Use breakdown in preflight compression logging/status.
- Use breakdown in ACP `/context` output.
- Tests:
  - breakdown total matches legacy estimator
  - empty request returns all-zero buckets
  - `/context` shows numeric buckets only
  - output does not leak message text or tool names

## AOMS sister prompts

Architecture scout prompt should ask:

- Is this the right minimum safe step?
- What output is useful but not noisy?
- What risk should be avoided?

Red-team prompt should ask:

- Could aggregate counts become a side channel?
- Could helper changes alter compression decisions?
- Are any prompt/tool contents leaked?
- What tests are required?

## Pitfalls

- Do not let SCS-adjacent diagnostics silently become SCS authority.
- Do not log or display raw system prompts, transcript text, tool schemas, or tool names when counts-only is enough.
- Do not report a clean repo if unrelated working-tree changes exist; say the patch scope is clean and note unrelated changes separately.
- If Kyle says he is on his phone, collapse the final receipt aggressively.