from __future__ import annotations

import json

from plugins.comms_steward import handle_comms_audit, handle_draft_laws
from pathlib import Path

from plugins.comms_steward.steward import (
    AOMS_BLOCK,
    AOMS_PASS,
    AOMS_WATCH,
    DiscordApiError,
    DiscordChannelSnapshot,
    DiscordMessageSnapshot,
    DiscordReadClient,
    audit_comms_spine,
    audit_discord_snapshot,
    draft_discord_channel_law,
    has_speech_act,
)


def _ch(channel_id: str, name: str, topic: str = "") -> DiscordChannelSnapshot:
    return DiscordChannelSnapshot(id=channel_id, name=name, topic=topic)


def _msg(channel_id: str, content: str, *, bot: bool = True) -> DiscordMessageSnapshot:
    return DiscordMessageSnapshot(channel_id=channel_id, id=f"m-{len(content)}", content=content, author_bot=bot)


def test_discord_missing_required_channels_are_watch_actions():
    findings, actions, errors = audit_discord_snapshot([_ch("C1", "organism", "coordination")], {"C1": []})

    assert not errors
    missing = [f for f in findings if f.kind == "missing_required_channel"]
    assert {f.target for f in missing} == {"general", "receipts", "alerts"}
    assert all(a.dry_run and a.requires_approval for a in actions)
    assert any(a.action_type == "create_or_map_channel" for a in actions)


def test_discord_receipts_require_speech_act_and_evidence():
    channels = [_ch("R", "receipts", "receipts evidence")]
    messages = {"R": [_msg("R", "done, shipped it"), _msg("R", "RECEIPT Delta: shipped commit:abc1234 L4")]}

    findings, actions, _errors = audit_discord_snapshot(channels, messages)

    drift = next(f for f in findings if f.kind == "receipt_envelope_drift")
    assert drift.evidence["count"] == 1
    assert any(a.action_type == "enforce_receipt_envelope" for a in actions)


def test_discord_general_ops_leak_and_alert_routine_noise_detected():
    channels = [_ch("G", "general", "warmth"), _ch("A", "alerts", "critical alerts")]
    messages = {
        "G": [_msg("G", "RECEIPT: commit:deadbee shipped", bot=True)],
        "A": [_msg("A", "heartbeat health tick ok", bot=True)],
    }

    findings, actions, _errors = audit_discord_snapshot(channels, messages)

    assert any(f.kind == "general_ops_leak" for f in findings)
    assert any(f.kind == "routine_alert_noise" for f in findings)
    assert {"reroute_general_ops", "route_routine_out_of_alerts"}.issubset({a.action_type for a in actions})


def test_discord_organism_bot_posts_need_speech_act_and_samples_redact():
    channels = [_ch("O", "organism", "coordination")]
    messages = {"O": [_msg("O", "token=sk-secret heartbeat from bot", bot=True)]}

    findings, _actions, _errors = audit_discord_snapshot(channels, messages)

    finding = next(f for f in findings if f.kind == "missing_speech_act")
    sample = finding.evidence["samples"][0]
    assert "sk-secret" not in sample
    assert "<redacted" in sample


def test_telegram_breakglass_pass_and_on_watch():
    good = audit_comms_spine(platforms=["telegram"], snapshots={"telegram": {"mode": "breakglass", "enabled": False}})
    risky = audit_comms_spine(platforms=["telegram"], snapshots={"telegram": {"mode": "on", "enabled": True}})

    assert good.gate == AOMS_PASS
    assert any(f.kind == "breakglass_posture" for f in good.findings)
    assert risky.gate == AOMS_WATCH
    assert any(a.action_type == "downgrade_to_breakglass" for a in risky.proposed_actions)


def test_telegram_config_enabled_is_watch_when_no_snapshot(monkeypatch):
    import hermes_cli.config

    monkeypatch.setattr(hermes_cli.config, "load_config", lambda: {"telegram": {"enabled": True, "mode": "on"}})
    report = audit_comms_spine(platforms=["telegram"])

    assert report.gate == AOMS_WATCH
    assert any(f.kind == "routine_route_risk" for f in report.findings)


def test_comms_dry_run_false_blocks():
    report = audit_comms_spine(dry_run=False)

    assert report.gate == AOMS_BLOCK
    assert not report.ok
    assert report.proposed_actions == ()


