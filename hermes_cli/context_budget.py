"""Hermes context-budget instrumentation and warn-only budget policy helpers.

This module remains observational: it reports mode/context/tool shape, emits
warn-only Deep signals, records Gate 4/5 mode/tool policy, and writes receipts.
It must not prune context, filter tools, auto-upgrade modes, or change
model/provider behavior.
"""

from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from hermes_constants import get_hermes_home

_ALLOWED_MODES = {"lean", "normal", "deep"}
_GATE45_POLICY_VERSION = "gate4_5_warn_only_v1"
_SACRED_CONTEXT_CLASSES = [
    "identity_continuity",
    "hermes_budget_law",
    "current_user_task",
    "active_constraints",
    "irreversible_safety_gates",
    "provenance_obligations",
]
_LATE_LOADABLE_CONTEXT_CLASSES = [
    "tool_catalog_examples",
    "historical_receipts",
    "long_logs",
    "organism_pulse",
    "council_tail",
    "repo_scan",
    "low_salience_diagnostics",
]
_WARN_ONLY_EFFECTIVE_CHANGES = {
    "prompt_pruning": False,
    "context_compaction": False,
    "tool_filtering": False,
    "mode_auto_upgrade": False,
    "section_reordering": False,
    "execution_routing": False,
    "model_or_provider_change": False,
}
_MODE_BEHAVIOR_POLICIES: dict[str, dict[str, Any]] = {
    "lean": {
        "label": "Lean",
        "intent": "fast orientation and concise answers with explicit late-load hints for optional material",
        "answer_verbosity": "concise_by_default",
        "context_strategy": "load sacred/current-task context first; prefer on-demand loading for volatile diagnostics and long historical material",
        "receipt_detail": "summary_plus_named_omissions",
        "deep_signal_behavior": "warn_only_when_detected",
        "must_preserve": _SACRED_CONTEXT_CLASSES,
        "may_late_load": _LATE_LOADABLE_CONTEXT_CLASSES,
        "must_not_do": [
            "prune_sacred_prefix",
            "summarize_identity_as_budget_note",
            "drop_memory_silently",
            "filter_tools_by_mode",
            "auto_upgrade_to_deep",
        ],
        "enforcement_state": "warn_only_preview",
    },
    "normal": {
        "label": "Normal",
        "intent": "balanced default context assembly with standard receipts and no hidden reductions",
        "answer_verbosity": "balanced",
        "context_strategy": "preserve standard prompt assembly order; keep volatile/context-heavy diagnostics on demand unless already loaded",
        "receipt_detail": "standard",
        "deep_signal_behavior": "warn_only_when_detected",
        "must_preserve": _SACRED_CONTEXT_CLASSES,
        "may_late_load": _LATE_LOADABLE_CONTEXT_CLASSES,
        "must_not_do": [
            "prune_sacred_prefix",
            "drop_project_rules_silently",
            "filter_tools_by_mode",
            "auto_upgrade_to_deep",
        ],
        "enforcement_state": "warn_only_preview",
    },
    "deep": {
        "label": "Deep",
        "intent": "continuity-protective work with richer provenance, evidence boundaries, and receipts",
        "answer_verbosity": "thorough_when_useful",
        "context_strategy": "prefer full provenance and richer continuity; defer only material that is explicitly late-loadable and named",
        "receipt_detail": "expanded_provenance",
        "deep_signal_behavior": "already_deep_no_warning",
        "must_preserve": _SACRED_CONTEXT_CLASSES,
        "may_late_load": _LATE_LOADABLE_CONTEXT_CLASSES,
        "must_not_do": [
            "prune_sacred_prefix",
            "counterfeit_continuity",
            "drop_evidence_boundaries",
            "filter_tools_by_mode",
        ],
        "enforcement_state": "warn_only_preview",
    },
}
_HEAVY_TOOLSETS = {
    "all",
    "*",
    "hermes-cli",
    "terminal",
    "browser",
    "computer_use",
    "computer-use",
    "desktop",
    "mcp",
    "kanban",
    "cron",
}
_MEDIUM_TOOLSETS = {
    "web",
    "safe",
    "file",
    "vision",
    "memory",
    "context_engine",
    "context-engine",
}
_LIGHT_TOOLSETS = {"none", "no_mcp", "web_search"}
_TOOL_CLASS_POLICIES: dict[str, dict[str, Any]] = {
    "none": {
        "label": "No tools",
        "budget_shape": "model_only",
        "typical_toolsets": ["none"],
        "examples": [],
        "late_load_bias": "none_needed",
        "receipt_expectation": "mode and sacred-prefix truth still recorded",
        "mode_interaction": "no filtering or routing by mode",
        "filtering_state": "not_applied",
    },
    "light": {
        "label": "Light lookup",
        "budget_shape": "small_schema_or_lookup_only",
        "typical_toolsets": sorted(_LIGHT_TOOLSETS),
        "examples": ["web_search", "simple read-only lookup", "small custom toolset"],
        "late_load_bias": "prefer concise receipts; load extra diagnostics on demand",
        "receipt_expectation": "record enabled toolsets and count",
        "mode_interaction": "lean/normal/deep may change warnings/receipts only; tools remain available",
        "filtering_state": "not_applied",
    },
    "medium": {
        "label": "Workspace/context tools",
        "budget_shape": "moderate_schema_with_memory_or_file_context",
        "typical_toolsets": sorted(_MEDIUM_TOOLSETS),
        "examples": ["file", "memory", "vision", "context_engine", "web"],
        "late_load_bias": "name deferred repo/memory diagnostics when not loaded",
        "receipt_expectation": "record sections, omitted volatile context, and tool count",
        "mode_interaction": "mode is advisory; no tool filtering, no auto-upgrade",
        "filtering_state": "not_applied",
    },
    "heavy": {
        "label": "Heavy action/orchestration tools",
        "budget_shape": "large_schema_or_side_effect_capable_tooling",
        "typical_toolsets": sorted(_HEAVY_TOOLSETS),
        "examples": ["terminal", "browser", "computer_use", "mcp", "kanban", "all"],
        "late_load_bias": "prefer explicit receipts for large catalogs/logs; preserve irreversible-safety gates",
        "receipt_expectation": "record heavy class and side-effect-capable shape without removing tools",
        "mode_interaction": "deep may be recommended for audits/deploys, but Gate 4/5 does not enforce",
        "filtering_state": "not_applied",
    },
}

