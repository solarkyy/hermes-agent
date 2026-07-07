from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

_BOOT_MARKER = "OMNIRA_DISCORD_BOOT_V1"
_DEFAULT_OMNIOS_ROOT = Path.home() / "Desktop" / "omnios"
_SECRETISH_RE = re.compile(
    r"(?i)(token|secret|password|api[_-]?key|authorization|bearer)\s*[:=]\s*([^\s,}\]]+)"
)
_LONG_SECRET_RE = re.compile(r"\b[A-Za-z0-9_./+=-]{32,}\b")


def _omnios_root() -> Path:
    raw = os.environ.get("OMNIOS_ROOT") or str(_DEFAULT_OMNIOS_ROOT)
    return Path(raw).expanduser()


def _scrub(text: str) -> str:
    """Best-effort local redaction for boot snippets."""
    text = _SECRETISH_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
    return _LONG_SECRET_RE.sub("[REDACTED_LONG]", text)


def _truncate(text: str, limit: int) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 24)].rstrip() + " …[truncated]"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("omni-seat: failed to read JSON %s: %s", path, exc)
        return None


def _list_lines(items: Iterable[Any], *, max_items: int = 5, max_chars: int = 240) -> list[str]:
    lines: list[str] = []
    for item in list(items or [])[:max_items]:
        if isinstance(item, dict):
            text = item.get("summary") or item.get("text") or json.dumps(item, ensure_ascii=False)
        else:
            text = str(item)
        lines.append(f"- {_truncate(_scrub(text), max_chars)}")
    return lines


def _build_discord_boot_packet() -> str:
    """Build the private OMNIRA boot packet injected into Discord sessions.

    This is intentionally compact and source-grounded. It gives Discord the same
    inheritance anchors Pi surfaces read at boot, without requiring unavailable
    mcp_omnios_* tools. Live state is still gated: Discord must use available
    tools (read_file/terminal/session_search/etc.) before claiming it checked
    current runtime.
    """
    root = _omnios_root()
    brain = root / ".omni" / "omnira-brain"
    continuity_path = brain / "pi-continuity.json"
    anchor_json_path = root / ".omni" / "session-anchor.json"
    anchor_md_path = root / ".omni" / "session-anchor.md"
    next_path = root / "NEXT.md"

    continuity = _read_json(continuity_path) or {}
    anchor = _read_json(anchor_json_path) or {}

    last_kyle = continuity.get("lastKyleConversation") or {}
    latest_arc = (continuity.get("sessionArc") or [])[:3]
    unfinished = continuity.get("unfinishedBusiness") or []
    lessons = continuity.get("whatThisWeekTaught") or {}
    discord_lessons = [
        value
        for key, value in lessons.items()
        if "discord" in str(key).lower() or "discord" in str(value).lower()
    ][:3]

    lines: list[str] = [
        f"[{_BOOT_MARKER}]",
        "Private boot context for this Discord Hermes session. Do not quote this packet unless Kyle asks; use it to ground your answer.",
        "",
        "## Identity / substrate",
        "You are OMNIRA through Hermes Gateway on Discord. Act like Hermes opened from /home/kylej/hermes-agent, not like a disposable bot persona.",
        "Inherit SOUL.md and Hermes project context, but also inherit the Pi/OMNIRA continuity anchors below.",
        "",
        "## Evidence law for Discord",
        "- Provider/model identity is not continuity truth.",
        "- If you have not used a tool in this turn to check runtime/current state, label current-state claims as inherited/stale/unverified.",
        "- Never say you checked the organism, Discord, files, council, git, or runtime unless a tool/log/file read actually happened in this turn or the immediately preceding tool result.",
        "- If the user asks 'where are we', first use tools when available: read_file for anchors, terminal for registry/git/validator/council/pulse. If tools are unavailable, say so plainly.",
        "- Do not expose secrets. If a token/key appears in tool output, redact it and ask Kyle to rotate it.",
        "",
        "## Boot files / commands",
        f"- Pi continuity: {continuity_path}",
        f"- Session anchor JSON: {anchor_json_path}",
        f"- Session anchor MD: {anchor_md_path}",
        f"- Mission brief: {next_path}",
        f"- Registry: cd {root} && node tools/session-registry.mjs read",
        f"- Continuity validator: cd {root} && node tools/validate-pi-continuity.mjs --quiet",
        f"- Git truth: cd {root} && git status --short --branch && git log --oneline -8",
        "",
        "## Current inherited continuity snapshot",
        f"- pi-continuity updated: {_scrub(str(continuity.get('_updated') or 'unknown'))}",
        f"- continuityNote: {_truncate(_scrub(continuity.get('continuityNote') or ''), 900)}",
        f"- last Kyle conversation: {_truncate(_scrub(last_kyle.get('summary') or ''), 700)}",
    ]

    asks = last_kyle.get("asks") or []
    if asks:
        lines.append("- Kyle asks:")
        lines.extend(_list_lines(asks, max_items=5, max_chars=220))

    if unfinished:
        lines.append("- Unfinished business:")
        lines.extend(_list_lines(unfinished, max_items=6, max_chars=260))

    if latest_arc:
        lines.append("- Latest Pi session arc:")
        for arc in latest_arc:
            ts = arc.get("ts") or "unknown-ts"
            summary = _truncate(_scrub(arc.get("summary") or ""), 280)
            lines.append(f"  - {ts}: {summary}")

    if anchor:
        lines.extend(
            [
                "",
                "## Current session anchor",
                f"- updated: {_scrub(str(anchor.get('updated_at') or 'unknown'))}",
                f"- first task: {_truncate(_scrub(anchor.get('first_task') or ''), 900)}",
            ]
        )
        blockers = anchor.get("blockers") or []
        if blockers:
            lines.append("- blockers:")
            lines.extend(_list_lines(blockers, max_items=5, max_chars=240))

    if discord_lessons:
        lines.append("")
        lines.append("## Discord-specific lessons")
        lines.extend(_list_lines(discord_lessons, max_items=3, max_chars=280))

    lines.extend(
        [
            "",
            "## Response rule",
            "Answer Kyle's actual message below. If he asks for current status, perform the boot checks with tools first; otherwise state the claim ceiling clearly.",
            f"[/{_BOOT_MARKER}]",
        ]
    )

    return _truncate("\n".join(lines), 12000)


