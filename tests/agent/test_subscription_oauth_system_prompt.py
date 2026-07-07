"""OAuth system-prompt relocation for subscription billing parity."""

from __future__ import annotations

from agent.anthropic_adapter import (
    _CLAUDE_CODE_SYSTEM_PREFIX,
    build_anthropic_kwargs,
    relocate_subscription_oauth_system_prompt,
)


class TestRelocateSubscriptionOAuthSystemPrompt:
    def test_keeps_only_claude_code_identity_in_system(self):
        system = [
            {"type": "text", "text": _CLAUDE_CODE_SYSTEM_PREFIX},
            {"type": "text", "text": "You are OMNIRA. Full organism context here."},
        ]
        messages = [{"role": "user", "content": "Hello"}]
        kept, out_msgs = relocate_subscription_oauth_system_prompt(system, messages)
        assert kept == [{"type": "text", "text": _CLAUDE_CODE_SYSTEM_PREFIX}]
        assert out_msgs[0]["content"].startswith("You are OMNIRA.")
        assert "Hello" in out_msgs[0]["content"]

    def test_string_system_relocates_to_user(self):
        system = f"{_CLAUDE_CODE_SYSTEM_PREFIX}\n\nExtra instructions."
        messages = [{"role": "user", "content": "Hi"}]
        kept, out_msgs = relocate_subscription_oauth_system_prompt(system, messages)
        assert len(kept) == 1
        assert kept[0]["text"] == _CLAUDE_CODE_SYSTEM_PREFIX
        assert "Extra instructions." in out_msgs[0]["content"]

    def test_build_anthropic_kwargs_oauth_minimal_system(self):
        messages = [
            {"role": "system", "content": "OMNIRA organism brief.\n" * 100},
            {"role": "user", "content": "ping"},
        ]
        kwargs = build_anthropic_kwargs(
            model="claude-fable-5",
            messages=messages,
            tools=None,
            max_tokens=256,
            reasoning_config=None,
            is_oauth=True,
        )
        system = kwargs["system"]
        assert isinstance(system, list)
        assert len(system) == 1
        assert system[0]["text"] == _CLAUDE_CODE_SYSTEM_PREFIX
        user_content = kwargs["messages"][0]["content"]
        assert "OMNIRA organism brief." in user_content
