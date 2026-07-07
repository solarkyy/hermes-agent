"""Cross-platform communications spine stewardship.

This module keeps OMNIRA comms aligned to the oneness/comms spine:
Slack is the primary cockpit, Discord is backup/community/presence, and
Telegram is breakglass only. MVP is dry-run/read-only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from typing import Any, Iterable, Mapping, Sequence
from urllib import parse, request

try:  # Reuse the redaction grammar we already hardened for Slack samples.
    from plugins.slack_steward.steward import (
        AOMS_BLOCK,
        AOMS_PASS,
        AOMS_WATCH,
        audit_live as audit_slack_live,
        draft_channel_laws as draft_slack_laws,
        redact_sensitive_text,
    )
except Exception:  # pragma: no cover - defensive import fallback
    AOMS_PASS = "PASS"
    AOMS_WATCH = "WATCH"
    AOMS_BLOCK = "BLOCK"

    def redact_sensitive_text(text: str) -> str:
        return text

    def audit_slack_live(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("slack_steward unavailable")

    def draft_slack_laws(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"laws": {}, "proposed_actions": []}


GATE_RANK = {AOMS_PASS: 0, AOMS_WATCH: 1, AOMS_BLOCK: 2}
DEFAULT_PLATFORMS = ("slack", "discord", "telegram")
DISCORD_REQUIRED_CHANNELS = ("general", "receipts", "alerts", "organism")
DISCORD_SPEECH_ACTS = ("ASK", "OFFER", "CLAIM", "EVIDENCE", "OBJECTION", "HANDOFF", "RECEIPT", "WITNESS")

ROUTINE_NOISE_PATTERNS = (
    re.compile(r"\b(heartbeat|health tick|pulse|cycle=\d+|debug|trace)\b", re.I),
    re.compile(r"\[overnight-aom\]", re.I),
)
ALERT_PATTERNS = (re.compile(r"\b(P0|P1|critical|anomaly|crash|secret breach|data loss|runaway spend)\b", re.I),)
RECEIPT_PATTERNS = (re.compile(r"\b(RECEIPT|HANDOFF|commit:[0-9a-f]{7,}|receipt|L[3-5]|refs?:)\b", re.I),)
EVIDENCE_PATTERNS = (re.compile(r"\b(commit:[0-9a-f]{7,}|[0-9a-f]{7,}\b|refs?:|receipt|log:|path:|L[3-5])", re.I),)

DISCORD_CHANNEL_LAWS: dict[str, dict[str, str]] = {
    "general": {
        "purpose": "personal Kyle conversation, warmth, one-off gratitude",
        "allowed": "ASK/OFFER/WITNESS when human-facing and non-operational",
        "disallowed": "receipts, alerts, task circles, bot dumps",
    },
    "receipts": {
        "purpose": "completed work, session closes, commit receipts, L5 proofs",
        "allowed": "RECEIPT and HANDOFF with evidence refs",
        "disallowed": "chat, questions, speculation, partial work",
    },
    "alerts": {
        "purpose": "anomaly, crash, p>=4, dark node, stuck training, secret breach",
        "allowed": "P0/P1 OBJECTION/EVIDENCE with cooldown and proof",
        "disallowed": "routine summaries, feature announcements, warmth, heartbeat logs",
    },
    "organism": {
        "purpose": "agent coordination, choruses, task circles, daily digest",
        "allowed": "ASK/OFFER/CLAIM/EVIDENCE/HANDOFF/WITNESS with thread_id when applicable",
        "disallowed": "personal messages, critical alerts, receipt-only closes",
    },
}


@dataclass(frozen=True)
class ProposedAction:
    id: str
    gate: str
    platform: str
    action_type: str
    target: str
    summary: str
    reason: str
    dry_run: bool = True
    requires_approval: bool = True
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    gate: str
    platform: str
    kind: str
    target: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)
    action_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommsReport:
    ok: bool
    gate: str
    dry_run: bool
    generated_at: str
    platforms: tuple[str, ...]
    findings: tuple[Finding, ...]
    proposed_actions: tuple[ProposedAction, ...]
    errors: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "gate": self.gate,
            "dry_run": self.dry_run,
            "generated_at": self.generated_at,
            "platforms": list(self.platforms),
            "findings": [asdict(f) for f in self.findings],
            "proposed_actions": [asdict(a) for a in self.proposed_actions],
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class DiscordChannelSnapshot:
    id: str
    name: str
    topic: str = ""
    type: int | None = None

    @classmethod
    def from_discord(cls, raw: Mapping[str, Any]) -> "DiscordChannelSnapshot":
        return cls(
            id=str(raw.get("id") or ""),
            name=normalize_name(str(raw.get("name") or "")),
            topic=str(raw.get("topic") or ""),
            type=int(raw["type"]) if str(raw.get("type", "")).isdigit() else None,
        )


@dataclass(frozen=True)
class DiscordMessageSnapshot:
    channel_id: str
    id: str
    content: str = ""
    author_id: str = ""
    author_bot: bool = False
    timestamp: str = ""

    @classmethod
    def from_discord(cls, raw: Mapping[str, Any], channel_id: str) -> "DiscordMessageSnapshot":
        author = raw.get("author") or {}
        return cls(
            channel_id=channel_id,
            id=str(raw.get("id") or ""),
            content=str(raw.get("content") or ""),
            author_id=str(author.get("id") or raw.get("author_id") or ""),
            author_bot=bool(author.get("bot", raw.get("author_bot", False))),
            timestamp=str(raw.get("timestamp") or ""),
        )


class DiscordApiError(RuntimeError):
    def __init__(self, method: str, status: int, body: str = ""):
        super().__init__(f"Discord API {method} failed: {status}")
        self.method = method
        self.status = status
        self.body = body[:200]


class DiscordReadClient:
    """Tiny Discord REST read client. MVP exposes no write methods."""

    def __init__(self, token: str, *, base_url: str = "https://discord.com/api/v10", timeout: int = 15):
        if not token:
            raise ValueError("Discord token is required")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @classmethod
    def from_env(cls) -> "DiscordReadClient":
        return cls(os.getenv("DISCORD_BOT_TOKEN", ""))

    def _api(self, method: str, path: str, params: Mapping[str, Any] | None = None) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        if params:
            url += "?" + parse.urlencode({k: v for k, v in params.items() if v is not None})
        req = request.Request(url, headers={"Authorization": f"Bot {self._token}", "User-Agent": "Hermes-Comms-Steward/0.1"})
        try:
            with request.urlopen(req, timeout=self._timeout) as resp:  # nosec B310 - Discord API URL is fixed/configured
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # urllib HTTPError has .code and .read
            status = int(getattr(exc, "code", 0) or 0)
            body = ""
            try:
                body = exc.read().decode("utf-8", "replace")  # type: ignore[attr-defined]
            except Exception:
                body = type(exc).__name__
            raise DiscordApiError(method, status, body) from exc

    def infer_guild_id(self) -> str | None:
        home = os.getenv("DISCORD_HOME_CHANNEL") or os.getenv("DISCORD_CHANNEL_ID")
        if home:
            channel = self._api("GET", f"channels/{home}")
            guild_id = channel.get("guild_id") if isinstance(channel, Mapping) else None
            if guild_id:
                return str(guild_id)
        guilds = self._api("GET", "users/@me/guilds")
        if not isinstance(guilds, list) or not guilds:
            return None
        if len(guilds) == 1:
            return str(guilds[0].get("id") or "") or None
        raise DiscordApiError("infer_guild_id", 409, "ambiguous_guild_without_home_channel")

    def list_channels(self, guild_id: str | None = None) -> list[DiscordChannelSnapshot]:
        guild_id = guild_id or self.infer_guild_id()
        if not guild_id:
            return []
        data = self._api("GET", f"guilds/{guild_id}/channels")
        if not isinstance(data, list):
            return []
        return [DiscordChannelSnapshot.from_discord(ch) for ch in data if isinstance(ch, Mapping)]

    def history(self, channel_id: str, *, limit: int = 50) -> list[DiscordMessageSnapshot]:
        data = self._api("GET", f"channels/{channel_id}/messages", {"limit": max(1, min(limit, 100))})
        if not isinstance(data, list):
            return []
        return [DiscordMessageSnapshot.from_discord(msg, channel_id) for msg in data if isinstance(msg, Mapping)]


def audit_comms_spine(
    *,
    platforms: Sequence[str] | None = None,
    snapshots: Mapping[str, Any] | None = None,
    dry_run: bool = True,
    lookback_messages: int = 50,
) -> CommsReport:
    if not dry_run:
        return _blocked_report("non_dry_run_refused", "Comms steward refuses dry_run=false in MVP.")

    selected = tuple(normalize_name(p) for p in (platforms or DEFAULT_PLATFORMS))
    findings: list[Finding] = []
    actions: list[ProposedAction] = []
    errors: list[dict[str, Any]] = []
    snapshots = snapshots or {}

    for platform in selected:
        if platform == "slack":
            f, a, e = _audit_slack_bridge(snapshots.get("slack"), lookback_messages=lookback_messages)
        elif platform == "discord":
            f, a, e = _audit_discord_bridge(snapshots.get("discord"), lookback_messages=lookback_messages)
        elif platform == "telegram":
            f, a, e = audit_telegram_mode(snapshots.get("telegram") if isinstance(snapshots.get("telegram"), Mapping) else None)
        else:
            f, a, e = ([], [], [{"gate": AOMS_WATCH, "platform": platform, "kind": "unknown_platform"}])
        findings.extend(f)
        actions.extend(a)
        errors.extend(e)

    gate = aggregate_gate([f.gate for f in findings] + [e.get("gate", AOMS_WATCH) for e in errors])
    return CommsReport(
        ok=gate != AOMS_BLOCK,
        gate=gate,
        dry_run=True,
        generated_at=datetime.now(timezone.utc).isoformat(),
        platforms=selected,
        findings=tuple(findings),
        proposed_actions=tuple(actions),
        errors=tuple(errors),
    )


def audit_discord_snapshot(
    channels: Sequence[DiscordChannelSnapshot],
    messages_by_channel: Mapping[str, Sequence[DiscordMessageSnapshot]],
) -> tuple[list[Finding], list[ProposedAction], list[dict[str, Any]]]:
    by_name = {normalize_name(ch.name): ch for ch in channels}
    findings: list[Finding] = []
    actions: list[ProposedAction] = []
    errors: list[dict[str, Any]] = []

    for name in DISCORD_REQUIRED_CHANNELS:
        if name not in by_name:
            action = make_action(
                gate=AOMS_WATCH,
                platform="discord",
                action_type="create_or_map_channel",
                target=name,
                summary=f"Create/map Discord #{name} for Agent Oneness routing",
                reason="Discord secondary route lacks a required oneness channel.",
            )
            actions.append(action)
            findings.append(
                Finding(
                    gate=AOMS_WATCH,
                    platform="discord",
                    kind="missing_required_channel",
                    target=name,
                    summary=f"Discord #{name} is not visible in channel inventory.",
                    action_ids=(action.id,),
                )
            )

    for name, channel in by_name.items():
        if name not in DISCORD_CHANNEL_LAWS:
            continue
        messages = tuple(messages_by_channel.get(channel.id) or messages_by_channel.get(name) or ())
        f, a = _audit_discord_channel(name, messages)
        findings.extend(f)
        actions.extend(a)
        if _discord_topic_missing_law(name, channel.topic):
            action = make_action(
                gate=AOMS_WATCH,
                platform="discord",
                action_type="draft_channel_law",
                target=name,
                summary=f"Pin/update Discord #{name} oneness channel law",
                reason="Channel topic does not encode the oneness posting law.",
                payload={"text": draft_discord_channel_law(name)},
            )
            actions.append(action)
            findings.append(
                Finding(
                    gate=AOMS_WATCH,
                    platform="discord",
                    kind="channel_law_missing",
                    target=name,
                    summary=f"Discord #{name} needs an explicit posting law.",
                    action_ids=(action.id,),
                )
            )
    return findings, actions, errors


def audit_telegram_mode(snapshot: Mapping[str, Any] | None = None) -> tuple[list[Finding], list[ProposedAction], list[dict[str, Any]]]:
    cfg = _telegram_posture_from_config()
    cfg.update(dict(snapshot or {}))
    mode = str(cfg.get("mode") or os.getenv("OMNIRA_TELEGRAM_MODE") or "breakglass").strip().lower()
    enabled = cfg.get("enabled")
    if enabled is None:
        enabled = os.getenv("TELEGRAM_BOT_TOKEN") is not None and os.getenv("TELEGRAM_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    findings: list[Finding] = []
    actions: list[ProposedAction] = []
    errors: list[dict[str, Any]] = []
    if mode not in {"off", "breakglass", "on"}:
        findings.append(Finding(AOMS_BLOCK, "telegram", "invalid_mode", "telegram", f"Telegram mode {mode!r} is invalid; expected off|breakglass|on."))
    elif mode == "on" or enabled is True:
        action = make_action(
            gate=AOMS_WATCH,
            platform="telegram",
            action_type="downgrade_to_breakglass",
            target="telegram",
            summary="Keep Telegram breakglass-only, not routine ops",
            reason="Comms spine says Telegram must not carry routine council/training/watchdog traffic.",
            payload={"recommended_mode": "breakglass", "current_mode": mode, "enabled": bool(enabled)},
        )
        actions.append(action)
        findings.append(
            Finding(
                AOMS_WATCH,
                "telegram",
                "routine_route_risk",
                "telegram",
                "Telegram appears enabled/on; verify it is breakglass-only with TTL.",
                action_ids=(action.id,),
            )
        )
    else:
        findings.append(Finding(AOMS_PASS, "telegram", "breakglass_posture", "telegram", f"Telegram posture is {mode}; no routine route implied."))
    return findings, actions, errors


def draft_comms_laws(platforms: Sequence[str] | None = None) -> dict[str, Any]:
    selected = tuple(normalize_name(p) for p in (platforms or DEFAULT_PLATFORMS))
    laws: dict[str, Any] = {}
    proposed: list[dict[str, Any]] = []
    if "slack" in selected:
        slack = draft_slack_laws()
        laws["slack"] = slack.get("laws", {})
        proposed.extend(slack.get("proposed_actions", []))
    if "discord" in selected:
        laws["discord"] = {name: draft_discord_channel_law(name) for name in DISCORD_REQUIRED_CHANNELS}
        for name, text in laws["discord"].items():
            proposed.append(asdict(make_action(
                gate=AOMS_WATCH,
                platform="discord",
                action_type="pin_channel_law",
                target=name,
                summary=f"Pin/update Discord #{name} oneness law",
                reason="Draft only. Pinning requires Kyle/admin approval.",
                payload={"text": text},
            )))
    if "telegram" in selected:
        laws["telegram"] = {
            "breakglass": "Telegram is breakglass only: P0 AND Slack failed AND Discord failed AND cooldown/TTL permits. No routine council, training, watchdog, cron, pulse, or daemon chatter."
        }
        proposed.append(asdict(make_action(
            gate=AOMS_WATCH,
            platform="telegram",
            action_type="set_breakglass_mode",
            target="telegram",
            summary="Configure Telegram as breakglass-only",
            reason="Comms spine requires Telegram to stay cold unless primary/secondary routes fail.",
            payload={"mode": "breakglass"},
        )))
    return {"ok": True, "gate": AOMS_PASS, "dry_run": True, "laws": laws, "proposed_actions": proposed}


def _audit_slack_bridge(snapshot: Any, *, lookback_messages: int) -> tuple[list[Finding], list[ProposedAction], list[dict[str, Any]]]:
    try:
        if isinstance(snapshot, Mapping):
            from plugins.slack_steward import handle_steward_audit
            report = json.loads(handle_steward_audit({"snapshot": snapshot}))
        else:
            report = audit_slack_live(lookback_messages=lookback_messages).to_dict()
    except Exception as exc:
        return ([], [], [{"gate": AOMS_BLOCK, "platform": "slack", "kind": "slack_audit_failed", "error": type(exc).__name__}])
    return _convert_external_report("slack", report)


def _audit_discord_bridge(snapshot: Any, *, lookback_messages: int) -> tuple[list[Finding], list[ProposedAction], list[dict[str, Any]]]:
    if isinstance(snapshot, Mapping):
        return audit_discord_snapshot(_snapshot_discord_channels(snapshot), _snapshot_discord_messages(snapshot))
    try:
        client = DiscordReadClient.from_env()
        channels = client.list_channels()
        messages: dict[str, list[DiscordMessageSnapshot]] = {}
        errors: list[dict[str, Any]] = []
        for channel in channels:
            if channel.name in DISCORD_CHANNEL_LAWS:
                try:
                    messages[channel.id] = client.history(channel.id, limit=lookback_messages)
                except DiscordApiError as exc:
                    errors.append({"gate": AOMS_WATCH, "platform": "discord", "kind": "history_read_failed", "channel": channel.name, "status": exc.status})
        findings, actions, snapshot_errors = audit_discord_snapshot(channels, messages)
        return findings, actions, snapshot_errors + errors
    except ValueError:
        return ([], [], [{"gate": AOMS_BLOCK, "platform": "discord", "kind": "missing_discord_token"}])
    except DiscordApiError as exc:
        gate = AOMS_BLOCK if exc.status in {401, 403} else AOMS_WATCH
        return ([], [], [{"gate": gate, "platform": "discord", "kind": "discord_api_error", "method": exc.method, "status": exc.status}])
    except Exception as exc:
        return ([], [], [{"gate": AOMS_WATCH, "platform": "discord", "kind": "discord_read_failed", "error": type(exc).__name__}])


def _audit_discord_channel(channel_name: str, messages: Sequence[DiscordMessageSnapshot]) -> tuple[list[Finding], list[ProposedAction]]:
    findings: list[Finding] = []
    actions: list[ProposedAction] = []
    if channel_name == "general":
        leaks = [m for m in messages if any(p.search(m.content) for p in RECEIPT_PATTERNS) or any(p.search(m.content) for p in ALERT_PATTERNS)]
        if leaks:
            action = make_action(AOMS_WATCH, "discord", "reroute_general_ops", channel_name, "Move operational Discord messages out of #general", "General is for warmth/personal conversation, not receipts/alerts.", {"samples": sample_discord(leaks)})
            actions.append(action)
            findings.append(Finding(AOMS_WATCH, "discord", "general_ops_leak", channel_name, "Discord #general contains receipt/alert-like operational posts.", {"count": len(leaks), "samples": sample_discord(leaks)}, (action.id,)))
    elif channel_name == "receipts":
        bad = [m for m in messages if m.content.strip() and (not has_speech_act(m.content, {"RECEIPT", "HANDOFF"}) or not any(p.search(m.content) for p in EVIDENCE_PATTERNS))]
        if bad:
            action = make_action(AOMS_WATCH, "discord", "enforce_receipt_envelope", channel_name, "Require RECEIPT/HANDOFF plus evidence refs in #receipts", "Receipt close must carry L3+ evidence or refs.", {"samples": sample_discord(bad)})
            actions.append(action)
            findings.append(Finding(AOMS_WATCH, "discord", "receipt_envelope_drift", channel_name, "Discord #receipts has messages without valid receipt/handoff evidence envelope.", {"count": len(bad), "samples": sample_discord(bad)}, (action.id,)))
    elif channel_name == "alerts":
        routine = [m for m in messages if any(p.search(m.content) for p in ROUTINE_NOISE_PATTERNS) and not any(p.search(m.content) for p in ALERT_PATTERNS)]
        if routine:
            action = make_action(AOMS_WATCH, "discord", "route_routine_out_of_alerts", channel_name, "Keep Discord #alerts for P0/P1 only", "Routine heartbeat/cycle noise belongs in logs/Slack organism-pulse, not backup alerts.", {"samples": sample_discord(routine)})
            actions.append(action)
            findings.append(Finding(AOMS_WATCH, "discord", "routine_alert_noise", channel_name, "Discord #alerts has routine noise without P0/P1 severity.", {"count": len(routine), "samples": sample_discord(routine)}, (action.id,)))
    elif channel_name == "organism":
        bot_messages = [m for m in messages if m.author_bot and m.content.strip()]
        no_act = [m for m in bot_messages if not has_speech_act(m.content)]
        if no_act:
            action = make_action(AOMS_WATCH, "discord", "enforce_speech_act", channel_name, "Require speech acts for bot posts in #organism", "Agent Oneness Protocol requires one speech act per inter-agent message.", {"samples": sample_discord(no_act)})
            actions.append(action)
            findings.append(Finding(AOMS_WATCH, "discord", "missing_speech_act", channel_name, "Discord #organism has bot posts without canonical speech acts.", {"count": len(no_act), "samples": sample_discord(no_act)}, (action.id,)))
    return findings, actions


def _convert_external_report(platform: str, report: Mapping[str, Any]) -> tuple[list[Finding], list[ProposedAction], list[dict[str, Any]]]:
    findings = [
        Finding(
            gate=str(item.get("gate") or AOMS_WATCH),
            platform=platform,
            kind=str(item.get("kind") or "finding"),
            target=str(item.get("channel") or item.get("target") or platform),
            summary=str(item.get("summary") or ""),
            evidence=dict(item.get("evidence") or {}),
            action_ids=tuple(item.get("action_ids") or ()),
        )
        for item in report.get("findings") or []
        if isinstance(item, Mapping)
    ]
    actions = [
        ProposedAction(
            id=str(item.get("id") or make_id(platform, str(item.get("action_type")), str(item.get("channel")))),
            gate=str(item.get("gate") or AOMS_WATCH),
            platform=platform,
            action_type=str(item.get("action_type") or "action"),
            target=str(item.get("channel") or item.get("target") or platform),
            summary=str(item.get("summary") or ""),
            reason=str(item.get("reason") or ""),
            dry_run=bool(item.get("dry_run", True)),
            requires_approval=bool(item.get("requires_approval", True)),
            payload=dict(item.get("payload") or {}),
        )
        for item in report.get("proposed_actions") or []
        if isinstance(item, Mapping)
    ]
    errors = [dict(error, platform=platform) for error in report.get("errors") or [] if isinstance(error, Mapping)]
    return findings, actions, errors


def _telegram_posture_from_config() -> dict[str, Any]:
    posture: dict[str, Any] = {}
    try:
        from hermes_cli.config import load_config
        config = load_config()
    except Exception:
        return posture
    telegram_cfg = config.get("telegram") if isinstance(config, Mapping) else None
    if isinstance(telegram_cfg, Mapping):
        if "enabled" in telegram_cfg:
            posture["enabled"] = bool(telegram_cfg.get("enabled"))
        if telegram_cfg.get("mode"):
            posture["mode"] = telegram_cfg.get("mode")
        if telegram_cfg.get("ttl_minutes") is not None:
            posture["ttl_minutes"] = telegram_cfg.get("ttl_minutes")
    platforms = config.get("platforms") if isinstance(config, Mapping) else None
    platform_telegram = platforms.get("telegram") if isinstance(platforms, Mapping) else None
    if isinstance(platform_telegram, Mapping) and "enabled" in platform_telegram:
        posture["enabled"] = bool(platform_telegram.get("enabled"))
    return posture


def _snapshot_discord_channels(snapshot: Mapping[str, Any]) -> list[DiscordChannelSnapshot]:
    return [DiscordChannelSnapshot.from_discord(ch) for ch in (snapshot.get("channels") or []) if isinstance(ch, Mapping)]


def _snapshot_discord_messages(snapshot: Mapping[str, Any]) -> dict[str, list[DiscordMessageSnapshot]]:
    out: dict[str, list[DiscordMessageSnapshot]] = {}
    raw = snapshot.get("messages") or {}
    if not isinstance(raw, Mapping):
        return out
    for key, items in raw.items():
        channel_id = str(key)
        out[channel_id] = [DiscordMessageSnapshot.from_discord(item, channel_id) for item in (items or []) if isinstance(item, Mapping)]
    return out


def draft_discord_channel_law(channel_name: str) -> str:
    name = normalize_name(channel_name)
    law = DISCORD_CHANNEL_LAWS.get(name)
    if not law:
        return f"Discord #{name}: define purpose, allowed speech acts, disallowed noise, and evidence requirements."
    return (
        f"Discord #{name} oneness law\n"
        f"Purpose: {law['purpose']}.\n"
        f"Allowed: {law['allowed']}.\n"
        f"Disallowed: {law['disallowed']}.\n"
        "Source of truth: git/council/.omni/pulse/receipts, not Discord itself."
    )


def has_speech_act(content: str, allowed: set[str] | None = None) -> bool:
    text = (content or "").strip()
    acts = allowed or set(DISCORD_SPEECH_ACTS)
    if not text:
        return False
    for act in acts:
        if re.match(rf"^(?:\[[^\]]+\]\s*)?{act}\b", text, re.I):
            return True
        if re.search(rf"\"kind\"\s*:\s*\"{act}\"", text, re.I):
            return True
    return False


def make_action(gate: str, platform: str, action_type: str, target: str, summary: str, reason: str, payload: Mapping[str, Any] | None = None) -> ProposedAction:
    payload_dict = dict(payload or {})
    return ProposedAction(
        id=make_id(platform, action_type, target, summary, reason, payload_dict),
        gate=gate,
        platform=platform,
        action_type=action_type,
        target=normalize_name(target),
        summary=summary,
        reason=reason,
        dry_run=True,
        requires_approval=True,
        payload=payload_dict,
    )


def make_id(*parts: Any) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    return "comms_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def aggregate_gate(gates: Iterable[str]) -> str:
    result = AOMS_PASS
    for gate in gates:
        if GATE_RANK.get(str(gate), 0) > GATE_RANK[result]:
            result = str(gate)
    return result


def normalize_name(name: str) -> str:
    return str(name or "").strip().lstrip("#").lower().replace(" ", "-")


def sample_discord(messages: Sequence[DiscordMessageSnapshot], *, limit: int = 3, chars: int = 180) -> list[str]:
    samples: list[str] = []
    for msg in messages[:limit]:
        text = redact_sensitive_text(re.sub(r"\s+", " ", msg.content).strip())
        if len(text) > chars:
            text = text[: chars - 1] + "…"
        samples.append(text)
    return samples


def _discord_topic_missing_law(channel_name: str, topic: str) -> bool:
    text = (topic or "").lower()
    if not text:
        return True
    return not any(word in text for word in ("speech", "receipt", "alert", "oneness", "evidence", "coordination"))


def render_report_text(report: CommsReport, *, max_findings: int = 8) -> str:
    if not report.findings and not report.errors:
        return f"Comms Steward {report.gate}: no material findings for {', '.join(report.platforms)}."
    lines = [f"Comms Steward {report.gate} · dry-run={str(report.dry_run).lower()}"]
    for finding in report.findings[:max_findings]:
        lines.append(f"• {finding.gate} {finding.platform}:{finding.target} {finding.kind}: {finding.summary}")
    remaining = max(0, max_findings - len(report.findings))
    for error in report.errors[:remaining]:
        lines.append(f"• {error.get('gate', AOMS_WATCH)} {error.get('platform', '?')} {error.get('kind')}: {error.get('error', error.get('status', ''))}")
    lines.append(f"Proposed actions: {len(report.proposed_actions)} (approval-gated; no comms writes performed).")
    return "\n".join(lines)


def _blocked_report(kind: str, summary: str) -> CommsReport:
    return CommsReport(
        ok=False,
        gate=AOMS_BLOCK,
        dry_run=True,
        generated_at=datetime.now(timezone.utc).isoformat(),
        platforms=DEFAULT_PLATFORMS,
        findings=(Finding(AOMS_BLOCK, "comms", kind, "comms", summary),),
        proposed_actions=(),
    )
