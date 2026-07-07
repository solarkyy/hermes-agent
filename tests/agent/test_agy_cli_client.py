import pytest

from agent.agy_cli_client import AgyCliClient


def test_agy_cli_client_execs_agy_print(monkeypatch, tmp_path):
    calls = []

    class Completed:
        returncode = 0
        stdout = "OK\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return Completed()

    monkeypatch.setenv("HERMES_AGY_COMMAND", "/bin/agy-test")
    monkeypatch.setattr("agent.agy_cli_client.shutil.which", lambda command: command)
    monkeypatch.setattr("agent.agy_cli_client.subprocess.run", fake_run)

    client = AgyCliClient(agy_cwd=str(tmp_path))
    response = client.chat.completions.create(
        model="gemini-3.5-flash",
        messages=[{"role": "user", "content": "Reply OK"}],
        timeout=30,
    )

    assert response.choices[0].message.content == "OK"
    cmd, kwargs = calls[0]
    assert cmd[:4] == ["/bin/agy-test", "--model", "gemini-3.5-flash", "--print-timeout"]
    assert cmd[-2] == "--print"
    assert "Reply OK" in cmd[-1]
    assert kwargs["cwd"] == str(tmp_path)


def test_agy_cli_stream_shape(monkeypatch):
    monkeypatch.setattr(AgyCliClient, "_run_prompt", lambda *args, **kwargs: "OK")

    client = AgyCliClient(command="agy")
    stream = client.chat.completions.create(
        model="gemini-3.5-flash",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )

    chunks = list(stream)
    assert chunks[0].choices[0].delta.content == "OK"
    assert chunks[-1].choices[0].finish_reason == "stop"


def test_agy_cli_rejects_unknown_model_before_agy_can_silently_fallback(monkeypatch):
    monkeypatch.setattr("agent.agy_cli_client.shutil.which", lambda command: command)
    monkeypatch.setattr("agent.agy_cli_client._live_agy_models", lambda command, home: frozenset())

    client = AgyCliClient(command="agy")

    with pytest.raises(RuntimeError, match="silently falling back"):
        client.chat.completions.create(
            model="definitely-not-a-model",
            messages=[{"role": "user", "content": "hi"}],
        )


def test_agy_cli_accepts_live_model_names(monkeypatch):
    class Completed:
        returncode = 0
        stdout = "OK\n"
        stderr = ""

    monkeypatch.setattr("agent.agy_cli_client.shutil.which", lambda command: command)
    monkeypatch.setattr("agent.agy_cli_client._live_agy_models", lambda command, home: frozenset({"Future Gemini"}))
    monkeypatch.setattr("agent.agy_cli_client.subprocess.run", lambda *args, **kwargs: Completed())

    client = AgyCliClient(command="agy")
    response = client.chat.completions.create(
        model="Future Gemini",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert response.choices[0].message.content == "OK"


def test_agy_cli_tool_call_extraction(monkeypatch):
    raw = (
        '<tool_call>{"id":"call_1","type":"function",'
        '"function":{"name":"read_file","arguments":"{\\"path\\":\\"x\\"}"}}'
        '</tool_call>'
    )
    monkeypatch.setattr(AgyCliClient, "_run_prompt", lambda *args, **kwargs: raw)

    client = AgyCliClient(command="agy")
    response = client.chat.completions.create(
        model="gemini-3.5-flash",
        messages=[{"role": "user", "content": "read x"}],
    )

    assert response.choices[0].finish_reason == "tool_calls"
    call = response.choices[0].message.tool_calls[0]
    assert call.function.name == "read_file"
    assert call.function.arguments == '{"path":"x"}'
