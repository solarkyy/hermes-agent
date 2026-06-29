# Receipt: Hermes Budget Gate 2/3 instrumentation and sacred-prefix review

Date: 2026-06-29

## Status

Recreated after the referenced receipt path was missing during review. This receipt describes the current checked state; it is not evidence of an earlier file that no longer exists.

## Summary

Hermes Budget Gate 2/3 is present as observational context-budget instrumentation plus sacred-prefix ordering.

- `agent/system_prompt.py` places identity/continuity first and `HERMES_BUDGET_LAW_PROMPT` second, before Hermes help guidance, current task context, project context, memory, and volatile session metadata.
- `agent/prompt_builder.py` defines `HERMES_BUDGET_LAW_PROMPT` as prompt law text, not a runtime enforcement gate.
- `hermes_cli/context_budget.py` builds JSON receipts with `sacred_prefix: first`, token/load estimates, loaded/omitted section metadata, tool-shape metadata, and truthful non-enforcement fields.
- `cli.py` writes context-budget receipts during startup/agent initialization/usage/turn completion and emits warn-only Deep-work warnings around user turns.
- `hermes_cli/_parser.py` accepts `--hermes-mode` for `lean`, `normal`, and `deep` as a warn-only mode label.

## Truth fields

- `sacred_prefix: first`
- `pruning: none`
- `tool_filtering: none`
- `enforcement: none`
- no prompt pruning implemented
- no tool filtering implemented
- no mode auto-upgrade implemented
- no provider/model/route change implemented

## Verification

```bash
python -m py_compile hermes_cli/context_budget.py agent/prompt_builder.py agent/system_prompt.py cli.py hermes_cli/_parser.py hermes_cli/main.py hermes_cli/oneshot.py
pytest -q tests/hermes_cli/test_context_budget.py tests/agent/test_hermes_budget_prompt.py tests/agent/test_subscription_oauth_system_prompt.py tests/agent/test_subscription_oauth_tools.py
```

Result: `23 passed, 1 warning`.

## Non-goals

Gate 2/3 does not enforce budget modes, compact memory, remove tools, or prove training/admission readiness for AOM/AOMS. It only records and displays budget context truth and preserves sacred-prefix order.