def test_handle_comms_audit_accepts_offline_discord_snapshot():
    snapshot = {
        "discord": {
            "channels": [{"id": "R", "name": "receipts", "topic": "receipts evidence"}],
            "messages": {"R": [{"id": "1", "content": "done without evidence", "author": {"bot": True}}]},
        },
        "telegram": {"mode": "breakglass", "enabled": False},
    }

    parsed = json.loads(handle_comms_audit({"platforms": ["discord", "telegram"], "snapshots": snapshot}))

    assert parsed["gate"] == AOMS_WATCH
    assert any(f["kind"] == "receipt_envelope_drift" for f in parsed["findings"])


def test_draft_laws_include_discord_and_telegram_contracts():
    parsed = json.loads(handle_draft_laws({"platforms": ["discord", "telegram"]}))

    assert parsed["gate"] == AOMS_PASS
    assert "Discord #receipts oneness law" in parsed["laws"]["discord"]["receipts"]
    assert "breakglass only" in parsed["laws"]["telegram"]["breakglass"]
    assert all(a["dry_run"] for a in parsed["proposed_actions"])


def test_speech_act_detection_accepts_text_and_json_envelope():
    assert has_speech_act("RECEIPT Delta: done commit:abc1234", {"RECEIPT"})
    assert has_speech_act('{"kind":"HANDOFF","summary":"next"}', {"HANDOFF"})
    assert not has_speech_act("I did a thing", {"RECEIPT"})


class _FakeCtx:
    def __init__(self):
        self.tools = []
        self.commands = []

    def register_tool(self, **kwargs):
        self.tools.append(kwargs)

    def register_command(self, *args, **kwargs):
        self.commands.append((args, kwargs))


def test_discord_multi_guild_without_home_channel_is_ambiguous(monkeypatch):
    class AmbiguousClient(DiscordReadClient):
        def __init__(self):
            pass

        def _api(self, method, path, params=None):
            assert path == "users/@me/guilds"
            return [{"id": "G1"}, {"id": "G2"}]

    monkeypatch.delenv("DISCORD_HOME_CHANNEL", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)

    try:
        AmbiguousClient().infer_guild_id()
    except DiscordApiError as exc:
        assert exc.status == 409
        assert "ambiguous" in exc.body
    else:  # pragma: no cover
        raise AssertionError("expected DiscordApiError")


class _PartialDiscordClient:
    def list_channels(self):
        return [_ch("R", "receipts", "receipts evidence"), _ch("O", "organism", "coordination")]

    def history(self, channel_id, *, limit=50):
        if channel_id == "R":
            raise DiscordApiError("GET", 403, "forbidden")
        return [_msg(channel_id, "no speech act", bot=True)]


def test_discord_live_partial_history_failure_continues(monkeypatch):
    from plugins.comms_steward import steward

    monkeypatch.setattr(steward.DiscordReadClient, "from_env", lambda: _PartialDiscordClient())
    report = audit_comms_spine(platforms=["discord"])

    assert report.gate == AOMS_WATCH
    assert any(e.get("kind") == "history_read_failed" for e in report.errors)
    assert any(f.kind == "missing_speech_act" for f in report.findings)


def test_no_comms_write_endpoint_strings_present():
    root = Path(__file__).resolve().parents[2]
    text = (root / "plugins" / "comms_steward" / "steward.py").read_text()

    forbidden = ["chat.postMessage", "pins.add", "DELETE", "PATCH", "conversations.archive", "chat.delete"]
    assert not any(token in text for token in forbidden)


def test_plugin_registers_comms_tools_and_command():
    from plugins.comms_steward import register

    ctx = _FakeCtx()
    register(ctx)

    assert {tool["name"] for tool in ctx.tools} == {"comms_steward_audit", "comms_steward_draft_laws"}
    assert all(tool["toolset"] == "comms_steward" for tool in ctx.tools)
    assert {cmd[0][0] for cmd in ctx.commands} == {"comms-steward", "comms_steward"}


def test_draft_discord_channel_law_states_discord_not_truth_plane():
    law = draft_discord_channel_law("receipts")

    assert "Source of truth" in law
    assert "Discord #receipts" in law
