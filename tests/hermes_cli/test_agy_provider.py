from hermes_cli.auth import get_auth_status, resolve_provider
from hermes_cli.models import detect_provider_for_model, normalize_provider
from hermes_cli.runtime_provider import resolve_runtime_provider


def test_gemini_oauth_aliases_route_to_agy():
    assert resolve_provider("gemini-oauth") == "agy"
    assert normalize_provider("gemini-oauth") == "agy"
    assert resolve_provider("gemini-subscription") == "agy"


def test_agy_status_uses_agy_command_not_copilot(monkeypatch):
    monkeypatch.setenv("HERMES_AGY_COMMAND", "/opt/bin/agy")
    monkeypatch.delenv("HERMES_COPILOT_ACP_COMMAND", raising=False)
    monkeypatch.setattr("hermes_cli.auth.shutil.which", lambda command: command if command == "/opt/bin/agy" else None)

    status = get_auth_status("agy")

    assert status["provider"] == "agy"
    assert status["command"] == "/opt/bin/agy"
    assert status["args"] == []
    assert status["base_url"] == "agy://antigravity"
    assert status["logged_in"] is True


def test_runtime_agy_uses_external_process_without_api_key(monkeypatch):
    monkeypatch.setenv("HERMES_AGY_COMMAND", "/opt/bin/agy")
    monkeypatch.setattr("hermes_cli.auth.shutil.which", lambda command: command if command == "/opt/bin/agy" else None)

    runtime = resolve_runtime_provider(requested="agy", target_model="gemini-3.5-flash")

    assert runtime["provider"] == "agy"
    assert runtime["api_mode"] == "chat_completions"
    assert runtime["base_url"] == "agy://antigravity"
    assert runtime["api_key"] == "agy-external"
    assert runtime["command"] == "/opt/bin/agy"


def test_bare_gemini_model_prefers_agy_when_binary_exists(monkeypatch):
    monkeypatch.setattr("hermes_cli.models.shutil.which", lambda command: "/opt/bin/agy" if command == "agy" else None)

    assert detect_provider_for_model("gemini-3.5-flash", "auto") == ("agy", "gemini-3.5-flash")
