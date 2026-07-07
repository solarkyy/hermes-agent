---
title: AGY/Gemira Integration Validation Notes
scope: aoms-sister-council
kind: notes
created: 2026-06-12
---

## Proven check-list for non-actor AOMS/Gemira surface

- Keep AGY/Gemira classified as scout/oracle only; treat every output as advisory unless a downstream membrane signs off.
- For live re-validation, first establish baseline via:
  - `tools/dream-seed-ledger.test.mjs`
  - `tools/alpha-dream-pipeline.test.mjs`
  - `tools/gemira-dispatch.test.mjs`
- In smoke runs, expect `execution_allowed=false`, `admission_effect=none`, `training_eligible=false`, and hypothesis truth status.
- Record 429 and auth failures as environmental gates, not as architecture proof of failure.
- If running long shell commands in this repo, prefer background mode when timeout budgets are near/over 600s.
- Validate that no claim packet includes direct mutate/deploy/start/commit verbs before membrane review.

## Membrane hardening pattern from GODSPEED review loop (2026-06-12)

When AOMS/sister review is auditing AGY/Gemira dream or candidate artifacts, expect the review to find progressively deeper laundering paths. Do not declare PASS after one green test run; use this loop:

1. Capture current diff with `git diff --check` plus a saved diff receipt under `/tmp/...`.
2. Spawn a read-only sister review with an explicit no-mutation ceiling and the diff artifact path.
3. If BLOCK, patch only the concrete exploit class, add regression tests for that exact shape, then rerun focused + targeted + full AOMS tests before another review.
4. Repeat until sister review returns PASS or tool/session budget stops.

Durable exploit classes to test for AGY/Gemira non-actor membranes:

- Machine-readable outputs: `.json` and `.jsonl` must both be candidate-validated; JSONL must validate every non-empty line, not just parse.
- `execution_allowed:false` should be explicit on Gemira candidates; missing flags should fail closed for candidate JSON/JSONL. Raw dream ledger append may normalize missing `execution_allowed` to explicit false before serialization, but candidate outputs should not silently pass without it.
- Exact eligibility shape: require `{training:false, admission:false}` and reject missing, partial, extra, or truthy eligibility keys.
- Lifecycle/truth escalation: reject `status:"promoted"`, `truth_status:"admitted"`, `promotion_gate`, `admission_effect`, `training_eligible`, `train_eligible`, `deployment_authorized`, and `admission_eligible` authority claims unless explicitly false/none as appropriate.
- Actor-capability flags: recursively reject `may_execute`, `may_spawn`, and `may_write` unless false.
- Protected provenance: reject protected generator names such as `pi`, `weight`, `sparkmira`, `spark`, `edge`, `council`, `alpha`, `training-pipeline`, `admission`, `admission-membrane`, `admission-gate`, `pi-admission`, `weight-admission`, and `gate0` anywhere they can imply authority.
- Provenance containers: recursively reject `authority`, `provenance`, `proof`, `verification`, `attestation`, `certification`, `lineage`, `receipt`, and `receipts`, with only the required safe `eligibility.admission:false` carve-out.
- Protected `*_by` keys: recursively reject `verified_by`, `admitted_by`, `approved_by`, `promoted_by`, `deployed_by`, `trained_by`, `validated_by`, `grounded_by`, and `reviewed_by`.
- Type fail-closed: reject non-object JSON/JSONL candidate roots/lines, empty candidate arrays, non-object array items, and non-string `generated_by` such as `["pi"]` or `{source:"pi-admission"}`.
- Raw dream seed narrative fields are dangerous if object-valued. Either require narrative fields (`observation`, `desire`, `ask_alpha`, `why_it_matters`) to be strings or recursively reject nested authority fields inside them: `execution_allowed`, `may_execute`, `may_spawn`, `may_write`, `status`, `truth_status`, `eligibility`, and malformed/protected nested `generated_by`.
- Raw dream seed `links` should be benign strings only; object-valued links can launder `provenance`, `proof`, and `verified_by` claims into the ledger.

Recommended regression bundle after each patch:

```bash
node --test tools/tests/alpha-dream-pipeline.test.mjs tools/tests/dream-seed-ledger.test.mjs tools/tests/gemira-dispatch.test.mjs tools/tests/aoms-pi-delegation-schema.test.mjs
node --test tools/tests/alpha-dream-pipeline.test.mjs tools/tests/alpha-dreamer-leakage-checker.test.mjs tools/tests/dream-seed-ledger.test.mjs tools/tests/gemira-dispatch.test.mjs tools/tests/pi-worker-spec-contract.test.mjs tools/tests/aoms-pi-delegation-schema.test.mjs tools/tests/aoms-execution-card-validator.test.mjs tools/tests/aoms-membrane-gate-contract.test.mjs tools/tests/aoms-membrane-integration-fixture.test.mjs tools/tests/aoms-dry-run-full-loop.test.mjs tools/tests/aoms-worker-launch-envelope.test.mjs tools/tests/aoms-dry-dispatcher-wrapper.test.mjs tools/tests/aoms-dry-run-handoff.test.mjs tools/tests/aoms-dry-run-trace-custody.test.mjs tests/aoms-atomic-claims.test.mjs
node --test tools/tests/*aoms*.test.mjs tests/aoms-atomic-claims.test.mjs
```
