# Free Frontier Model Council Pattern — 2026-06-15

## Trigger

Use this pattern when Kyle asks to exploit temporarily free frontier models (e.g. Nex-N2-Pro, Nemotron 3 Ultra) for research, always-on lanes, parallel councils, or comparative cognition against GPT-5.5.

## 2026-06-15 Session

AOMS council ran:

- GPT-5.5: Weight / Strategy
- GPT-5.5: Edge / Implementation
- Nemotron 3 Ultra: Spark / Research Surface
- Nemotron 3 Ultra: Alpha / Always-On Cortex
- GPT-5.5: synthesis sister

All five completed successfully via `tools/pi-sister-spawn.mjs`.

## Council Verdict

`PASS with constraints`.

Use free frontier models as **surplus cognition**, not authority.

Good lanes:

- broad research sweeps
- literature/blog/social scanning
- first-pass synthesis
- brainstorming
- hypothesis generation
- structured extraction
- classification/ranking
- non-secret code review second opinions
- sanitized always-on monitoring summaries
- draft generation for trusted review

Reserved lanes:

- final synthesis
- identity/personality definition
- canonical memory writes
- secrets/credentials/private data
- irreversible actions
- user-facing action-affecting decisions
- financial/legal/medical/security-sensitive/exploit tasks
- external autonomous actions

## Route Model to Lane

| Lane | Preferred model | Use |
|---|---|---|
| Broad research sweeps | Nex-N2-Pro | Long-form synthesis, comparative analysis, planning drafts |
| Structured extraction | Nemotron 3 Ultra | JSON-like extraction, classification, ranking, technical summaries |
| Literature/blog/social scanning | Nemotron 3 Ultra | High-volume signal detection and source clustering |
| Parallel hypothesis generation | Nex-N2-Pro + Nemotron | Independent ideas, dissent, exploratory framing |
| Drafting | Nex-N2-Pro | First-pass reports/plans/summaries for trusted review |
| Code review second opinion | Nex-N2-Pro or Nemotron | Non-secret, non-security-critical critique |
| Always-on monitoring | Nemotron 3 Ultra | Sanitized metrics, heartbeat, anomaly/event summaries |
| Important research verification | Both free models → trusted verifier | Quorum-style disagreement/synthesis handoff |
| Final synthesis/decision | Trusted core/human | Required before canonical memory or action |

## Hard Blocks

Do not send free models:

- secrets, credentials, API keys, tokens
- unredacted private/sensitive personal data
- Kyle’s direct private instructions
- raw sensitive logs or file contents with PII
- identity/personality definition
- canonical memory updates
- final strategic authority
- irreversible advice/actions
- financial, legal, medical, security-sensitive, or exploit-related tasks
- user-facing action-affecting decisions without trusted review
- autonomous external actions

## Receipt Requirements

Every external free-model call should log:

- `receipt_id`
- `timestamp`
- `workflow`
- `task_id`
- `provider`
- `model`
- `route_reason`
- `risk_level`
- `input_hash`
- `input_redaction_level`
- `output_hash`
- `tokens_in/out`
- `latency_ms`
- `cost_usd`
- `status`
- `fallback_from`
- `schema_valid`
- `human_or_trusted_verified`
- `notes`

Also track provider/model health, drift probes, fallbacks, and whether output was advisory-only.

## 48-Hour Pilot

1. Enable free-model routing only for low-risk lanes.
2. Add mandatory redaction before external calls.
3. Log receipts for every call.
4. Run quorum tests on important research:
   - ask Nex-N2-Pro and Nemotron independently
   - compare disagreement
   - send summary to trusted verifier
5. Run nightly drift/quality probes.
6. Monitor malformed JSON, hallucinated citations, unsupported causal claims, model unavailability, privacy violations, and disagreement requiring escalation.
7. After 48 hours, review usefulness, verification burden, latency/reliability, privacy compliance, and whether lanes should expand, shrink, or pause.

## Handoff Targets

- SparkMira: research-lane validation, citation traceability, source diversity, echo-control/dissent requirements.
- Pi: `route_free_ok(prompt_metadata)` gate, receipt logging, redaction, fallback/health cache, drift probes.
- Edge: routing rules, retry/fallback policy, schema validation, budget/rate-limit guardrails.
- Kyle: approve hard blocks, always-on monitoring scope, external-provider risk, and whether free models may produce user-facing drafts after trusted review.

## Important Caveat

Free status is temporary weather. Do not encode provider pricing or availability as durable truth. Encode the routing discipline, receipts, redaction, verification, and fallback pattern.
