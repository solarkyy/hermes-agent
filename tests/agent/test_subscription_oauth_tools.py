"""Tests for subscription OAuth tool naming (Hermes ↔ Claude Code / Pi)."""

from __future__ import annotations

from agent.subscription_oauth_tools import (
    from_subscription_oauth_tool_name,
    to_subscription_oauth_tool_name,
    trim_subscription_oauth_tools,
    wire_subscription_oauth_tools,
    SUBSCRIPTION_OAUTH_MAX_TOOLS,
)


class _FakeRegistry:
    def __init__(self, names: set[str]):
        self._names = names

    def get_entry(self, name: str):
        if name in self._names:
            return object()
        return None


class TestToSubscriptionOAuthToolName:
    def test_maps_hermes_builtins_to_claude_code(self):
        assert to_subscription_oauth_tool_name("web_search") == "WebSearch"
        assert to_subscription_oauth_tool_name("read_file") == "Read"
        assert to_subscription_oauth_tool_name("terminal") == "Bash"

    def test_keeps_unmapped_native_names(self):
        assert to_subscription_oauth_tool_name("vision_analyze") == "vision_analyze"
        assert to_subscription_oauth_tool_name("image_generate") == "image_generate"

    def test_keeps_native_mcp_server_tools(self):
        name = "mcp_composio_COMPOSIO_SEARCH_TOOLS"
        assert to_subscription_oauth_tool_name(name) == name

    def test_never_adds_mcp_prefix_to_bare_tools(self):
        assert not to_subscription_oauth_tool_name("web_search").startswith("mcp_")


class TestFromSubscriptionOAuthToolName:
    def test_reverses_claude_code_alias(self):
        reg = _FakeRegistry({"web_search", "read_file"})
        assert from_subscription_oauth_tool_name("WebSearch", reg) == "web_search"
        assert from_subscription_oauth_tool_name("Read", reg) == "read_file"

    def test_keeps_native_mcp_tool(self):
        reg = _FakeRegistry({"mcp_composio_SEARCH"})
        assert from_subscription_oauth_tool_name("mcp_composio_SEARCH", reg) == "mcp_composio_SEARCH"

    def test_legacy_mcp_strip_for_oauth_injected_tools(self):
        reg = _FakeRegistry({"read_file"})
        assert from_subscription_oauth_tool_name("mcp_read_file", reg) == "read_file"

    def test_prefers_full_name_when_both_registered(self):
        reg = _FakeRegistry({"foo", "mcp_foo"})
        assert from_subscription_oauth_tool_name("mcp_foo", reg) == "mcp_foo"


class TestWireSubscriptionOAuthTools:
    def test_rewrites_tool_list_in_place(self):
        tools = [
            {"name": "web_search", "description": "x", "input_schema": {}},
            {"name": "mcp_composio_SEARCH", "description": "y", "input_schema": {}},
            {"name": "vision_analyze", "description": "z", "input_schema": {}},
        ]
        out = wire_subscription_oauth_tools(tools)
        assert [t["name"] for t in out] == [
            "WebSearch",
            "mcp_composio_SEARCH",
            "vision_analyze",
        ]


class TestTrimSubscriptionOAuthTools:
    def test_keeps_priority_tools_under_cap(self):
        tools = [{"name": f"tool_{i}", "input_schema": {}} for i in range(30)]
        tools.extend([
            {"name": "web_search", "input_schema": {}},
            {"name": "terminal", "input_schema": {}},
            {"name": "read_file", "input_schema": {}},
        ])
        kept = trim_subscription_oauth_tools(tools, max_tools=22)
        assert len(kept) == 22
        names = {t["name"] for t in kept}
        assert "web_search" in names
        assert "terminal" in names
        assert "read_file" in names

    def test_wire_omits_skill_tools_on_oauth(self):
        tools = [
            {"name": "web_search", "description": "x", "input_schema": {}},
            {"name": "skills_list", "description": "y", "input_schema": {}},
            {"name": "skill_view", "description": "z", "input_schema": {}},
        ]
        out = wire_subscription_oauth_tools(tools)
        assert [t["name"] for t in out] == ["WebSearch"]