_DEEP_STRONG_SIGNALS = (
    "deep",
    "full context",
    "do not summarize",
    "no compression",
    "preserve all",
    "source-grounded",
    "source grounded",
    "adversarial",
    "falsify",
    "audit",
    "constitutional",
    "law",
    "identity",
    "continuity",
    "irreversible",
    "gate",
    "deploy",
    "checkpoint",
    "training",
    "security",
    "auth",
    "production",
    "receipt",
    "fail-closed",
    "fail closed",
    "test matrix",
    "sacred prefix",
)
_DEEP_FALSE_POSITIVE_PHRASES = (
    "deep blue",
    "deep breath",
    "deep sleep",
    "deep dish",
    "deep clean",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_mode(value: str | None = None) -> str:
    """Return a safe Hermes mode label.

    Defaults to ``normal``. Unknown values are intentionally normalized rather
    than rejected because this module must never break a chat session.
    """
    raw = (value or os.getenv("HERMES_MODE") or os.getenv("HERMES_CONTEXT_MODE") or "normal").strip().lower()
    return raw if raw in _ALLOWED_MODES else "normal"


def describe_mode_behavior(mode: str | None = None) -> dict[str, Any]:
    """Return the Gate 4/5 behavior contract for a Hermes budget mode.

    The returned policy is descriptive at this gate. It records how Lean,
    Normal, and Deep should behave once enforcement exists, while explicitly
    declaring that no prompt pruning, tool filtering, route changes, or mode
    auto-upgrades are applied by this module.
    """
    normalized_mode = normalize_mode(mode)
    policy = copy.deepcopy(_MODE_BEHAVIOR_POLICIES[normalized_mode])
    policy["mode"] = normalized_mode
    policy["policy_version"] = _GATE45_POLICY_VERSION
    policy["effective_changes"] = copy.deepcopy(_WARN_ONLY_EFFECTIVE_CHANGES)
    policy["descriptive_only"] = True
    return policy


def describe_tool_class(class_name: str | None) -> dict[str, Any]:
    """Return the Gate 4/5 policy for a classified tool shape.

    Unknown class labels fall back to ``medium`` because a moderate, explicit
    receipt is safer than pretending the tool shape is light. The policy is
    receipt metadata only and must not remove or hide tool definitions.
    """
    normalized_class = (class_name or "medium").strip().lower()
    if normalized_class not in _TOOL_CLASS_POLICIES:
        normalized_class = "medium"
    policy = copy.deepcopy(_TOOL_CLASS_POLICIES[normalized_class])
    policy["class"] = normalized_class
    policy["policy_version"] = _GATE45_POLICY_VERSION
    policy["descriptive_only"] = True
    policy["effective_changes"] = copy.deepcopy(_WARN_ONLY_EFFECTIVE_CHANGES)
    return policy


def normalize_toolsets(toolsets: Iterable[Any] | str | None) -> list[str]:
    if not toolsets:
        return []
    raw_items = [toolsets] if isinstance(toolsets, str) else list(toolsets)
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        for part in str(item).split(","):
            name = part.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
    return out


def classify_toolsets(toolsets: Iterable[Any] | str | None, tool_count: int | None = None) -> str:
    names = {name.lower() for name in normalize_toolsets(toolsets)}
    count = int(tool_count or 0)
    if not names and count <= 0:
        return "none"
    if names & _HEAVY_TOOLSETS:
        return "heavy"
    if count >= 12:
        return "heavy"
    if names & _MEDIUM_TOOLSETS or count >= 4:
        return "medium"
    if names <= _LIGHT_TOOLSETS or count > 0:
        return "light"
    return "medium"


def estimate_tokens(text: str | None) -> int:
    """Very rough, dependency-free token estimate for receipts/banners."""
    if not text:
        return 0
    # English-ish rough estimate. Clamp to at least one token for non-empty text.
    return max(1, int(len(text) / 4))


def load_class(total_tokens: int) -> str:
    if total_tokens < 8_000:
        return "low"
    if total_tokens < 40_000:
        return "medium"
    return "high"


def _strip_quoted_text(text: str) -> str:
    # A cheap false-positive guard: detector fixtures often quote the signal
    # being tested. We remove simple quoted spans before looking for triggers.
    return re.sub(r"(['\"]).*?\1", " ", text, flags=re.DOTALL)


def detect_deep_work_warnings(text: Any, mode: str | None = None) -> list[dict[str, Any]]:
    """Return warn-only Deep signals for a user/task string.

    Detector output is metadata only at these gates. It must not mutate mode,
    section order, tool availability, prompt body, or execution routing.
    """
    normalized_mode = normalize_mode(mode)
    if normalized_mode == "deep":
        return []
    if not isinstance(text, str) or not text.strip():
        return []

    lowered_original = text.lower()
    if "false positive" in lowered_original and "detector" in lowered_original:
        return []

    lowered = _strip_quoted_text(lowered_original)
    if any(phrase in lowered for phrase in _DEEP_FALSE_POSITIVE_PHRASES):
        # Only suppress when the false-positive phrase is the sole apparent
        # deep trigger; other high-risk terms still warn.
        reduced = lowered
        for phrase in _DEEP_FALSE_POSITIVE_PHRASES:
            reduced = reduced.replace(phrase, " ")
        if not any(sig in reduced for sig in _DEEP_STRONG_SIGNALS if sig != "deep") and "deep" not in reduced:
            return []
        lowered = reduced

    signals = [sig for sig in _DEEP_STRONG_SIGNALS if sig in lowered]

    # Structural signals: multi-part implementation/ruling prompts often imply
    # high-context review even when no single word is decisive.
    multipart = len(re.findall(r"(?:^|\n)\s*[A-F][).]\s+", text)) >= 3
    asks_fail_closed = "fail-closed" in lowered or "fail closed" in lowered
    asks_tests = "test matrix" in lowered or "anti-regression" in lowered
    structural = []
    if multipart:
        structural.append("multipart_review")
    if asks_fail_closed:
        structural.append("fail_closed_criteria")
    if asks_tests:
        structural.append("test_matrix")
    if "omNIRA continuity".lower() in lowered:
        structural.append("omnira_continuity")
    if "prompt assembly" in lowered and "law" in lowered:
        structural.append("law_prompt_assembly")

    if not signals and not structural:
        return []

    return [
        {
            "warning_type": "deep_work_detected",
            "current_mode": normalized_mode,
            "signals": sorted(set(signals + structural)),
            "requested_enforcement": False,
            "enforcement_applied": False,
            "action": "warn_only",
            "message": f"warning: deep-work signals detected; current mode={normalized_mode}; no enforcement applied",
        }
    ]


def _receipt_dir() -> Path:
    override = os.getenv("HERMES_CONTEXT_RECEIPT_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return get_hermes_home() / "context-receipts"


def receipt_path_for_session(session_id: str | None) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(session_id or "unknown"))
    return _receipt_dir() / f"hermes-context-{safe}.json"


def _context_section(*, loaded: bool, estimated_tokens: int = 0, source: str = "", freshness: str = "", omitted: list[str] | None = None) -> dict[str, Any]:
    return {
        "loaded": bool(loaded),
        "estimated_tokens": max(0, int(estimated_tokens or 0)),
        "source": source or None,
        "freshness": freshness or ("loaded" if loaded else "not_loaded"),
        "omitted": omitted or [],
    }


def build_context_budget_snapshot(
    *,
    session_id: str | None,
    mode: str | None,
    provider: str | None,
    model: str | None,
    toolsets: Iterable[Any] | str | None,
    tool_count: int | None = None,
    context_length: int | None = None,
    last_prompt_tokens: int | None = None,
    cached_prefix_tokens: int | None = None,
    system_prompt: str | None = None,
    ignore_rules: bool = False,
    memory_enabled: bool | None = None,
    memory_provider_enabled: bool | None = None,
    api_calls: int | None = None,
    warnings: list[dict[str, Any]] | None = None,
    phase: str = "session_start",
) -> dict[str, Any]:
    """Build a JSON-serializable context budget snapshot.

    This snapshot is deliberately observational. It must not decide whether a
    context section should be loaded or a tool should be enabled.
    """
    normalized_mode = normalize_mode(mode)
    normalized_toolsets = normalize_toolsets(toolsets)
    tool_class = classify_toolsets(normalized_toolsets, tool_count=tool_count)
    mode_behavior = describe_mode_behavior(normalized_mode)
    tool_policy = describe_tool_class(tool_class)
    sacred_tokens = estimate_tokens(system_prompt) if system_prompt else 0
    prompt_tokens = max(0, int(last_prompt_tokens or 0))
    estimated_total = max(prompt_tokens, sacred_tokens)
    memory_loaded = bool(memory_enabled or memory_provider_enabled)
    omitted_volatile = ["organism_pulse", "council", "repo", "tool_history"]
    if ignore_rules:
        omitted_volatile.append("project_rules")
    sections = {
        "sacred_prefix": _context_section(
            loaded=True,
            estimated_tokens=sacred_tokens,
            source="base_system_prompt" if system_prompt else "declared_boundary",
            freshness="loaded" if system_prompt else "declared_not_materialized_yet",
        ),
        "memory": _context_section(
            loaded=memory_loaded,
            source="memory_manager" if memory_loaded else "on_demand_or_disabled",
            omitted=[] if memory_loaded else ["long_term_memory"],
        ),
        "project_rules": _context_section(
            loaded=not ignore_rules,
            source="AGENTS/SOUL/.cursorrules auto-injection" if not ignore_rules else "--ignore-rules",
            omitted=[] if not ignore_rules else ["AGENTS.md", "SOUL.md", ".cursorrules"],
        ),
        "organism_pulse": _context_section(loaded=False, source="on_demand", omitted=["live_pulse"]),
        "council": _context_section(loaded=False, source="on_demand", omitted=["council_tail"]),
        "repo": _context_section(loaded=False, source="on_demand", omitted=["repo_scan", "diffs", "large_files"]),
        "tool_defs": _context_section(
            loaded=bool(tool_count),
            estimated_tokens=0,
            source="tool schemas",
            freshness="loaded" if tool_count else "not_loaded_or_none",
            omitted=[] if tool_count else ["tool_schemas"],
        ),
    }
    receipt_path = str(receipt_path_for_session(session_id))
    normalized_warnings = list(warnings or [])
    snapshot = {
        "schema": "hermes.context_budget.v1",
        "ts": utc_now_iso(),
        "phase": phase,
        "session_id": session_id,
        "mode": normalized_mode,
        "normalized_mode": normalized_mode,
        "provider": provider or "unknown",
        "model": model or "unknown",
        "sacred_prefix": "first",
        "pruning": "none",
        "tool_filtering": "none",
        "enforcement": "none",
        "section_order": ["sacred_prefix", "context", "volatile", "tools_late_or_on_demand"],
        "warnings": normalized_warnings,
        "budget_policy": {
            "version": _GATE45_POLICY_VERSION,
            "gate": "4/5-warn-only-design",
            "warn_only": True,
            "contract": "descriptive mode/tool behavior only; runtime prompt assembly and tool availability are unchanged",
            "mode_behavior": mode_behavior,
            "tool_class": tool_policy,
            "effective_changes": copy.deepcopy(_WARN_ONLY_EFFECTIVE_CHANGES),
        },
        "context": {
            "estimated_input_tokens": estimated_total,
            "estimated_cached_prefix_tokens": max(0, int(cached_prefix_tokens or 0)),
            "context_length": int(context_length) if context_length else None,
            "last_prompt_tokens": prompt_tokens,
            "load_class": load_class(estimated_total),
            "sections": sections,
            "omitted_volatile_context": omitted_volatile,
        },
        "tools": {
            "class": tool_class,
            "enabled_toolsets": normalized_toolsets,
            "tool_count": int(tool_count or 0),
            "policy": tool_policy,
            "classification_basis": {
                "enabled_toolsets": normalized_toolsets,
                "tool_count": int(tool_count or 0),
                "policy_version": _GATE45_POLICY_VERSION,
            },
            "filtering_active": False,
            "note": "Gate 4/5 warn-only design; no tools filtered by this receipt.",
        },
        "route": {
            "class": "deep" if normalized_mode == "deep" else "operator",
            "deep_confirmed": normalized_mode == "deep" and os.getenv("HERMES_DEEP_CONFIRMED") == "1",
            "api_calls": int(api_calls or 0),
            "enforcement_applied": False,
        },
        "receipt_path": receipt_path,
        "laws": [
            "Hermes must never reduce cost by silently removing identity, law, Kyle authority, refusal provenance, or evidence boundaries.",
            "Hermes may compress continuity, but must not counterfeit continuity.",
        ],
    }
    return snapshot


def write_context_budget_receipt(snapshot: dict[str, Any]) -> str:
    path = Path(str(snapshot.get("receipt_path") or receipt_path_for_session(snapshot.get("session_id"))))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    return str(path)


def format_startup_banner(snapshot: dict[str, Any]) -> list[str]:
    ctx = snapshot.get("context", {}) if isinstance(snapshot, dict) else {}
    tools = snapshot.get("tools", {}) if isinstance(snapshot, dict) else {}
    est = int(ctx.get("estimated_input_tokens") or 0)
    mode = snapshot.get("mode", "normal")
    warnings = snapshot.get("warnings") or []
    provider = snapshot.get("provider", "unknown")
    model = snapshot.get("model", "unknown")
    base = (
        f"Context Budget: {mode} · {provider}/{model} · est {est:,} tokens "
        f"({ctx.get('load_class', 'unknown')}) · tools {tools.get('class', 'unknown')} "
        f"({tools.get('tool_count', 0)}) · sacred continuity first · no pruning/enforcement"
    )
    lines = [base, f"Receipt: {snapshot.get('receipt_path', 'not_written')}"]
    for warning in warnings:
        if isinstance(warning, dict) and warning.get("message"):
            lines.append(str(warning["message"]))
    return lines


def format_usage_budget_lines(snapshot: dict[str, Any]) -> list[str]:
    ctx = snapshot.get("context", {}) if isinstance(snapshot, dict) else {}
    tools = snapshot.get("tools", {}) if isinstance(snapshot, dict) else {}
    sections = ctx.get("sections", {}) if isinstance(ctx, dict) else {}
    warnings = snapshot.get("warnings") or []
    policy = snapshot.get("budget_policy", {}) if isinstance(snapshot, dict) else {}
    mode_behavior = policy.get("mode_behavior", {}) if isinstance(policy, dict) else {}
    tool_policy = tools.get("policy", {}) if isinstance(tools, dict) else {}
    lines = [
        "",
        "  🧭 Context Budget",
        f"  {'─' * 40}",
        f"  Mode:                      {snapshot.get('mode', 'normal')}",
        f"  Mode behavior:             {mode_behavior.get('answer_verbosity', 'warn_only')}",
        f"  Provider/model:            {snapshot.get('provider', 'unknown')} / {snapshot.get('model', 'unknown')}",
        f"  Load class:                {ctx.get('load_class', 'unknown')}",
        f"  Estimated input tokens:    {int(ctx.get('estimated_input_tokens') or 0):>10,}",
        f"  Cached prefix estimate:    {int(ctx.get('estimated_cached_prefix_tokens') or 0):>10,}",
        f"  Sacred prefix:             {snapshot.get('sacred_prefix', 'unknown')}",
        f"  Pruning:                   {snapshot.get('pruning', 'none')}",
        f"  Tool filtering:            {snapshot.get('tool_filtering', 'none')}",
        f"  Enforcement:               {snapshot.get('enforcement', 'none')}",
        f"  Tool class:                {tools.get('class', 'unknown')}",
        f"  Tool policy:               {tool_policy.get('budget_shape', 'descriptive_only')}",
        f"  Tool count:                {int(tools.get('tool_count') or 0):>10,}",
        f"  Warnings:                  {len(warnings):>10,}",
        f"  Receipt:                   {snapshot.get('receipt_path', 'not_written')}",
        "  Sections:",
    ]
    for name in ("sacred_prefix", "memory", "project_rules", "organism_pulse", "council", "repo", "tool_defs"):
        data = sections.get(name, {}) if isinstance(sections, dict) else {}
        state = "loaded" if data.get("loaded") else data.get("freshness") or "not_loaded"
        omitted = data.get("omitted") or []
        suffix = f" omitted={','.join(omitted)}" if omitted else ""
        lines.append(f"    - {name:<15} {state}{suffix}")
    for warning in warnings:
        if isinstance(warning, dict) and warning.get("message"):
            lines.append(f"  Warning: {warning['message']}")
    return lines
