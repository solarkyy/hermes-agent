"""Slack Steward plugin — read-only Slack hygiene audits and laws.

The plugin is intentionally dry-run first. It registers tools and a `/steward`
slash command that can audit Slack channel noise and propose approval-gated
moderation actions without writing to Slack.
"""

from __future__ import annotations

import json
import shlex
from typing import Any, Mapping

from .steward import (
    DEFAULT_CHANNELS,
    SlackChannelSnapshot,
    SlackMessageSnapshot,
    audit_live,
    audit_snapshot,
    draft_channel_laws,
    render_report_text,
)


AUDIT_SCHEMA = {
    "name": "slack_steward_audit",
    "description": (
        "Dry-run Slack moderation audit: channel laws, heartbeat noise, "
        "duplicate alerts, research cycle logs, and stale approvals. Never writes to Slack."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "channels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Channel names to audit, default: council, alerts, omnira-research, approvals.",
            },
            "lookback_messages": {
                "type": "integer",
                "minimum": 1,
                "maximum": 200,
                "default": 100,
                "description": "Maximum recent messages to inspect per channel for live Slack reads.",
            },
            "dry_run": {
                "type": "boolean",
                "default": True,
                "description": "Must remain true in the MVP. dry_run=false returns BLOCK.",
            },
            "snapshot": {
                "type": "object",
                "description": "Optional offline snapshot for tests/manual analysis: {channels:[...], messages:{channel_id_or_name:[...]}}.",
            },
        },
        "additionalProperties": False,
    },
}

DRAFT_LAWS_SCHEMA = {
    "name": "slack_steward_draft_laws",
    "description": "Draft approval-gated pinned posting laws for Slack channels. Never pins or writes.",
    "parameters": {
        "type": "object",
        "properties": {
            "channels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Channel names to draft laws for.",
            }
        },
        "additionalProperties": False,
    },
}


def handle_steward_audit(args: Mapping[str, Any], **_: Any) -> str:
    channels = _channels_from_args(args)
    dry_run = bool(args.get("dry_run", True))
    lookback = int(args.get("lookback_messages") or 100)

    snapshot = args.get("snapshot")
    if isinstance(snapshot, Mapping):
        report = audit_snapshot(
            _snapshot_channels(snapshot),
            _snapshot_messages(snapshot),
            channel_names=channels,
            dry_run=dry_run,
        )
    else:
        report = audit_live(channel_names=channels, lookback_messages=lookback, dry_run=dry_run)
    return json.dumps(report.to_dict(), sort_keys=True)


def handle_draft_laws(args: Mapping[str, Any], **_: Any) -> str:
    return json.dumps(draft_channel_laws(_channels_from_args(args)), sort_keys=True)


def _handle_slash(raw_args: str) -> str:
    try:
        argv = shlex.split(raw_args or "")
    except ValueError as exc:
        return f"Usage error: {exc}\n\n{_HELP}"
    if not argv or argv[0] in {"help", "-h", "--help"}:
        return _HELP

    sub = argv[0].lower()
    channels = [arg for arg in argv[1:] if arg.startswith("#") or arg in DEFAULT_CHANNELS]
    if sub == "audit":
        report = audit_live(channel_names=channels or None, dry_run=True)
        return render_report_text(report)
    if sub in {"rules", "laws"}:
        data = draft_channel_laws(channels or None)
        lines = ["Slack Steward channel laws (draft; not pinned):"]
        for channel, text in data["laws"].items():
            lines.append(f"\n{text}")
        return "\n".join(lines)
    if sub in {"noisy-sources", "dedupe-alerts"}:
        selected = channels or ["council", "alerts", "omnira-research"]
        report = audit_live(channel_names=selected, dry_run=True)
        return render_report_text(report)
    return f"Unknown subcommand: {sub}\n\n{_HELP}"


_HELP = """Slack Steward dry-run commands:
/steward audit [#council #alerts #omnira-research #approvals]
/steward rules [#channel]
/steward noisy-sources [#channel]

MVP law: no Slack writes, deletes, pins, archives, or channel mutations are performed. Proposed actions are approval-gated.
""".strip()


def _channels_from_args(args: Mapping[str, Any]) -> list[str] | None:
    raw = args.get("channels")
    if raw is None or raw == "":
        return None
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(part).strip() for part in raw if str(part).strip()]
    return None


def _snapshot_channels(snapshot: Mapping[str, Any]) -> list[SlackChannelSnapshot]:
    channels = []
    for raw in snapshot.get("channels") or []:
        if isinstance(raw, Mapping):
            channels.append(SlackChannelSnapshot.from_slack(raw))
    return channels


def _snapshot_messages(snapshot: Mapping[str, Any]) -> dict[str, list[SlackMessageSnapshot]]:
    messages: dict[str, list[SlackMessageSnapshot]] = {}
    raw_messages = snapshot.get("messages") or {}
    if not isinstance(raw_messages, Mapping):
        return messages
    for channel_key, items in raw_messages.items():
        channel_id = str(channel_key)
        messages[channel_id] = [
            SlackMessageSnapshot.from_slack(item, channel_id)
            for item in (items or [])
            if isinstance(item, Mapping)
        ]
    return messages


def register(ctx) -> None:
    ctx.register_tool(
        name="slack_steward_audit",
        toolset="slack_steward",
        schema=AUDIT_SCHEMA,
        handler=handle_steward_audit,
        description="Read-only Slack hygiene audit with AOMS gates.",
        emoji="🧹",
    )
    ctx.register_tool(
        name="slack_steward_draft_laws",
        toolset="slack_steward",
        schema=DRAFT_LAWS_SCHEMA,
        handler=handle_draft_laws,
        description="Draft Slack channel posting laws without writing.",
        emoji="📌",
    )
    ctx.register_command(
        "steward",
        handler=_handle_slash,
        description="Dry-run Slack admin/moderation steward.",
        args_hint="audit|rules [#channel]",
    )
