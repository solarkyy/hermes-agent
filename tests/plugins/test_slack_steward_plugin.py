from __future__ import annotations

import json
import time
from dataclasses import asdict

import pytest

from plugins.slack_steward import handle_draft_laws, handle_steward_audit
from plugins.slack_steward.steward import (
    AOMS_BLOCK,
    AOMS_PASS,
    AOMS_WATCH,
    SlackApiError,
    SlackChannelSnapshot,
    SlackMessageSnapshot,
    audit_live,
    audit_snapshot,
    draft_channel_law,
    sample_texts,
)


def _channel(channel_id: str, name: str, topic: str = "") -> SlackChannelSnapshot:
    return SlackChannelSnapshot(id=channel_id, name=name, topic=topic, is_member=True)


def _msg(channel_id: str, text: str, *, ts: str | None = None, bot_id: str = "BTEST", reactions=()) -> SlackMessageSnapshot:
    return SlackMessageSnapshot(
        channel_id=channel_id,
        ts=ts or str(time.time()),
        text=text,
        bot_id=bot_id,
        reactions=tuple(reactions),
    )


def test_council_heartbeat_spam_proposes_reroute_and_channel_law():
    channels = [_channel("C1", "council", topic="organism council")]
    messages = {
        "C1": [
            _msg("C1", "Weight heartbeat health tick ok"),
            _msg("C1", "mesh-witness heartbeat: vps ok"),
            _msg("C1", "EVO pulse health ok"),
        ]
    }

    report = audit_snapshot(channels, messages, channel_names=["council"])

    assert report.gate == AOMS_WATCH
    assert any(f.kind == "heartbeat_noise" for f in report.findings)
    action_types = {a.action_type for a in report.proposed_actions}
    assert "reroute_heartbeat_source" in action_types
    assert "draft_channel_law" in action_types
    assert all(a.dry_run and a.requires_approval for a in report.proposed_actions)


def test_alert_duplicate_flood_proposes_rate_limit_once():
    channels = [_channel("C2", "alerts", topic="P0/P1 actionable alerts only")]
    messages = {
        "C2": [
            _msg("C2", "[git-sync:vps] fast-forward FAILED at 2026-06-01T01:00:00Z"),
            _msg("C2", "[git-sync:vps] fast-forward FAILED at 2026-06-01T01:02:00Z"),
            _msg("C2", "[git-sync:vps] fast-forward FAILED at 2026-06-01T01:04:00Z"),
            _msg("C2", "different incident opened"),
        ]
    }

    report = audit_snapshot(channels, messages, channel_names=["alerts"])

    assert report.gate == AOMS_WATCH
    assert [a.action_type for a in report.proposed_actions].count("rate_limit_alert_signature") == 1
    duplicate = next(f for f in report.findings if f.kind == "duplicate_alert_flood")
    assert duplicate.evidence["count"] == 3


def test_research_cycle_noise_suggests_threading():
    channels = [_channel("C3", "omnira-research", topic="hypotheses and comparator packets")]
    messages = {"C3": [_msg("C3", f"[overnight-aom] cycle={i} complete") for i in range(6)]}

    report = audit_snapshot(channels, messages, channel_names=["omnira-research"])

    assert any(a.action_type == "thread_research_cycles" for a in report.proposed_actions)
    assert any(f.kind == "research_cycle_noise" for f in report.findings)


def test_stale_approval_digest_ignores_resolved_reactions():
    now = 1_780_000_000.0
    old = str(now - 25 * 3600)
    channels = [_channel("C4", "approvals", topic="Kyle approval requests")]
    messages = {
        "C4": [
            _msg("C4", "approval requested: deploy X", ts=old),
            _msg("C4", "approval requested: deploy Y", ts=old, reactions=("white_check_mark",)),
        ]
    }

    report = audit_snapshot(channels, messages, channel_names=["approvals"], now=now)

    stale = next(f for f in report.findings if f.kind == "stale_approvals")
    assert stale.evidence["count"] == 1
    assert any(a.action_type == "digest_stale_approvals" for a in report.proposed_actions)


