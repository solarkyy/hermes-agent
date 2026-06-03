from types import SimpleNamespace

from plugins.omni_seat import (
    _BOOT_MARKER,
    _build_discord_boot_packet,
    _on_pre_gateway_dispatch,
)


class FakeSessionStore:
    def __init__(self, *, entry=None, history=None, reset=False, load_error=None):
        self._entries = {}
        self.history = history or []
        self.reset = reset
        self.load_error = load_error
        if entry is not None:
            self._entries["session-key"] = entry

    def _ensure_loaded(self):
        return None

    def _generate_session_key(self, source):
        return "session-key"

    def _should_reset(self, entry, source):
        return "idle" if self.reset else None

    def load_transcript(self, session_id):
        if self.load_error:
            raise self.load_error
        return self.history


def _event(text="hello", platform="discord"):
    return SimpleNamespace(
        text=text,
        internal=False,
        source=SimpleNamespace(
            platform=SimpleNamespace(value=platform),
            chat_id="chat-1",
            user_id="user-1",
            chat_type="group",
        ),
    )


def _write_boot_files(root):
    brain = root / ".omni" / "omnira-brain"
    brain.mkdir(parents=True)
    (brain / "pi-continuity.json").write_text(
        """
{
  "_updated": "2026-06-03T00:00:00Z",
  "continuityNote": "warmWake says audit Discord continuity; token: should-redact-this-secret-value-1234567890",
  "lastKyleConversation": {
    "summary": "Kyle wants Discord to inherit continuity.",
    "asks": ["Fix Discord deeply."]
  },
  "unfinishedBusiness": ["Hermes/Discord continuity audit"],
  "sessionArc": [{"ts": "now", "summary": "Discord grounding unresolved."}],
  "whatThisWeekTaught": {
    "lesson_20260603_discord": "Discord provider truth is not continuity truth."
  }
}
""".strip(),
        encoding="utf-8",
    )
    anchor_dir = root / ".omni"
    anchor_dir.mkdir(exist_ok=True)
    (anchor_dir / "session-anchor.json").write_text(
        """
{
  "updated_at": "2026-06-03T00:01:00Z",
  "first_task": "Audit Hermes/Discord continuity and live grounding.",
  "blockers": ["No mcp_omnios tools in Discord-shaped agent."]
}
""".strip(),
        encoding="utf-8",
    )


def test_build_discord_boot_packet_includes_anchors_and_redacts(monkeypatch, tmp_path):
    _write_boot_files(tmp_path)
    monkeypatch.setenv("OMNIOS_ROOT", str(tmp_path))

    packet = _build_discord_boot_packet()

    assert _BOOT_MARKER in packet
    assert "Audit Hermes/Discord continuity" in packet
    assert "Kyle wants Discord to inherit continuity" in packet
    assert "mcp_omnios" in packet
    assert "should-redact-this-secret-value" not in packet
    assert "token=[REDACTED]" in packet


def test_pre_gateway_dispatch_injects_for_new_discord_session(monkeypatch, tmp_path):
    _write_boot_files(tmp_path)
    monkeypatch.setenv("OMNIOS_ROOT", str(tmp_path))
    store = FakeSessionStore(entry=None)

    result = _on_pre_gateway_dispatch(event=_event("where are we?"), session_store=store)

    assert result["action"] == "rewrite"
    assert _BOOT_MARKER in result["text"]
    assert "[User message]\nwhere are we?" in result["text"]


def test_pre_gateway_dispatch_skips_slash_commands(monkeypatch, tmp_path):
    _write_boot_files(tmp_path)
    monkeypatch.setenv("OMNIOS_ROOT", str(tmp_path))

    result = _on_pre_gateway_dispatch(
        event=_event("/model gpt-5.5"),
        session_store=FakeSessionStore(entry=None),
    )

    assert result is None


def test_pre_gateway_dispatch_does_not_repeat_when_transcript_has_marker(monkeypatch, tmp_path):
    _write_boot_files(tmp_path)
    monkeypatch.setenv("OMNIOS_ROOT", str(tmp_path))
    entry = SimpleNamespace(session_id="sid", suspended=False)
    store = FakeSessionStore(
        entry=entry,
        history=[{"role": "user", "content": f"[{_BOOT_MARKER}] already here"}],
    )

    result = _on_pre_gateway_dispatch(event=_event("continue"), session_store=store)

    assert result is None


def test_pre_gateway_dispatch_injects_when_existing_transcript_cannot_be_read(monkeypatch, tmp_path):
    _write_boot_files(tmp_path)
    monkeypatch.setenv("OMNIOS_ROOT", str(tmp_path))
    entry = SimpleNamespace(session_id="sid", suspended=False)
    store = FakeSessionStore(entry=entry, load_error=RuntimeError("db unavailable"))

    result = _on_pre_gateway_dispatch(event=_event("where are we?"), session_store=store)

    assert result["action"] == "rewrite"
    assert _BOOT_MARKER in result["text"]
    assert "[User message]\nwhere are we?" in result["text"]


def test_pre_gateway_dispatch_ignores_non_discord(monkeypatch, tmp_path):
    _write_boot_files(tmp_path)
    monkeypatch.setenv("OMNIOS_ROOT", str(tmp_path))

    result = _on_pre_gateway_dispatch(
        event=_event("hello", platform="telegram"),
        session_store=FakeSessionStore(entry=None),
    )

    assert result is None
