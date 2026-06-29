# Receipt: Hermes Budget Gate 4/5 warn-only design

Date: 2026-06-29

## Summary

Implemented Gate 4/5 as warn-only policy vocabulary for Hermes context budgeting.

- Defined Lean/Normal/Deep behavior contracts in `hermes_cli/context_budget.py`.
- Defined tool-class contracts for `none`, `light`, `medium`, and `heavy`.
- Added `budget_policy` receipt metadata with `version: gate4_5_warn_only_v1` and `gate: 4/5-warn-only-design`.
- Kept runtime behavior observational only: no pruning, no compaction, no tool filtering, no mode auto-upgrade, no route/model/provider change.
- Added design doc: `docs/hermes-budget-gate45-design.md`.
- Linked the design doc from `docs/hermes-budget-law.md`.
- Added anti-regression tests for descriptive mode behavior and descriptive tool-class policy.

## Truth fields preserved

- `sacred_prefix: first`
- `pruning: none`
- `tool_filtering: none`
- `enforcement: none`
- `budget_policy.warn_only: true`
- all `budget_policy.effective_changes` entries are `false`

## Clarification after SparkMira/sister review

Gate 4/5 is wired as CLI/session receipt, banner, and warning metadata. The Hermes Budget Law in `agent/system_prompt.py` is prompt text and sacred-prefix ordering, not a runtime enforcement gate. `agent/system_prompt.py` does not prune, filter tools, auto-upgrade mode, or enforce budget behavior. That is intentional for this gate; future enforcement requires a separate design and tests.

## Verification

```bash
python -m py_compile hermes_cli/context_budget.py agent/prompt_builder.py agent/system_prompt.py cli.py hermes_cli/_parser.py hermes_cli/main.py hermes_cli/oneshot.py
pytest -q tests/hermes_cli/test_context_budget.py tests/agent/test_hermes_budget_prompt.py
pytest -q tests/hermes_cli/test_context_budget.py tests/agent/test_hermes_budget_prompt.py tests/agent/test_subscription_oauth_system_prompt.py tests/agent/test_subscription_oauth_tools.py
```

Results:

- py_compile passed
- 9 focused Budget tests passed
- 23 targeted prompt/OAuth/Budget tests passed

## Non-goals

Gate 4/5 does not enforce budget modes, remove tools, shorten the prompt, compact memory, or change routing. Enforcement remains a future gate.