def test_non_dry_run_is_blocked_before_any_action():
    report = audit_snapshot([], {}, dry_run=False)

    assert report.gate == AOMS_BLOCK
    assert not report.ok
    assert report.proposed_actions == ()
    assert report.findings[0].kind == "non_dry_run_refused"


def test_draft_laws_are_dry_run_and_include_expected_council_routing():
    data = handle_draft_laws({"channels": ["#council"]})
    parsed = json.loads(data)

    assert parsed["gate"] == AOMS_PASS
    assert parsed["dry_run"] is True
    assert "#council steward law" in parsed["laws"]["council"]
    assert "#organism-pulse" in parsed["laws"]["council"]
    assert parsed["proposed_actions"][0]["requires_approval"] is True


def test_tool_handler_accepts_offline_snapshot_without_slack_token(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    snapshot = {
        "channels": [asdict(_channel("C1", "council"))],
        "messages": {
            "C1": [
                {"ts": "1", "text": "Weight heartbeat health tick ok", "bot_id": "B1"},
                {"ts": "2", "text": "EVO pulse health ok", "bot_id": "B1"},
                {"ts": "3", "text": "pi heartbeat health tick ok", "bot_id": "B1"},
            ]
        },
    }

    parsed = json.loads(handle_steward_audit({"channels": ["council"], "snapshot": snapshot}))

    assert parsed["gate"] == AOMS_WATCH
    assert any(f["kind"] == "heartbeat_noise" for f in parsed["findings"])


def test_live_audit_missing_token_blocks_without_exception(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)

    report = audit_live(channel_names=["council"])

    assert report.gate == AOMS_BLOCK
    assert report.findings[0].kind == "missing_slack_token"


class _ScopeFailClient:
    def list_channels(self):
        raise SlackApiError("conversations.list", "missing_scope")


def test_live_audit_missing_scope_is_block_not_exception():
    report = audit_live(client=_ScopeFailClient(), channel_names=["council"])

    assert report.gate == AOMS_BLOCK
    assert report.errors[0]["error"] == "missing_scope"


class _GenericFailClient:
    def list_channels(self):
        raise ValueError("boom with xoxb-should-not-leak")


def test_live_audit_generic_failure_is_sanitized_watch():
    report = audit_live(client=_GenericFailClient(), channel_names=["council"])

    assert report.gate == AOMS_WATCH
    assert report.errors[0] == {"gate": AOMS_WATCH, "kind": "slack_read_failed", "error": "ValueError"}


class _MissingChannelClient:
    def list_channels(self):
        return [_channel("C1", "alerts")]

    def history(self, channel_id, *, limit=100):
        return []


def test_live_audit_missing_requested_channel_reports_watch():
    report = audit_live(client=_MissingChannelClient(), channel_names=["council"])

    assert report.gate == AOMS_WATCH
    assert report.errors[0]["kind"] == "channel_not_visible"
    assert report.errors[0]["channel"] == "council"


def test_samples_redact_token_like_text_before_reporting():
    samples = sample_texts([
        _msg("C1", "failed with token=sk-test-secret and bearer abcdefghijklmnop"),
        _msg("C1", "slack xoxb-123-456-secret"),
    ])

    joined = "\n".join(samples)
    assert "sk-test-secret" not in joined
    assert "abcdefghijklmnop" not in joined
    assert "xoxb-123" not in joined
    assert "<redacted" in joined


class _FakeCtx:
    def __init__(self):
        self.tools = []
        self.commands = []

    def register_tool(self, **kwargs):
        self.tools.append(kwargs)

    def register_command(self, *args, **kwargs):
        self.commands.append((args, kwargs))


def test_plugin_registers_tools_and_steward_command():
    from plugins.slack_steward import register

    ctx = _FakeCtx()
    register(ctx)

    assert {tool["name"] for tool in ctx.tools} == {"slack_steward_audit", "slack_steward_draft_laws"}
    assert all(tool["toolset"] == "slack_steward" for tool in ctx.tools)
    assert ctx.commands[0][0][0] == "steward"


def test_unknown_channel_law_has_safe_default():
    law = draft_channel_law("#random")

    assert "#random steward law" in law
    assert "raw logs" in law
