# Hermes Budget Gate 4/5 Design

Gate 4/5 defines the budget-mode and tool-class vocabulary that later gates may enforce. This gate is still warn-only: it records intended behavior in receipts, but does not prune prompts, compact continuity, filter tools, route execution, or change provider/model selection.

## Invariants

- Sacred identity/continuity remains the first semantic prompt block.
- Hermes Budget Law remains second, before help/tools/context/memory.
- Budget mode is an intent signal, not authority to forget.
- Any deferred material must be named in a receipt or visible diagnostic.
- Tool classes describe budget shape only. They do not remove tools.
- Receipts must keep saying `pruning: none`, `tool_filtering: none`, and `enforcement: none` until enforcement exists.

## Modes

| Mode | Intent | Context behavior | Deep-work signal | Receipt level |
| --- | --- | --- | --- | --- |
| `lean` | Fast orientation and concise answers. | Load sacred/current-task context first; prefer on-demand loading for volatile diagnostics, long logs, historical receipts, and broad repo scans. | Warn only if deep/audit/law/continuity/test-matrix signals appear. | Summary plus named omissions. |
| `normal` | Balanced default. | Preserve current assembly order; keep heavyweight diagnostics on demand unless already loaded. | Warn only if deep signals appear. | Standard. |
| `deep` | Continuity-protective, provenance-rich work. | Prefer richer continuity, evidence boundaries, and full provenance. Defer only explicit late-loadable classes and name them. | No detector warning because the user already selected deep. | Expanded provenance. |

All modes must preserve: identity continuity, Hermes Budget Law, current user task, active constraints, irreversible-safety gates, and provenance obligations.

Late-loadable classes are: tool catalog examples, historical receipts, long logs, organism pulse, council tail, repo scans, and low-salience diagnostics.

## Tool classes

| Class | Shape | Examples | Gate 4/5 behavior |
| --- | --- | --- | --- |
| `none` | No tools / model-only. | `none` | Receipt still records mode and sacred-prefix truth. |
| `light` | Small schema or lookup-only. | `web_search`, `no_mcp`, tiny custom toolsets. | Prefer concise receipts and on-demand diagnostics. |
| `medium` | Workspace/context tools. | `file`, `memory`, `vision`, `context_engine`, `web`. | Record sections, omitted volatile context, and count. |
| `heavy` | Large schema or side-effect-capable tools. | `terminal`, `browser`, `computer_use`, `mcp`, `kanban`, `cron`, `all`, or 12+ tools. | Record heavy shape and safety relevance without removing tools. |

Classification is descriptive. A heavy class may recommend deep mode in a future gate, but Gate 4/5 only records the shape and emits warnings when the user asks for deep work in a lower mode.

## Receipt fields added

Gate 4/5 receipts add `budget_policy`:

- `version: gate4_5_warn_only_v1`
- `gate: 4/5-warn-only-design`
- `mode_behavior`: the normalized Lean/Normal/Deep behavior contract
- `tool_class`: the active tool-class contract
- `effective_changes`: all false for prompt pruning, context compaction, tool filtering, mode auto-upgrade, section reordering, execution routing, and model/provider change

The existing truth fields remain unchanged: `sacred_prefix: first`, `pruning: none`, `tool_filtering: none`, `enforcement: none`.