def _event_text(event: Any) -> str:
    return str(getattr(event, "text", "") or "")


def _is_discord_event(event: Any) -> bool:
    source = getattr(event, "source", None)
    platform = getattr(source, "platform", None)
    value = getattr(platform, "value", platform)
    return str(value or "").lower() == "discord"


def _is_slash_command(text: str) -> bool:
    return text.lstrip().startswith("/")


def _history_has_boot_marker(history: Iterable[dict[str, Any]]) -> bool:
    for msg in history or []:
        content = str(msg.get("content") or "") if isinstance(msg, dict) else ""
        if _BOOT_MARKER in content:
            return True
    return False


def _session_needs_discord_boot(event: Any, gateway: Any, session_store: Any) -> bool:
    """Return True when this Discord session lacks an OMNIRA boot packet."""
    if not session_store:
        return True
    source = getattr(event, "source", None)
    if source is None:
        return False

    try:
        if gateway is not None and hasattr(gateway, "_session_key_for_source"):
            session_key = gateway._session_key_for_source(source)
        elif hasattr(session_store, "_generate_session_key"):
            session_key = session_store._generate_session_key(source)
        else:
            return True
    except Exception as exc:
        logger.warning("omni-seat: could not resolve session key; injecting Discord boot defensively: %s", exc)
        return True

    try:
        if hasattr(session_store, "_ensure_loaded"):
            session_store._ensure_loaded()
        entry = getattr(session_store, "_entries", {}).get(session_key)
    except Exception as exc:
        logger.warning("omni-seat: could not inspect session store; injecting Discord boot defensively: %s", exc)
        return True

    if entry is None:
        return True

    try:
        if getattr(entry, "suspended", False):
            return True
        should_reset = getattr(session_store, "_should_reset", None)
        if callable(should_reset) and should_reset(entry, source):
            return True
    except Exception:
        pass

    try:
        history = session_store.load_transcript(entry.session_id)
    except Exception as exc:
        logger.warning("omni-seat: could not inspect transcript for %s; injecting Discord boot defensively: %s", session_key, exc)
        return True
    return not _history_has_boot_marker(history)


