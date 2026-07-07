"""Tests for Anthropic subscription-OAuth tool-name round-trip.

Local OMNIRA policy mirrors Pi / Claude Code for subscription OAuth: mapped
Hermes builtins use Claude Code canonical names (Read/Bash/WebSearch), while
unmapped and native MCP tools keep their registry names. The response side also
keeps compatibility with Hermes' newer ``mcp__`` wire names.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


def _make_tool_use_block(name: str, block_id: str = "tc_1", input_data: dict | None = None):
    return SimpleNamespace(
        type="tool_use",
        id=block_id,
        name=name,
        input=input_data or {"query": "test"},
    )


def _make_response(*blocks, stop_reason="end_turn"):
    return SimpleNamespace(
        content=list(blocks),
        stop_reason=stop_reason,
        model="claude-sonnet-4",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )


class _FakeRegistry:
    def __init__(self, registered_names: set[str]):
        self._names = registered_names

    def get_entry(self, name: str):
        if name in self._names:
            return SimpleNamespace(name=name)
        return None


class TestAnthropicSubscriptionOauthResponseNames:
    def _get_transport(self):
        from agent.transports.anthropic import AnthropicTransport
        return AnthropicTransport()

    def test_reverses_claude_code_alias(self):
        transport = self._get_transport()
        response = _make_response(_make_tool_use_block("Read"))
        registry = _FakeRegistry({"read_file", "terminal", "web_search"})
        with patch("tools.registry.registry", registry):
            result = transport.normalize_response(response, strip_tool_prefix=True)
        assert result.tool_calls[0].name == "read_file"

    def test_reverses_legacy_double_mcp_native_tool(self):
        transport = self._get_transport()
        response = _make_response(_make_tool_use_block("mcp__read_file"))
        registry = _FakeRegistry({"read_file", "terminal", "web_search"})
        with patch("tools.registry.registry", registry):
            result = transport.normalize_response(response, strip_tool_prefix=True)
        assert result.tool_calls[0].name == "read_file"

    def test_reverses_legacy_double_mcp_server_tool(self):
        transport = self._get_transport()
        response = _make_response(_make_tool_use_block("mcp__linear_get_issue"))
        registry = _FakeRegistry({"mcp_linear_get_issue", "read_file"})
        with patch("tools.registry.registry", registry):
            result = transport.normalize_response(response, strip_tool_prefix=True)
        assert result.tool_calls[0].name == "mcp_linear_get_issue"

    def test_no_strip_when_flag_false(self):
        transport = self._get_transport()
        response = _make_response(_make_tool_use_block("Read"))
        registry = _FakeRegistry({"read_file"})
        with patch("tools.registry.registry", registry):
            result = transport.normalize_response(response, strip_tool_prefix=False)
        assert result.tool_calls[0].name == "Read"

    def test_preserves_directly_registered_wire_name(self):
        transport = self._get_transport()
        response = _make_response(_make_tool_use_block("mcp__foo"))
        registry = _FakeRegistry({"foo", "mcp__foo"})
        with patch("tools.registry.registry", registry):
            result = transport.normalize_response(response, strip_tool_prefix=True)
        assert result.tool_calls[0].name == "mcp__foo"


class TestAnthropicSubscriptionOauthOutgoingNames:
    def _build(self, tools, is_oauth=True):
        from agent.anthropic_adapter import build_anthropic_kwargs
        return build_anthropic_kwargs(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": "Hi"}],
            tools=tools,
            max_tokens=4096,
            reasoning_config=None,
            is_oauth=is_oauth,
        )

    def test_oauth_maps_core_tools_to_claude_code_names(self):
        kwargs = self._build([
            {"type": "function", "function": {"name": "read_file", "description": "x", "parameters": {}}},
            {"type": "function", "function": {"name": "terminal", "description": "y", "parameters": {}}},
            {"type": "function", "function": {"name": "web_search", "description": "z", "parameters": {}}},
        ])
        assert [t["name"] for t in kwargs["tools"]] == ["Read", "Bash", "WebSearch"]

    def test_oauth_keeps_unmapped_and_native_mcp_names(self):
        kwargs = self._build([
            {"type": "function", "function": {"name": "vision_analyze", "description": "x", "parameters": {}}},
            {"type": "function", "function": {"name": "mcp_linear_get_issue", "description": "y", "parameters": {}}},
        ])
        names = [t["name"] for t in kwargs["tools"]]
        assert names == ["vision_analyze", "mcp_linear_get_issue"]

    def test_oauth_mixed_native_and_bare_tools(self):
        kwargs = self._build([
            {"type": "function", "function": {"name": "read_file", "description": "x", "parameters": {}}},
            {"type": "function", "function": {"name": "mcp_linear_get_issue", "description": "y", "parameters": {}}},
            {"type": "function", "function": {"name": "terminal", "description": "z", "parameters": {}}},
        ])
        assert sorted(t["name"] for t in kwargs["tools"]) == ["Bash", "Read", "mcp_linear_get_issue"]

    def test_non_oauth_path_untouched(self):
        kwargs = self._build([
            {"type": "function", "function": {"name": "read_file", "description": "x", "parameters": {}}},
            {"type": "function", "function": {"name": "mcp_linear_get_issue", "description": "y", "parameters": {}}},
        ], is_oauth=False)
        assert sorted(t["name"] for t in kwargs["tools"]) == ["mcp_linear_get_issue", "read_file"]
