"""Comms Steward plugin — oneness-aligned Slack/Discord/Telegram audits.

This plugin is a read-only/dry-run steward for the comms spine:
Slack primary cockpit, Discord secondary/presence, Telegram breakglass only.
"""

from __future__ import annotations

import json
import shlex
from typing import Any, Mapping

from .steward import (
    DEFAULT_PLATFORMS,
    audit_comms_spine,
    draft_comms_laws,
    render_report_text,
)


AUDIT_SCHEMA = {
    "name": "comms_steward_audit",
    "description": (
        "Dry-run cross-platform comms spine audit for Slack, Discord, and Telegram. "
        "Detects route drift, channel-law gaps, Discord speech-act drift, and Telegram routine-route risk. Never writes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["slack", "discord", "telegram"]},
                "description": "Platforms to audit. Default: slack, discord, telegram.",
            },
            "lookback_messages": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 50,
                "description": "Recent messages to inspect per live channel when supported.",
            },
            "dry_run": {
                "type": "boolean",
                "default": True,
                "description": "Must remain true in MVP; false returns BLOCK.",
            },
            "snapshots": {
                "type": "object",
                "description": "Optional offline snapshots keyed by platform for tests/manual analysis.",
            },
        },
        "additionalProperties": False,
    },
}

DRAFT_LAWS_SCHEMA = {
    "name": "comms_steward_draft_laws",
    "description": "Draft Slack/Discord/Telegram comms spine posting laws. Never pins or writes.",
    "parameters": {
        "type": "object",
        "properties": {
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["slack", "discord", "telegram"]},
                "description": "Platforms to draft laws for. Default: all.",
            }
        },
        "additionalProperties": False,
    },
}


def handle_comms_audit(args: Mapping[str, Any], **_: Any) -> str:
    report = audit_comms_spine(
        platforms=_platforms_from_args(args),
        snapshots=args.get("snapshots") if isinstance(args.get("snapshots"), Mapping) else None,
        dry_run=bool(args.get("dry_run", True)),
        lookback_messages=int(args.get("lookback_messages") or 50),
    )
    return json.dumps(report.to_dict(), sort_keys=True)


def handle_draft_laws(args: Mapping[str, Any], **_: Any) -> str:
    return json.dumps(draft_comms_laws(_platforms_from_args(args)), sort_keys=True)


def _handle_slash(raw_args: str) -> str:
    try:
        argv = shlex.split(raw_args or "")
    except ValueError as exc:
        return f"Usage error: {exc}\n\n{_HELP}"
    if not argv or argv[0] in {"help", "-h", "--help"}:
        return _HELP
    sub = argv[0].lower()
    platforms = [arg.lower() for arg in argv[1:] if arg.lower() in DEFAULT_PLATFORMS]
    if sub == "audit":
        return render_report_text(audit_comms_spine(platforms=platforms or None, dry_run=True))
    if sub in {"laws", "rules"}:
        data = draft_comms_laws(platforms or None)
        lines = ["Comms Steward laws (draft; no pins/writes):"]
        for platform, laws in data["laws"].items():
            lines.append(f"\n[{platform}]")
            if isinstance(laws, Mapping):
                for _name, text in laws.items():
                    lines.append(str(text))
            else:
                lines.append(str(laws))
        return "\n".join(lines)
    if sub == "status":
        return "Comms spine target: Slack primary cockpit → Discord secondary/presence → Telegram breakglass only. Use `/comms-steward audit`."
    return f"Unknown subcommand: {sub}\n\n{_HELP}"


_HELP = """Comms Steward dry-run commands:
/comms-steward audit [slack discord telegram]
/comms-steward rules [slack discord telegram]
/comms-steward status

MVP law: no Slack/Discord/Telegram writes, deletes, pins, archives, or route mutations are performed. Proposed actions are approval-gated.
""".strip()


def _platforms_from_args(args: Mapping[str, Any]) -> list[str] | None:
    raw = args.get("platforms")
    if raw is None or raw == "":
        return None
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(part).strip() for part in raw if str(part).strip()]
    return None


def register(ctx) -> None:
    ctx.register_tool(
        name="comms_steward_audit",
        toolset="comms_steward",
        schema=AUDIT_SCHEMA,
        handler=handle_comms_audit,
        description="Read-only Slack/Discord/Telegram comms spine audit with AOMS gates.",
        emoji="📡",
    )
    ctx.register_tool(
        name="comms_steward_draft_laws",
        toolset="comms_steward",
        schema=DRAFT_LAWS_SCHEMA,
        handler=handle_draft_laws,
        description="Draft comms spine posting laws without writing.",
        emoji="📜",
    )
    for command_name in ("comms-steward", "comms_steward"):
        ctx.register_command(
            command_name,
            handler=_handle_slash,
            description="Dry-run oneness comms spine steward.",
            args_hint="audit|rules [slack discord telegram]",
        )