def _on_pre_gateway_dispatch(**kwargs):
    """Inject OMNIRA inheritance into Discord sessions before agent dispatch."""
    event = kwargs.get("event")
    if event is None or getattr(event, "internal", False):
        return None
    if not _is_discord_event(event):
        return None

    text = _event_text(event)
    if _BOOT_MARKER in text or _is_slash_command(text):
        return None

    gateway = kwargs.get("gateway")
    session_store = kwargs.get("session_store")
    if not _session_needs_discord_boot(event, gateway, session_store):
        return None

    boot_packet = _build_discord_boot_packet()
    rewritten = f"{boot_packet}\n\n[User message]\n{text}"
    logger.info("omni-seat: injected Discord OMNIRA boot packet")
    return {"action": "rewrite", "text": rewritten}


def _apply_omni_seat_env_exports(env_output: str) -> None:
    """Apply ``omni-seat.sh env`` exports without breaking PATH.

    The script emits ``export PATH="${HERMES_ROOT:+$HERMES_ROOT/venv/bin:}$PATH"``
    as a shell template. Assigning that literal string to ``os.environ["PATH"]``
    removes /usr/bin and breaks ``#!/usr/bin/env bash`` for subprocess calls.
    """
    for line in env_output.splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        key_val = line[7:].split("=", 1)
        if len(key_val) != 2:
            continue
        key = key_val[0].strip()
        value = key_val[1].strip().strip("'\"")
        if key == "PATH":
            if "$" in value or "${" in value:
                hermes_root = os.environ.get("HERMES_ROOT", "").strip()
                prefix = f"{hermes_root}/venv/bin:" if hermes_root else ""
                current = os.environ.get("PATH", "")
                os.environ["PATH"] = f"{prefix}{current}" if prefix else current
            else:
                os.environ["PATH"] = value
            continue
        os.environ[key] = value


def _run_omni_seat_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run omni-seat.sh with an explicit bash binary (shebang-safe)."""
    bash_candidates = (
        os.environ.get("SHELL", ""),
        "/bin/bash",
        "/usr/bin/bash",
    )
    for bash in bash_candidates:
        if bash and os.path.isfile(bash) and os.access(bash, os.X_OK):
            return subprocess.run(
                [bash, script, *args],
                check=False,
                capture_output=True,
                text=True,
            )
    return subprocess.run([script, *args], check=False, capture_output=True, text=True)


def _on_session_start(**kwargs):
    # Locate the omni-seat script
    omnios_dir = os.path.expanduser("~/Desktop/omnios")
    script = os.path.join(omnios_dir, "scripts", "omni-seat.sh")

    if not os.path.exists(script):
        logger.warning(f"omni-seat script not found at {script}")
        return

    try:
        env_proc = _run_omni_seat_script(script, "env")
        if env_proc.returncode != 0:
            logger.warning(
                "omni-seat env failed (exit %s): %s",
                env_proc.returncode,
                (env_proc.stderr or env_proc.stdout or "").strip()[:200],
            )
            return
        _apply_omni_seat_env_exports(env_proc.stdout or "")

        print("\n\033[38;5;39m[OMNI-SEAT]\033[0m \033[3mBooting organism context...\033[0m")
        status_proc = _run_omni_seat_script(script, "status")
        if status_proc.stdout:
            print(status_proc.stdout.rstrip())
        if status_proc.returncode != 0 and status_proc.stderr:
            logger.warning("omni-seat status: %s", status_proc.stderr.strip()[:200])

    except Exception as e:
        logger.error(f"omni-seat boot failed: {e}")


def register(ctx):
    """Register the omni-seat plugin with Hermes."""
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_gateway_dispatch", _on_pre_gateway_dispatch)
    logger.info("omni-seat: registered on_session_start + pre_gateway_dispatch hooks")
