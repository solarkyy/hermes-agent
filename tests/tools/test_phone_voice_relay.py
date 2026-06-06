"""Tests for the phone voice relay used from SSH/mobile browsers."""

from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest


class RelayServer:
    def __init__(self, handler):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    @property
    def port(self) -> int:
        return int(self.server.server_address[1])

    def request_raw(self, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        res = conn.getresponse()
        data = res.read()
        conn.close()
        return res.status, dict(res.getheaders()), data

    def request(self, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None):
        status, _headers, data = self.request_raw(method, path, body=body, headers=headers)
        return status, json.loads(data.decode("utf-8"))


def test_extension_for_content_type_handles_browser_mimes():
    from tools.phone_voice_relay import _extension_for_content_type

    assert _extension_for_content_type("audio/webm;codecs=opus") == ".webm"
    assert _extension_for_content_type("audio/mp4") == ".mp4"
    assert _extension_for_content_type("audio/ogg; codecs=opus") == ".ogg"
    assert _extension_for_content_type("unknown/type") == ".webm"


def test_index_requires_token_and_does_not_embed_raw_token(tmp_path):
    from tools.phone_voice_relay import RelayConfig, make_handler

    config = RelayConfig(token="secret", temp_dir=str(tmp_path), transcriber=lambda path, model=None: {"success": True, "transcript": "ignored"})
    with RelayServer(make_handler(config)) as server:
        status, payload = server.request("GET", "/")
        ok_status, headers, body = server.request_raw("GET", "/?token=secret")

    assert status == 401
    assert payload["ok"] is False
    assert ok_status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert b"secret" not in body
    assert b"URLSearchParams" in body


def test_transcribe_endpoint_requires_token(tmp_path):
    from tools.phone_voice_relay import RelayConfig, make_handler

    config = RelayConfig(token="secret", temp_dir=str(tmp_path), transcriber=lambda path, model=None: {"success": True, "transcript": "ignored"})
    with RelayServer(make_handler(config)) as server:
        status, payload = server.request("POST", "/api/transcribe", body=b"audio", headers={"Content-Type": "audio/webm"})

    assert status == 401
    assert payload["ok"] is False


def test_transcribe_endpoint_writes_audio_and_returns_transcript(tmp_path):
    from tools.phone_voice_relay import RelayConfig, make_handler

    seen = {}

    def fake_transcriber(path, model=None):
        seen["path"] = path
        seen["model"] = model
        seen["audio"] = Path(path).read_bytes()
        return {"success": True, "transcript": "  hello from phone  ", "provider": "fake"}

    config = RelayConfig(token="secret", model="tiny", temp_dir=str(tmp_path), transcriber=fake_transcriber)
    with RelayServer(make_handler(config)) as server:
        status, payload = server.request(
            "POST",
            "/api/transcribe?token=secret",
            body=b"audio-bytes",
            headers={"Content-Type": "audio/webm;codecs=opus"},
        )

    assert status == 200
    assert payload["ok"] is True
    assert payload["transcript"] == "hello from phone"
    assert payload["provider"] == "fake"
    assert seen["model"] == "tiny"
    assert seen["audio"] == b"audio-bytes"
    assert Path(seen["path"]).suffix == ".webm"
    assert not Path(seen["path"]).exists()
    assert "audio_path" not in payload


def test_log_redaction_removes_query_token():
    from tools.phone_voice_relay import _redact_token_from_text

    line = '"POST /api/transcribe?token=secret&x=1 HTTP/1.1" 200 - secret'

    redacted = _redact_token_from_text(line, "secret")

    assert "secret" not in redacted
    assert "token=%3Credacted-token%3E" in redacted or "token=<redacted-token>" in redacted


def test_main_refuses_remote_host_without_explicit_opt_in(capsys):
    from tools.phone_voice_relay import main

    code = main(["--host", "0.0.0.0", "--port", "0"])

    assert code == 2
    assert "non-loopback" in capsys.readouterr().err


def test_draft_endpoint_refuses_send_without_allow_send(monkeypatch, tmp_path):
    from tools.phone_voice_relay import RelayConfig, make_handler

    called = False

    def fake_draft(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("tools.phone_voice_relay.draft_to_tmux", fake_draft)
    config = RelayConfig(token="secret", temp_dir=str(tmp_path), tmux_target="%1", allow_send=False)
    with RelayServer(make_handler(config)) as server:
        status, payload = server.request(
            "POST",
            "/api/draft?token=secret",
            body=json.dumps({"text": "ship it", "send": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    assert status == 403
    assert payload["ok"] is False
    assert called is False


def test_draft_to_tmux_uses_argv_not_shell(monkeypatch):
    from tools.phone_voice_relay import draft_to_tmux

    calls = []
    monkeypatch.setattr("tools.phone_voice_relay.shutil.which", lambda name: "/usr/bin/tmux")

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return None

    monkeypatch.setattr("tools.phone_voice_relay.subprocess.run", fake_run)
    draft_to_tmux("say hi; $(do-not-run)", target="%7", send=True)

    assert calls[0][0] == ["tmux", "set-buffer", "say hi; $(do-not-run)"]
    assert calls[1][0] == ["tmux", "paste-buffer", "-t", "%7"]
    assert calls[2][0] == ["tmux", "send-keys", "-t", "%7", "Enter"]


def test_draft_to_tmux_requires_target():
    from tools.phone_voice_relay import draft_to_tmux

    with pytest.raises(ValueError, match="tmux target"):
        draft_to_tmux("hello", target=None)
