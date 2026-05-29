from unittest.mock import patch

from hermes_cli.model_switch import resolve_alias, switch_model


_VALIDATION = {"accepted": True, "persist": True, "recognized": True, "message": None}


def test_native_anthropic_exact_version_short_aliases(monkeypatch):
    import hermes_cli.model_switch as ms

    ms.DIRECT_ALIASES.clear()
    monkeypatch.setattr("hermes_cli.config.load_config", lambda: {})

    assert resolve_alias("sonnet-4.6", "anthropic") == (
        "anthropic", "claude-sonnet-4-6", "sonnet-4.6"
    )
    assert resolve_alias("opus-4.6", "anthropic") == (
        "anthropic", "claude-opus-4-6", "opus-4.6"
    )
    assert resolve_alias("opus4.8", "anthropic") == (
        "anthropic", "claude-opus-4-8", "opus4.8"
    )


def test_switch_model_resolves_native_anthropic_exact_alias(monkeypatch):
    import hermes_cli.model_switch as ms

    ms.DIRECT_ALIASES.clear()
    monkeypatch.setattr("hermes_cli.config.load_config", lambda: {})
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda **kwargs: {
            "api_key": "test",
            "base_url": "https://api.anthropic.com",
            "api_mode": "anthropic_messages",
            "provider": "anthropic",
        },
    )
    monkeypatch.setattr("hermes_cli.models.validate_requested_model", lambda *a, **kw: _VALIDATION)
    monkeypatch.setattr("hermes_cli.model_switch.get_model_info", lambda *a, **kw: None)
    monkeypatch.setattr("hermes_cli.model_switch.get_model_capabilities", lambda *a, **kw: None)
    monkeypatch.setattr("hermes_cli.models.detect_provider_for_model", lambda *a, **kw: None)

    result = switch_model("opus4.8", "anthropic", "claude-sonnet-4-6")

    assert result.success
    assert result.target_provider == "anthropic"
    assert result.new_model == "claude-opus-4-8"
    assert result.resolved_via_alias == "opus4.8"
