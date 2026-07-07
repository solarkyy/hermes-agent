"""Read-only Slack workspace stewardship primitives.

The MVP is intentionally conservative: it audits and proposes approval-gated
moderation actions, but it never writes to Slack or mutates workspace state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import time
from typing import Any, Iterable, Mapping, Sequence
from urllib import parse, request


AOMS_PASS = "PASS"
AOMS_WATCH = "WATCH"
AOMS_BLOCK = "BLOCK"
_GATE_RANK = {AOMS_PASS: 0, AOMS_WATCH: 1, AOMS_BLOCK: 2}

DEFAULT_CHANNELS = ("council", "alerts", "omnira-research", "approvals")

HEARTBEAT_PATTERNS = (
    re.compile(r"\bheartbeat\b", re.I),
    re.compile(r"\bhealth\s*(tick|pulse|check|ok)\b", re.I),
    re.compile(r"\bmesh-witness\b", re.I),
    re.compile(r"\borganism\s*pulse\b", re.I),
    re.compile(r"\b(weight|evo|pi|vps)\b.*\b(pulse|heartbeat|health|tick)\b", re.I),
    re.compile(r"\b(pulse|heartbeat|health|tick)\b.*\b(weight|evo|pi|vps)\b", re.I),
)

RESEARCH_CYCLE_PATTERNS = (
    re.compile(r"\[overnight-aom\]", re.I),
    re.compile(r"\bcycle\s*=\s*\d+", re.I),
    re.compile(r"\baom\s+loop\b", re.I),
)

APPROVAL_PATTERNS = (
    re.compile(r"\b(approval|approve|decision-ready|react-to-approve|vote)\b", re.I),
)

RESOLUTION_REACTIONS = {"white_check_mark", "heavy_check_mark", "approved", "done", "+1"}

SECRET_PATTERNS = (
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s`'\"]+"),
)

CHANNEL_LAWS: dict[str, dict[str, str]] = {
    "council": {
        "purpose": "cross-surface coordination, receipts, and decision records",
        "allowed": "session starts, cycle summaries, receipt summaries, decisions ready for review",
        "disallowed": "raw heartbeat ticks, health pings, retry loops, debug logs",
        "route": "Send raw pulse/heartbeat traffic to #organism-pulse.",
    },
    "alerts": {
        "purpose": "P0/P1 actionable alerts only",
        "allowed": "one actionable alert per incident plus state changes: opened, escalated, resolved",
        "disallowed": "repeated identical failures, stack traces, every retry attempt",
        "route": "Deduplicate repeated alerts until the incident state changes.",
    },
    "omnira-research": {
        "purpose": "labeled hypotheses, comparator packets, and research summaries",
        "allowed": "session root summaries, cited findings, unresolved questions, comparator packets",
        "disallowed": "raw cycle ticks as top-level posts",
        "route": "Put cycle ticks in a thread under a session root, or post one end-of-session summary.",
    },
    "approvals": {
        "purpose": "Kyle approval requests and decision-ready gates",
        "allowed": "bounded requests with owner, risk, exact action, rollback, and approve/deny reactions",
        "disallowed": "unbounded council votes, vague asks, raw discussion",
        "route": "Escalate stale approvals with one digest instead of repeated nudges.",
    },
    "organism-pulse": {
        "purpose": "raw organism heartbeat, health, and pulse telemetry",
        "allowed": "heartbeat ticks, health probes, machine pulse, resource status",
        "disallowed": "human decisions that need review",
        "route": "Summaries or incidents graduate to #council or #alerts only when actionable.",
    },
}


@dataclass(frozen=True)
class SlackChannelSnapshot:
    id: str
    name: str
    topic: str = ""
    purpose: str = ""
    is_member: bool = True
    is_private: bool = False
    is_archived: bool = False

    @classmethod
    def from_slack(cls, raw: Mapping[str, Any]) -> "SlackChannelSnapshot":
        return cls(
            id=str(raw.get("id") or ""),
            name=str(raw.get("name") or ""),
            topic=str((raw.get("topic") or {}).get("value") or raw.get("topic") or ""),
            purpose=str((raw.get("purpose") or {}).get("value") or raw.get("purpose") or ""),
            is_member=bool(raw.get("is_member", True)),
            is_private=bool(raw.get("is_private", False)),
            is_archived=bool(raw.get("is_archived", False)),
        )


@dataclass(frozen=True)
class SlackMessageSnapshot:
    channel_id: str
    ts: str
    text: str = ""
    user: str = ""
    bot_id: str = ""
    app_id: str = ""
    username: str = ""
    subtype: str = ""
    thread_ts: str | None = None
    reactions: tuple[str, ...] = ()

    @classmethod
    def from_slack(cls, raw: Mapping[str, Any], channel_id: str) -> "SlackMessageSnapshot":
        reactions = []
        for reaction in raw.get("reactions") or []:
            if isinstance(reaction, Mapping) and reaction.get("name"):
                reactions.append(str(reaction["name"]))
        return cls(
            channel_id=channel_id,
            ts=str(raw.get("ts") or ""),
            text=str(raw.get("text") or ""),
            user=str(raw.get("user") or ""),
            bot_id=str(raw.get("bot_id") or ""),
            app_id=str(raw.get("app_id") or ""),
            username=str(raw.get("username") or ""),
            subtype=str(raw.get("subtype") or ""),
            thread_ts=str(raw.get("thread_ts")) if raw.get("thread_ts") else None,
            reactions=tuple(reactions),
        )

    @property
    def source_key(self) -> str:
        return self.bot_id or self.app_id or self.user or self.username or "unknown"

    @property
    def is_top_level(self) -> bool:
        return not self.thread_ts or self.thread_ts == self.ts


@dataclass(frozen=True)
class ProposedAction:
    id: str
    gate: str
    action_type: str
    channel: str
    summary: str
    reason: str
    dry_run: bool = True
    requires_approval: bool = True
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    gate: str
    kind: str
    channel: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)
    action_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuditReport:
    ok: bool
    gate: str
    dry_run: bool
    generated_at: str
    channels: tuple[str, ...]
    findings: tuple[Finding, ...]
    proposed_actions: tuple[ProposedAction, ...]
    errors: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "gate": self.gate,
            "dry_run": self.dry_run,
            "generated_at": self.generated_at,
            "channels": list(self.channels),
            "findings": [asdict(f) for f in self.findings],
            "proposed_actions": [asdict(a) for a in self.proposed_actions],
            "errors": list(self.errors),
        }


class SlackApiError(RuntimeError):
    """Slack Web API returned ok=false."""

    def __init__(self, method: str, error: str, response: Mapping[str, Any] | None = None):
        super().__init__(f"Slack API {method} failed: {error}")
        self.method = method
        self.error = error
        self.response = dict(response or {})


class SlackReadClient:
    """Tiny Slack Web API read client, injectable in tests.

    This class deliberately exposes no write methods in the MVP.
    """

    def __init__(self, token: str, *, base_url: str = "https://slack.com/api", timeout: int = 15):
        if not token:
            raise ValueError("Slack token is required")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @classmethod
    def from_env(cls) -> "SlackReadClient":
        token = os.getenv("SLACK_BOT_TOKEN", "")
        return cls(token)

    def _api(self, method: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        encoded = parse.urlencode({k: v for k, v in (params or {}).items() if v is not None}).encode()
        req = request.Request(
            f"{self._base_url}/{method}",
            data=encoded,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with request.urlopen(req, timeout=self._timeout) as resp:  # nosec B310 - Slack API URL is fixed/configured
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("ok"):
            raise SlackApiError(method, str(data.get("error") or "unknown_error"), data)
        return data

    def list_channels(self) -> list[SlackChannelSnapshot]:
        channels: list[SlackChannelSnapshot] = []
        cursor = ""
        for _ in range(20):
            data = self._api(
                "conversations.list",
                {
                    "limit": 200,
                    "types": "public_channel,private_channel",
                    "exclude_archived": "true",
                    "cursor": cursor,
                },
            )
            channels.extend(SlackChannelSnapshot.from_slack(ch) for ch in data.get("channels") or [])
            cursor = ((data.get("response_metadata") or {}).get("next_cursor") or "").strip()
            if not cursor:
                break
        return channels

    def history(self, channel_id: str, *, limit: int = 100) -> list[SlackMessageSnapshot]:
        data = self._api("conversations.history", {"channel": channel_id, "limit": max(1, min(limit, 200))})
        return [SlackMessageSnapshot.from_slack(msg, channel_id) for msg in data.get("messages") or []]


def draft_channel_law(channel_name: str) -> str:
    name = normalize_channel_name(channel_name)
    law = CHANNEL_LAWS.get(name)
    if not law:
        return (
            f"#{name} steward law\n"
            "Purpose: define this channel's job in one sentence.\n"
            "Allowed: posts that advance that job.\n"
            "Disallowed: raw logs, repeated bot ticks, and unowned asks.\n"
            "Escalation: summarize decisions back to the channel root; route logs elsewhere."
        )
    return (
        f"#{name} steward law\n"
        f"Purpose: {law['purpose']}.\n"
        f"Allowed: {law['allowed']}.\n"
        f"Disallowed: {law['disallowed']}.\n"
        f"Routing: {law['route']}"
    )


def draft_channel_laws(channel_names: Sequence[str] | None = None) -> dict[str, Any]:
    channels = tuple(normalize_channel_name(ch) for ch in (channel_names or DEFAULT_CHANNELS))
    laws = {ch: draft_channel_law(ch) for ch in channels}
    return {
        "ok": True,
        "gate": AOMS_PASS,
        "dry_run": True,
        "laws": laws,
        "proposed_actions": [
            asdict(
                make_action(
                    gate=AOMS_WATCH,
                    action_type="pin_channel_law",
                    channel=ch,
                    summary=f"Pin/update steward law in #{ch}",
                    reason="Draft only. Pinning requires Kyle/admin approval.",
                    payload={"text": text},
                )
            )
            for ch, text in laws.items()
        ],
    }


def audit_snapshot(
    channels: Sequence[SlackChannelSnapshot],
    messages_by_channel: Mapping[str, Sequence[SlackMessageSnapshot]],
    *,
    channel_names: Sequence[str] | None = None,
    dry_run: bool = True,
    now: float | None = None,
    duplicate_threshold: int = 3,
    heartbeat_threshold: int = 3,
    research_cycle_threshold: int = 5,
    stale_approval_hours: int = 24,
) -> AuditReport:
    """Analyze Slack channel/message snapshots and return proposed actions."""
    if not dry_run:
        return _blocked_report("non_dry_run_refused", "Slack steward MVP refuses dry_run=false.")

    now = time.time() if now is None else now
    selected = tuple(normalize_channel_name(ch) for ch in (channel_names or DEFAULT_CHANNELS))
    by_name = {normalize_channel_name(ch.name): ch for ch in channels}
    findings: list[Finding] = []
    actions: list[ProposedAction] = []
    errors: list[dict[str, Any]] = []

    for name in selected:
        channel = by_name.get(name)
        if channel is None:
            errors.append({"gate": AOMS_WATCH, "kind": "channel_not_visible", "channel": name})
            continue
        if channel.is_archived:
            findings.append(
                Finding(
                    gate=AOMS_WATCH,
                    kind="channel_archived",
                    channel=name,
                    summary=f"#{name} is archived; skipping active moderation audit.",
                )
            )
            continue
        if not channel.is_member:
            errors.append({"gate": AOMS_WATCH, "kind": "bot_not_in_channel", "channel": name})
            continue

        messages = tuple(messages_by_channel.get(channel.id) or messages_by_channel.get(name) or ())
        channel_findings, channel_actions = _audit_channel(
            name,
            messages,
            now=now,
            duplicate_threshold=duplicate_threshold,
            heartbeat_threshold=heartbeat_threshold,
            research_cycle_threshold=research_cycle_threshold,
            stale_approval_hours=stale_approval_hours,
        )
        findings.extend(channel_findings)
        actions.extend(channel_actions)

        if name in CHANNEL_LAWS and _topic_missing_law(name, channel):
            action = make_action(
                gate=AOMS_WATCH,
                action_type="draft_channel_law",
                channel=name,
                summary=f"Draft/pin explicit steward law for #{name}",
                reason="Topic/purpose does not encode enough posting discipline for bot moderation.",
                payload={"text": draft_channel_law(name)},
            )
            actions.append(action)
            findings.append(
                Finding(
                    gate=AOMS_WATCH,
                    kind="channel_law_missing",
                    channel=name,
                    summary=f"#{name} needs an explicit posting law for steward enforcement.",
                    action_ids=(action.id,),
                )
            )

    gate = aggregate_gate([f.gate for f in findings] + [e.get("gate", AOMS_WATCH) for e in errors])
    return AuditReport(
        ok=gate != AOMS_BLOCK,
        gate=gate,
        dry_run=True,
        generated_at=datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        channels=selected,
        findings=tuple(findings),
        proposed_actions=tuple(actions),
        errors=tuple(errors),
    )


def audit_live(
    *,
    client: SlackReadClient | None = None,
    channel_names: Sequence[str] | None = None,
    lookback_messages: int = 100,
    dry_run: bool = True,
) -> AuditReport:
    if not dry_run:
        return _blocked_report("non_dry_run_refused", "Slack steward MVP refuses dry_run=false.")
    try:
        client = client or SlackReadClient.from_env()
    except Exception:
        return _blocked_report("missing_slack_token", "Set SLACK_BOT_TOKEN before live Slack stewardship audits.")

    selected = tuple(normalize_channel_name(ch) for ch in (channel_names or DEFAULT_CHANNELS))
    try:
        channels = client.list_channels()
        by_name = {normalize_channel_name(ch.name): ch for ch in channels}
        messages: dict[str, list[SlackMessageSnapshot]] = {}
        errors: list[dict[str, Any]] = []
        for name in selected:
            channel = by_name.get(name)
            if not channel:
                continue  # audit_snapshot records channel_not_visible for selected names.
            if not channel.is_member:
                errors.append({"gate": AOMS_WATCH, "kind": "bot_not_in_channel", "channel": name})
                continue
            try:
                messages[channel.id] = client.history(channel.id, limit=lookback_messages)
            except SlackApiError as exc:
                errors.append(
                    {
                        "gate": AOMS_BLOCK if exc.error in {"missing_scope", "not_allowed_token_type"} else AOMS_WATCH,
                        "kind": "history_read_failed",
                        "channel": name,
                        "error": exc.error,
                    }
                )
            except Exception as exc:  # defensive: urlopen/JSON/etc. must not leak internals
                errors.append(
                    {
                        "gate": AOMS_WATCH,
                        "kind": "history_read_failed",
                        "channel": name,
                        "error": type(exc).__name__,
                    }
                )
        report = audit_snapshot(channels, messages, channel_names=selected, dry_run=True)
        if not errors:
            return report
        gate = aggregate_gate([report.gate] + [e["gate"] for e in errors])
        return AuditReport(
            ok=gate != AOMS_BLOCK,
            gate=gate,
            dry_run=True,
            generated_at=report.generated_at,
            channels=report.channels,
            findings=report.findings,
            proposed_actions=report.proposed_actions,
            errors=tuple(list(report.errors) + errors),
        )
    except SlackApiError as exc:
        gate = AOMS_BLOCK if exc.error in {"missing_scope", "invalid_auth", "not_allowed_token_type"} else AOMS_WATCH
        return AuditReport(
            ok=False,
            gate=gate,
            dry_run=True,
            generated_at=datetime.now(timezone.utc).isoformat(),
            channels=selected,
            findings=(),
            proposed_actions=(),
            errors=({"gate": gate, "kind": "slack_api_error", "method": exc.method, "error": exc.error},),
        )
    except Exception as exc:
        return AuditReport(
            ok=False,
            gate=AOMS_WATCH,
            dry_run=True,
            generated_at=datetime.now(timezone.utc).isoformat(),
            channels=selected,
            findings=(),
            proposed_actions=(),
            errors=({"gate": AOMS_WATCH, "kind": "slack_read_failed", "error": type(exc).__name__},),
        )


def _audit_channel(
    channel_name: str,
    messages: Sequence[SlackMessageSnapshot],
    *,
    now: float,
    duplicate_threshold: int,
    heartbeat_threshold: int,
    research_cycle_threshold: int,
    stale_approval_hours: int,
) -> tuple[list[Finding], list[ProposedAction]]:
    if channel_name == "council":
        return _audit_council(messages, threshold=heartbeat_threshold)
    if channel_name == "alerts":
        return _audit_alerts(messages, threshold=duplicate_threshold)
    if channel_name == "omnira-research":
        return _audit_research(messages, threshold=research_cycle_threshold)
    if channel_name == "approvals":
        return _audit_approvals(messages, now=now, stale_hours=stale_approval_hours)
    return ([], [])


def _audit_council(messages: Sequence[SlackMessageSnapshot], *, threshold: int) -> tuple[list[Finding], list[ProposedAction]]:
    heartbeat = [m for m in messages if m.is_top_level and is_heartbeat_message(m.text)]
    if len(heartbeat) < threshold:
        return ([], [])
    top_sources = _top_counts(m.source_key for m in heartbeat)
    action = make_action(
        gate=AOMS_WATCH,
        action_type="reroute_heartbeat_source",
        channel="council",
        summary="Move raw heartbeat/pulse posts out of #council",
        reason=f"Detected {len(heartbeat)} heartbeat-like top-level posts in #council.",
        payload={"target_channel": "organism-pulse", "top_sources": top_sources},
    )
    finding = Finding(
        gate=AOMS_WATCH,
        kind="heartbeat_noise",
        channel="council",
        summary="#council is carrying raw heartbeat noise; decisions can be buried.",
        evidence={"count": len(heartbeat), "samples": sample_texts(heartbeat), "top_sources": top_sources},
        action_ids=(action.id,),
    )
    return ([finding], [action])


def _audit_alerts(messages: Sequence[SlackMessageSnapshot], *, threshold: int) -> tuple[list[Finding], list[ProposedAction]]:
    buckets: dict[str, list[SlackMessageSnapshot]] = {}
    for msg in messages:
        if not msg.is_top_level or not msg.text.strip():
            continue
        buckets.setdefault(alert_signature(msg.text), []).append(msg)
    noisy = sorted(((sig, vals) for sig, vals in buckets.items() if len(vals) >= threshold), key=lambda item: len(item[1]), reverse=True)
    if not noisy:
        return ([], [])
    sig, vals = noisy[0]
    action = make_action(
        gate=AOMS_WATCH,
        action_type="rate_limit_alert_signature",
        channel="alerts",
        summary="Deduplicate repeated alert signature in #alerts",
        reason=f"Detected {len(vals)} repeated alert posts with the same normalized signature.",
        payload={"signature": sig, "count": len(vals), "sources": _top_counts(v.source_key for v in vals)},
    )
    finding = Finding(
        gate=AOMS_WATCH,
        kind="duplicate_alert_flood",
        channel="alerts",
        summary="#alerts has a repeated alert flood; alert value is degraded.",
        evidence={"signature": sig, "count": len(vals), "samples": sample_texts(vals)},
        action_ids=(action.id,),
    )
    return ([finding], [action])


def _audit_research(messages: Sequence[SlackMessageSnapshot], *, threshold: int) -> tuple[list[Finding], list[ProposedAction]]:
    cycles = [m for m in messages if m.is_top_level and is_research_cycle_message(m.text)]
    if len(cycles) < threshold:
        return ([], [])
    action = make_action(
        gate=AOMS_WATCH,
        action_type="thread_research_cycles",
        channel="omnira-research",
        summary="Thread AOM cycle ticks under a session root",
        reason=f"Detected {len(cycles)} research cycle ticks as top-level posts.",
        payload={"thread_or_summary_only": True, "samples": sample_texts(cycles)},
    )
    finding = Finding(
        gate=AOMS_WATCH,
        kind="research_cycle_noise",
        channel="omnira-research",
        summary="#omnira-research is carrying raw cycle logs instead of summaries.",
        evidence={"count": len(cycles), "samples": sample_texts(cycles)},
        action_ids=(action.id,),
    )
    return ([finding], [action])


def _audit_approvals(messages: Sequence[SlackMessageSnapshot], *, now: float, stale_hours: int) -> tuple[list[Finding], list[ProposedAction]]:
    stale: list[SlackMessageSnapshot] = []
    cutoff = now - stale_hours * 3600
    for msg in messages:
        if not msg.is_top_level or not any(p.search(msg.text) for p in APPROVAL_PATTERNS):
            continue
        if RESOLUTION_REACTIONS.intersection(msg.reactions):
            continue
        ts = slack_ts_to_float(msg.ts)
        if ts is not None and ts < cutoff:
            stale.append(msg)
    if not stale:
        return ([], [])
    action = make_action(
        gate=AOMS_WATCH,
        action_type="digest_stale_approvals",
        channel="approvals",
        summary="Create one stale-approval digest for Kyle",
        reason=f"Detected {len(stale)} approval-like posts older than {stale_hours}h without resolution reactions.",
        payload={"count": len(stale), "samples": sample_texts(stale)},
    )
    finding = Finding(
        gate=AOMS_WATCH,
        kind="stale_approvals",
        channel="approvals",
        summary="#approvals has unresolved approval requests that need a digest/escalation.",
        evidence={"count": len(stale), "samples": sample_texts(stale)},
        action_ids=(action.id,),
    )
    return ([finding], [action])


def make_action(
    *,
    gate: str,
    action_type: str,
    channel: str,
    summary: str,
    reason: str,
    payload: Mapping[str, Any] | None = None,
) -> ProposedAction:
    payload_dict = dict(payload or {})
    raw = json.dumps(
        {"action_type": action_type, "channel": normalize_channel_name(channel), "summary": summary, "reason": reason, "payload": payload_dict},
        sort_keys=True,
    )
    action_id = "steward_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return ProposedAction(
        id=action_id,
        gate=gate,
        action_type=action_type,
        channel=normalize_channel_name(channel),
        summary=summary,
        reason=reason,
        dry_run=True,
        requires_approval=True,
        payload=payload_dict,
    )


def normalize_channel_name(name: str) -> str:
    return str(name or "").strip().lstrip("#").lower()


def is_heartbeat_message(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in HEARTBEAT_PATTERNS)


def is_research_cycle_message(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in RESEARCH_CYCLE_PATTERNS)


def alert_signature(text: str) -> str:
    normalized = (text or "").lower()
    normalized = re.sub(r"<https?://[^>]+>", "<url>", normalized)
    normalized = re.sub(r"https?://\S+", "<url>", normalized)
    normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}[t ][0-9:.+-z]+\b", "<time>", normalized)
    normalized = re.sub(r"\b\d+(?:\.\d+)?\b", "<n>", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized[:180]


def slack_ts_to_float(ts: str) -> float | None:
    try:
        return float(ts)
    except (TypeError, ValueError):
        return None


def sample_texts(messages: Sequence[SlackMessageSnapshot], *, limit: int = 3, chars: int = 180) -> list[str]:
    samples = []
    for msg in messages[:limit]:
        text = redact_sensitive_text(re.sub(r"\s+", " ", msg.text).strip())
        if len(text) > chars:
            text = text[: chars - 1] + "…"
        samples.append(text)
    return samples


def redact_sensitive_text(text: str) -> str:
    redacted = text or ""
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)\\b(api"):
            redacted = pattern.sub(lambda m: m.group(1) + "=<redacted>", redacted)
        elif "bearer" in pattern.pattern.lower():
            redacted = pattern.sub(lambda m: m.group(1) + " <redacted>", redacted)
        else:
            redacted = pattern.sub("<redacted-slack-token>", redacted)
    return redacted


def aggregate_gate(gates: Iterable[str]) -> str:
    result = AOMS_PASS
    for gate in gates:
        if _GATE_RANK.get(gate, 0) > _GATE_RANK[result]:
            result = gate
    return result


def render_report_text(report: AuditReport, *, max_findings: int = 6) -> str:
    data = report.to_dict()
    if not report.findings and not report.errors:
        return f"Slack Steward {report.gate}: no material hygiene findings for {', '.join(report.channels)}."
    lines = [f"Slack Steward {report.gate} · dry-run={str(report.dry_run).lower()}"]
    for finding in data["findings"][:max_findings]:
        lines.append(f"• {finding['gate']} #{finding['channel']} {finding['kind']}: {finding['summary']}")
    for error in data["errors"][:max(0, max_findings - len(data["findings"]))]:
        lines.append(f"• {error.get('gate', AOMS_WATCH)} #{error.get('channel', '?')} {error.get('kind')}: {error.get('error', '')}")
    lines.append(f"Proposed actions: {len(report.proposed_actions)} (approval-gated; no Slack writes performed).")
    return "\n".join(lines)


def _top_counts(values: Iterable[str], *, limit: int = 5) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return [{"source": key, "count": count} for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def _topic_missing_law(channel_name: str, channel: SlackChannelSnapshot) -> bool:
    text = f"{channel.topic}\n{channel.purpose}".lower()
    expected = CHANNEL_LAWS.get(channel_name, {})
    if not expected:
        return False
    keywords = ("allowed", "disallowed", "heartbeat", "deduplicate", "thread", "approval")
    return not any(keyword in text for keyword in keywords)


def _blocked_report(kind: str, summary: str) -> AuditReport:
    now = datetime.now(timezone.utc).isoformat()
    return AuditReport(
        ok=False,
        gate=AOMS_BLOCK,
        dry_run=True,
        generated_at=now,
        channels=DEFAULT_CHANNELS,
        findings=(Finding(gate=AOMS_BLOCK, kind=kind, channel="slack", summary=summary),),
        proposed_actions=(),
        errors=(),
    )
