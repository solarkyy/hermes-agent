"""Tests for hermes_guard.py (OMNIRA Immune Guard)"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Since hermes_guard is in the root, it is discoverable
import hermes_guard
from hermes_guard import (
    immune_check,
    scan_messages,
    Classification,
    ImmuneBlockError,
)

class TestImmuneGuard:
    
    def test_clean_message_passes(self):
        """Verify that standard clean messages pass without findings."""
        messages = [
            {"role": "user", "content": "Hello, how do I write a fast sort algorithm in Python?"},
            {"role": "assistant", "content": "You can use Timsort which is built-in via sorted()."}
        ]
        findings = scan_messages(messages)
        assert len(findings["red"]) == 0
        assert len(findings["yellow"]) == 0

        # Run through full immune_check
        passed, reason = immune_check(messages, "openrouter", "deepseek-chat")
        assert passed is True
        assert "no secrets detected" in reason

    def test_red_secrets_detected(self):
        """Verify RED secret patterns are identified."""
        test_cases = [
            ("sk-proj-abc123xyz789ABCDEF012345", "OpenAI API key"),
            ("sk-ant-sid01-abc123xyz789ABCDEF012345", "Anthropic API key"),
            ("ghp_1234567890abcdefghijklmnopqrstuv", "GitHub personal access token"),
            ("-----BEGIN OPENSSH PRIVATE KEY-----\nb2Bl\n-----END OPENSSH PRIVATE KEY-----", "SSH private key"),
            ("postgresql://user:pass@localhost:5432/dbname", "Database connection string"),
        ]

        for secret, desc in test_cases:
            messages = [{"role": "user", "content": f"Here is the credential: {secret}"}]
            findings = scan_messages(messages)
            assert len(findings["red"]) > 0, f"Failed to detect: {desc}"
            assert any(f.description == desc for f in findings["red"])

    def test_yellow_secrets_detected(self):
        """Verify YELLOW secret patterns are identified."""
        test_cases = [
            ("MY_API_SECRET=super_secret_value", "Environment secret assignment"),
            ("192.168.1.50:8080", "Private IP address"),
            ("/home/kylej/Desktop/secret_project", "Home directory path"),
            ("Check the contents of .env.production file.", ".env file reference"),
        ]

        for secret, desc in test_cases:
            messages = [{"role": "user", "content": f"Config data: {secret}"}]
            findings = scan_messages(messages)
            assert len(findings["yellow"]) > 0, f"Failed to detect: {desc}"
            assert any(f.description == desc for f in findings["yellow"])

    def test_local_provider_bypass(self):
        """Verify that local providers bypass scanning entirely."""
        messages = [{"role": "user", "content": "sk-proj-abc123xyz789ABCDEF012345"}]
        
        # Even with RED secrets, local providers should pass immediately
        passed, reason = immune_check(messages, "evo-local", "local-model")
        assert passed is True
        assert "local provider" in reason

        passed, reason = immune_check(messages, "ollama", "qwen")
        assert passed is True
        assert "local provider" in reason

    @patch("hermes_guard.IMMUNE_MODE", "shadow")
    @patch("hermes_guard.log_to_audit")
    def test_shadow_mode_warns_but_passes(self, mock_audit):
        """Verify shadow mode logs warnings but does not block."""
        messages = [{"role": "user", "content": "my key is sk-proj-abc123xyz789ABCDEF012345"}]
        
        passed, reason = immune_check(messages, "openrouter", "deepseek-chat")
        assert passed is True
        assert "SHADOW" in reason
        assert "WOULD be blocked" in reason
        mock_audit.assert_called_once()

    @patch("hermes_guard.IMMUNE_MODE", "enforce")
    @patch("hermes_guard.log_to_audit")
    def test_enforce_mode_blocks_red_secrets(self, mock_audit):
        """Verify enforce mode raises ImmuneBlockError for RED secrets on cloud providers."""
        messages = [{"role": "user", "content": "my key is sk-proj-abc123xyz789ABCDEF012345"}]
        
        with pytest.raises(ImmuneBlockError) as exc_info:
            immune_check(messages, "openrouter", "deepseek-chat")
        
        assert "BLOCKED" in str(exc_info.value)
        assert "RED secrets found" in str(exc_info.value)
        mock_audit.assert_called_once()

    @patch("hermes_guard.IMMUNE_MODE", "enforce")
    @patch("hermes_guard.log_to_audit")
    def test_enforce_mode_allows_yellow_secrets(self, mock_audit):
        """Verify enforce mode allows YELLOW secrets (only logs/warns)."""
        messages = [{"role": "user", "content": "IP is 192.168.1.1"}]
        
        passed, reason = immune_check(messages, "openrouter", "deepseek-chat")
        assert passed is True
        assert "YELLOW" in reason
        mock_audit.assert_called_once()
