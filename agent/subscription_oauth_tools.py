"""Subscription OAuth tool naming — Hermes ↔ Claude Code / Pi parity.

Anthropic routes OAuth traffic into different billing lanes depending on how
tools are named on the wire and how many tools are attached:

* **Subscription lane** (same as Pi / Claude Code Max): native Hermes names
  (``web_search``) or Claude Code canonical names (``WebSearch``, ``Bash``),
  with **at most** ``SUBSCRIPTION_OAUTH_MAX_TOOLS`` tools per request.
* **Extra-usage lane** (requires paid credits): any tool whose API name starts
  with ``mcp_`` (unless a registered native MCP server tool), **or** more than
  ~22 tools on a single OAuth request (empirically verified 2026-06-12).

Hermes must never rewrite bare tool names to ``mcp_<tool>``. Pi's pi-ai layer
maps known tools to Claude Code PascalCase via ``toClaudeCodeName``; we mirror
that mapping for overlapping Hermes builtins so Fable/OAuth sees familiar CC
names while dispatch still hits Hermes handlers.

Shared machine-readable spec: ``references/subscription-oauth-tool-names.json``
(omnios sisters can import the same file from ``tools/lib/``).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

_MCP_PREFIX = "mcp_"
_MCP_DOUBLE_PREFIX = "mcp__"

# Anthropic subscription OAuth rejects >22 tools with "out of extra usage" (KjDesk 2026-06-12).
SUBSCRIPTION_OAUTH_MAX_TOOLS = 22

# Never attach these on subscription OAuth — they route to extra-usage billing even
# at low tool counts when the session carries a large system prompt (KjDesk 2026-06-12).
# Skills remain available via slash commands and the injected skills catalog.
_SUBSCRIPTION_OAUTH_EXCLUDED_TOOLS: frozenset[str] = frozenset({
    "skills_list", "skill_view", "skill_manage",
})

# Priority order when trimming. Browser builtins stay snake_case on the wire and
# must rank ahead of CC-mapped core tools — priority that leads with WebSearch/
# Bash/Read triggers extra-usage billing on large OAuth sessions (KjDesk 2026-06-12).
_SUBSCRIPTION_OAUTH_TOOL_PRIORITY: tuple[str, ...] = (
    "browser_navigate", "browser_snapshot", "browser_click",
    "browser_type", "browser_scroll", "browser_back",
    "browser_press", "browser_get_images",
    "browser_vision", "browser_console", "browser_cdp", "browser_dialog",
    "image_generate", "vision_analyze",
    "web_search", "web_extract",
    "terminal", "process",
    "read_file", "write_file", "patch", "search_files",
    "text_to_speech",
    "todo", "memory",
    "session_search",
    "clarify",
    "execute_code", "delegate_task",
    "cronjob",
    "send_message",
    "ha_list_entities", "ha_get_state", "ha_list_services", "ha_call_service",
    "kanban_show", "kanban_list", "kanban_complete", "kanban_block",
    "kanban_heartbeat", "kanban_comment", "kanban_create", "kanban_link",
    "kanban_unblock",
    "computer_use",
)

# Claude Code 2.x tool surface (pi-ai @earendil-works/pi-ai providers/anthropic.js)
CLAUDE_CODE_CANONICAL_TOOLS = frozenset({
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Grep",
    "Glob",
    "AskUserQuestion",
    "EnterPlanMode",
    "ExitPlanMode",
    "KillShell",
    "NotebookEdit",
    "Skill",
    "Task",
    "TaskOutput",
    "TodoWrite",
    "WebFetch",
    "WebSearch",
})

# Hermes builtin → Claude Code wire name (subset with clear semantic parity).
HERMES_TO_CLAUDE_CODE: Dict[str, str] = {
    "read_file": "Read",
    "write_file": "Write",
    "patch": "Edit",
    "terminal": "Bash",
    "process": "KillShell",
    "search_files": "Grep",
    "web_search": "WebSearch",
    "web_extract": "WebFetch",
    "todo": "TodoWrite",
    "delegate_task": "Task",
}

_CLAUDE_CODE_LOWER = {name.lower(): name for name in CLAUDE_CODE_CANONICAL_TOOLS}
_CLAUDE_CODE_TO_HERMES: Dict[str, str] = {
    cc: hermes for hermes, cc in HERMES_TO_CLAUDE_CODE.items()
}


def is_native_mcp_server_tool(name: str) -> bool:
    """True when the registry name is already a native MCP server tool."""
    return bool(name) and name.startswith(_MCP_PREFIX)


def to_subscription_oauth_tool_name(hermes_name: str) -> str:
    """Map a Hermes registry tool name to the OAuth API wire name."""
    if not hermes_name:
        return hermes_name
    if is_native_mcp_server_tool(hermes_name):
        return hermes_name
    return HERMES_TO_CLAUDE_CODE.get(hermes_name, hermes_name)


def from_subscription_oauth_tool_name(
    api_name: str,
    registry: Any,
    *,
    allow_legacy_mcp_strip: bool = True,
) -> str:
    """Resolve an OAuth API tool name back to a Hermes registry name."""
    if not api_name:
        return api_name

    get_entry = getattr(registry, "get_entry", None)
    if callable(get_entry) and get_entry(api_name):
        return api_name

    hermes = _CLAUDE_CODE_TO_HERMES.get(api_name)
    if hermes and get_entry and get_entry(hermes):
        return hermes

    cc_canonical = _CLAUDE_CODE_LOWER.get(api_name.lower())
    if cc_canonical:
        hermes = _CLAUDE_CODE_TO_HERMES.get(cc_canonical)
        if hermes and get_entry and get_entry(hermes):
            return hermes

    if allow_legacy_mcp_strip and api_name.startswith(_MCP_DOUBLE_PREFIX):
        bare = api_name[len(_MCP_DOUBLE_PREFIX):]
        single = _MCP_PREFIX + bare
        if get_entry and get_entry(single):
            return single
        if get_entry and get_entry(bare):
            return bare

    if allow_legacy_mcp_strip and api_name.startswith(_MCP_PREFIX):
        stripped = api_name[len(_MCP_PREFIX):]
        if get_entry and get_entry(stripped) and not get_entry(api_name):
            return stripped

    return api_name


def wire_subscription_oauth_tools(
    anthropic_tools: list[dict],
) -> list[dict]:
    """Rewrite and trim Anthropic tool schemas for subscription OAuth.

    Returns the (possibly shortened) tool list actually sent to Anthropic.
    """
    eligible = [
        t for t in anthropic_tools
        if str(t.get("name") or "") not in _SUBSCRIPTION_OAUTH_EXCLUDED_TOOLS
    ]
    dropped_skill = len(anthropic_tools) - len(eligible)
    if dropped_skill:
        logger.info(
            "Subscription OAuth: omitting %d skill tool(s) from wire "
            "(skills_list/skill_view/skill_manage trigger extra-usage on OAuth). "
            "Use slash commands or an API key for skill tool calls.",
            dropped_skill,
        )
    trimmed = trim_subscription_oauth_tools(eligible)
    for tool in trimmed:
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            continue
        if name.startswith(_MCP_PREFIX + _MCP_PREFIX):
            tool["name"] = name[len(_MCP_PREFIX):]
            name = tool["name"]
        tool["name"] = to_subscription_oauth_tool_name(name)
    return trimmed


def trim_subscription_oauth_tools(
    anthropic_tools: list[dict],
    *,
    max_tools: int = SUBSCRIPTION_OAUTH_MAX_TOOLS,
    priority: Sequence[str] = _SUBSCRIPTION_OAUTH_TOOL_PRIORITY,
) -> list[dict]:
    """Keep the highest-priority tools within the OAuth subscription cap."""
    if len(anthropic_tools) <= max_tools:
        return anthropic_tools

    rank = {name: idx for idx, name in enumerate(priority)}
    default_rank = len(rank) + 1000

    def sort_key(tool: dict) -> tuple[int, int, str]:
        name = str(tool.get("name") or "")
        # Preserve registration order within the same priority band so browser
        # tools keep their natural snake_case cluster on the wire.
        reg_idx = tool.get("_subscription_oauth_reg_idx", 10_000)
        if not isinstance(reg_idx, int):
            reg_idx = 10_000
        return (rank.get(name, default_rank), reg_idx, name)

    indexed = [
        {**tool, "_subscription_oauth_reg_idx": idx}
        for idx, tool in enumerate(anthropic_tools)
    ]
    kept = sorted(indexed, key=sort_key)[:max_tools]
    for tool in kept:
        tool.pop("_subscription_oauth_reg_idx", None)
    kept_names = {t.get("name") for t in kept}
    dropped = [t.get("name") for t in anthropic_tools if t.get("name") not in kept_names]
    logger.warning(
        "Subscription OAuth tool cap: sending %d/%d tools (max %d). "
        "Dropped (enable via smaller toolset or API key): %s",
        len(kept), len(anthropic_tools), max_tools,
        ", ".join(str(n) for n in dropped[:8]) + ("..." if len(dropped) > 8 else ""),
    )
    return kept


def wire_subscription_oauth_message_tools(anthropic_messages: list[dict]) -> None:
    """Rewrite tool_use names in outbound message history for OAuth parity."""
    for msg in anthropic_messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and isinstance(block.get("name"), str):
                block["name"] = to_subscription_oauth_tool_name(block["name"])
