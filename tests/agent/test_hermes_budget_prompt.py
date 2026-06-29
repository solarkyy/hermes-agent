from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from agent.prompt_builder import DEFAULT_AGENT_IDENTITY, HERMES_AGENT_HELP_GUIDANCE, HERMES_BUDGET_LAW_PROMPT
from agent.system_prompt import build_system_prompt


class _MemoryStore:
    def format_for_system_prompt(self, kind: str) -> str:
        if kind == "memory":
            return "MEMORY BLOCK"
        if kind == "user":
            return "USER PROFILE BLOCK"
        return ""


def _make_agent(**overrides):
    base = dict(
        load_soul_identity=False,
        skip_context_files=False,
        valid_tool_names=set(),
        _task_completion_guidance=False,
        _tool_use_enforcement=False,
        _environment_probe=False,
        _kanban_worker_guidance="",
        _memory_store=None,
        _memory_enabled=False,
        _user_profile_enabled=False,
        _memory_manager=None,
        model="test-model",
        provider="test-provider",
        platform="",
        pass_session_id=False,
        session_id="",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_sacred_prefix_identity_then_budget_law_then_help_before_context_and_memory(monkeypatch):
    monkeypatch.delenv("TERMINAL_CWD", raising=False)
    agent = _make_agent(
        _memory_store=_MemoryStore(),
        _memory_enabled=True,
        _user_profile_enabled=True,
    )

    with (
        patch("run_agent.load_soul_md", return_value="SOUL IDENTITY"),
        patch("run_agent.build_nous_subscription_prompt", return_value=""),
        patch("run_agent.build_environment_hints", return_value=""),
        patch("run_agent.build_context_files_prompt", return_value="PROJECT CONTEXT"),
    ):
        prompt = build_system_prompt(agent, system_message="CURRENT TASK LOCK")

    assert prompt.startswith("SOUL IDENTITY\n\n# Hermes Budget Law")
    assert prompt.index("SOUL IDENTITY") < prompt.index(HERMES_BUDGET_LAW_PROMPT)
    assert prompt.index(HERMES_BUDGET_LAW_PROMPT) < prompt.index(HERMES_AGENT_HELP_GUIDANCE)
    assert prompt.index(HERMES_AGENT_HELP_GUIDANCE) < prompt.index("CURRENT TASK LOCK")
    assert prompt.index("CURRENT TASK LOCK") < prompt.index("PROJECT CONTEXT")
    assert prompt.index("PROJECT CONTEXT") < prompt.index("MEMORY BLOCK")
    assert prompt.index("MEMORY BLOCK") < prompt.index("Conversation started:")


def test_default_identity_remains_first_when_soul_missing(monkeypatch):
    monkeypatch.delenv("TERMINAL_CWD", raising=False)
    agent = _make_agent(skip_context_files=True)

    with (
        patch("run_agent.load_soul_md", return_value=""),
        patch("run_agent.build_nous_subscription_prompt", return_value=""),
        patch("run_agent.build_environment_hints", return_value=""),
        patch("run_agent.build_context_files_prompt", return_value="SHOULD NOT LOAD"),
    ):
        prompt = build_system_prompt(agent)

    assert prompt.startswith(DEFAULT_AGENT_IDENTITY)
    assert prompt.index(DEFAULT_AGENT_IDENTITY) < prompt.index(HERMES_BUDGET_LAW_PROMPT)
    assert "SHOULD NOT LOAD" not in prompt
