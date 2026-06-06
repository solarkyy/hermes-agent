#!/usr/bin/env python3
"""Phone microphone relay for SSH-hosted Hermes/Pi sessions.

Raw SSH cannot access a phone microphone. This tiny localhost web service lets a
phone browser record audio, send it through an SSH local port forward, transcribe
it with Hermes STT on the remote machine, and optionally paste the resulting text
into a tmux pane as a draft.

Default posture is intentionally safe:

* binds to 127.0.0.1;
* requires a random per-run token for API calls;
* never presses Enter / auto-sends unless --allow-send is explicitly set;
* tmux paste is opt-in via --tmux-target.
"""

from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from tools.transcription_tools import transcribe_audio

Transcriber = Callable[[str, Optional[str]], dict[str, Any]]


CONTENT_TYPE_EXTENSIONS = {
    "audio/webm": ".webm",
    "video/webm": ".webm",
    "audio/ogg": ".ogg",
    "application/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".mp4",
    "video/mp4": ".mp4",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "application/octet-stream": ".webm",
}


@dataclass(slots=True)
class RelayConfig:
    host: str = "127.0.0.1"
    port: int = 8788
    token: str = field(default_factory=lambda: secrets.token_urlsafe(18))
    model: Optional[str] = None
    temp_dir: str = field(default_factory=lambda: os.path.join(tempfile.gettempdir(), "hermes_phone_voice"))
    max_bytes: int = 25 * 1024 * 1024
    tmux_target: Optional[str] = None
    allow_send: bool = False
    allow_remote: bool = False
    transcriber: Transcriber = transcribe_audio


def _is_loopback_host(host: str) -> bool:
    """Return whether ``host`` is safe for the default token-in-browser relay."""
    normalized = (host or "").strip().lower()
    if normalized in {"localhost", "ip6-localhost"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _redact_token_from_text(text: str, token: str) -> str:
    """Remove bearer-like token material from logs and diagnostics."""
    redacted = str(text or "")
    if token:
        redacted = redacted.replace(token, "<redacted-token>")
    parsed = urlparse(redacted)
    if parsed.query:
        query = parse_qs(parsed.query, keep_blank_values=True)
        if "token" in query:
            query["token"] = ["<redacted-token>"]
            redacted = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
    return redacted


def _extension_for_content_type(content_type: str) -> str:
    """Return a supported audio suffix for a browser MediaRecorder MIME type."""
    media_type = (content_type or "").split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(media_type, ".webm")


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _write_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = _json_bytes(payload)
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler: BaseHTTPRequestHandler, *, max_bytes: int = 256 * 1024) -> dict[str, Any]:
    raw_length = handler.headers.get("Content-Length") or "0"
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise ValueError("invalid Content-Length") from exc
    if length <= 0:
        return {}
    if length > max_bytes:
        raise ValueError("JSON body too large")
    body = handler.rfile.read(length)
    if not body:
        return {}
    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON body") from exc
    if not isinstance(parsed, dict):
        raise ValueError("JSON body must be an object")
    return parsed


def _authorized(handler: BaseHTTPRequestHandler, token: str) -> bool:
    if not token:
        return True
    header_token = handler.headers.get("X-Voice-Relay-Token", "")
    if secrets.compare_digest(header_token, token):
        return True
    query = parse_qs(urlparse(handler.path).query)
    query_token = (query.get("token") or [""])[0]
    return secrets.compare_digest(query_token, token)


def draft_to_tmux(
    text: str,
    *,
    target: Optional[str],
    send: bool = False,
    tmux_bin: str = "tmux",
    timeout: float = 5.0,
) -> None:
    """Paste ``text`` into a tmux pane, optionally pressing Enter.

    ``text`` is passed as an argv element to ``tmux set-buffer`` rather than
    through a shell, so shell metacharacters in dictated text are not executed.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        raise ValueError("empty transcript")
    if not target:
        raise ValueError("tmux target not configured; pass --tmux-target")
    if not shutil.which(tmux_bin):
        raise RuntimeError(f"{tmux_bin!r} not found")

    subprocess.run([tmux_bin, "set-buffer", clean_text], check=True, timeout=timeout)
    paste_cmd = [tmux_bin, "paste-buffer", "-t", target]
    subprocess.run(paste_cmd, check=True, timeout=timeout)
    if send:
        subprocess.run([tmux_bin, "send-keys", "-t", target, "Enter"], check=True, timeout=timeout)


def render_index(config: RelayConfig) -> str:
    payload = {
        "tmuxTarget": config.tmux_target or "",
        "allowSend": config.allow_send,
        "maxBytes": config.max_bytes,
    }
    cfg_json = json.dumps(payload)
    target_label = html.escape(config.tmux_target or "not configured")
    send_label = "enabled" if config.allow_send else "disabled"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>Hermes Phone Voice Relay</title>
<style>
  :root {{ color-scheme: dark; --bg:#0b0f14; --panel:#121923; --text:#e9f1ff; --muted:#91a0b6; --accent:#8bd3ff; --warn:#ffd28b; --bad:#ff8b8b; }}
  body {{ margin:0; padding:18px; font:16px/1.45 system-ui,-apple-system,Segoe UI,sans-serif; background:var(--bg); color:var(--text); }}
  main {{ max-width:760px; margin:0 auto; }}
  h1 {{ font-size:1.35rem; margin:.2rem 0 .4rem; }}
  .card {{ background:var(--panel); border:1px solid #253247; border-radius:16px; padding:14px; margin:12px 0; box-shadow:0 10px 30px #0005; }}
  .row {{ display:flex; flex-wrap:wrap; gap:10px; margin:10px 0; }}
  button {{ flex:1 1 140px; border:0; border-radius:12px; padding:13px 14px; font-weight:700; background:#1f6feb; color:white; }}
  button.secondary {{ background:#263243; }}
  button.warn {{ background:#8a5b16; }}
  button.danger {{ background:#8a2424; }}
  button:disabled {{ opacity:.45; }}
  textarea {{ box-sizing:border-box; width:100%; min-height:190px; border-radius:12px; border:1px solid #2f3f58; background:#07101a; color:var(--text); padding:12px; font:16px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }}
  label {{ display:flex; gap:8px; align-items:center; color:var(--muted); }}
  .muted {{ color:var(--muted); }} .accent {{ color:var(--accent); }} .warnText {{ color:var(--warn); }} .bad {{ color:var(--bad); }}
  code {{ background:#07101a; border:1px solid #263243; border-radius:6px; padding:1px 5px; }}
</style>
</head>
<body>
<main>
  <h1>🎙️ Hermes Phone Voice Relay</h1>
  <div class=\"muted\">Phone mic → SSH tunnel → Hermes STT → draft text. Auto-send is <b>{send_label}</b>. tmux target: <code>{target_label}</code>.</div>

  <section class=\"card\">
    <div id=\"status\" class=\"accent\">Ready. Tap Start, speak, then Stop.</div>
    <div class=\"row\">
      <button id=\"start\">Start</button>
      <button id=\"stop\" class=\"danger\" disabled>Stop + transcribe</button>
      <button id=\"chunk\" class=\"secondary\">Record 12s chunk</button>
    </div>
    <div class=\"row\">
      <button id=\"auto\" class=\"warn\">Start auto chunks / 12s</button>
      <button id=\"autoStop\" class=\"secondary\" disabled>Stop auto</button>
    </div>
    <label><input id=\"autoDraft\" type=\"checkbox\" /> Draft each chunk to tmux pane</label>
    <label><input id=\"sendEnter\" type=\"checkbox\" {'disabled' if not config.allow_send else ''} /> Press Enter after tmux paste (requires server <code>--allow-send</code>)</label>
  </section>

  <section class=\"card\">
    <div class=\"muted\">Transcript buffer</div>
    <textarea id=\"out\" placeholder=\"Transcripts appear here. Review before sending.\"></textarea>
    <div class=\"row\">
      <button id=\"copy\" class=\"secondary\">Copy</button>
      <button id=\"draft\" class=\"secondary\">Draft to tmux</button>
      <button id=\"clear\" class=\"danger\">Clear</button>
    </div>
  </section>

  <section class=\"card muted\">
    Safe default: this page drafts text only. Use SSH local forwarding like
    <code>ssh -L 8788:127.0.0.1:8788 ...</code>, then open this page on your phone.
  </section>
</main>
<script>
const CFG = {cfg_json};
CFG.token = new URLSearchParams(window.location.search).get('token') || '';
const statusEl = document.getElementById('status');
const out = document.getElementById('out');
const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const chunkBtn = document.getElementById('chunk');
const autoBtn = document.getElementById('auto');
const autoStopBtn = document.getElementById('autoStop');
const autoDraft = document.getElementById('autoDraft');
const sendEnter = document.getElementById('sendEnter');
let stream = null;
let recorder = null;
let autoMode = false;

function setStatus(msg, cls='accent') {{ statusEl.className = cls; statusEl.textContent = msg; }}
function preferredMime() {{
  const options = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/webm'];
  for (const opt of options) {{ if (window.MediaRecorder && MediaRecorder.isTypeSupported(opt)) return opt; }}
  return '';
}}
async function ensureStream() {{
  if (!stream) stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
  return stream;
}}
async function postBlob(blob) {{
  if (!blob || blob.size <= 0) return null;
  if (blob.size > CFG.maxBytes) throw new Error(`audio chunk too large: ${{blob.size}} bytes`);
  setStatus(`Transcribing ${{Math.round(blob.size / 1024)}} KiB...`);
  const res = await fetch('/api/transcribe?token=' + encodeURIComponent(CFG.token), {{
    method: 'POST',
    headers: {{ 'Content-Type': blob.type || 'application/octet-stream', 'X-Voice-Relay-Token': CFG.token }},
    body: blob,
  }});
  const data = await res.json().catch(() => ({{ ok:false, error:'bad JSON response' }}));
  if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${{res.status}}`);
  const text = (data.transcript || '').trim();
  if (text) {{
    out.value = out.value ? out.value.replace(/\\s*$/, '\\n') + text : text;
    out.scrollTop = out.scrollHeight;
    setStatus('Transcript added.', 'accent');
    if (autoDraft.checked) await draftText(text);
  }} else {{
    setStatus('No speech detected.', 'warnText');
  }}
  return text;
}}
function makeRecorder(timesliceMs=0) {{
  const mimeType = preferredMime();
  const rec = new MediaRecorder(stream, mimeType ? {{ mimeType }} : undefined);
  const chunks = [];
  rec.ondataavailable = async (ev) => {{
    if (!ev.data || ev.data.size <= 0) return;
    if (autoMode) {{
      try {{ await postBlob(ev.data); }} catch (err) {{ setStatus(String(err.message || err), 'bad'); }}
    }} else {{
      chunks.push(ev.data);
    }}
  }};
  rec.onstop = async () => {{
    startBtn.disabled = false; stopBtn.disabled = true;
    if (!autoMode && chunks.length) {{
      try {{ await postBlob(new Blob(chunks, {{ type: chunks[0].type || mimeType || 'audio/webm' }})); }}
      catch (err) {{ setStatus(String(err.message || err), 'bad'); }}
    }}
  }};
  rec.start(timesliceMs || undefined);
  return rec;
}}
async function startManual() {{
  await ensureStream(); autoMode = false; recorder = makeRecorder();
  startBtn.disabled = true; stopBtn.disabled = false; setStatus('Recording... tap Stop when done.');
}}
function stopCurrent() {{ if (recorder && recorder.state !== 'inactive') recorder.stop(); }}
async function recordChunk(seconds=12) {{
  await ensureStream(); autoMode = false; recorder = makeRecorder();
  startBtn.disabled = true; stopBtn.disabled = false; setStatus(`Recording ${{seconds}}s chunk...`);
  setTimeout(stopCurrent, seconds * 1000);
}}
async function startAuto() {{
  await ensureStream(); autoMode = true; recorder = makeRecorder(12000);
  autoBtn.disabled = true; autoStopBtn.disabled = false; startBtn.disabled = true; stopBtn.disabled = true;
  setStatus('Auto chunks on: transcribing every ~12s.');
}}
function stopAuto() {{
  autoMode = false; stopCurrent(); autoBtn.disabled = false; autoStopBtn.disabled = true; startBtn.disabled = false;
  setStatus('Auto chunks stopped.');
}}
async function draftText(text) {{
  const clean = (text || '').trim(); if (!clean) return;
  const res = await fetch('/api/draft?token=' + encodeURIComponent(CFG.token), {{
    method: 'POST', headers: {{ 'Content-Type': 'application/json', 'X-Voice-Relay-Token': CFG.token }},
    body: JSON.stringify({{ text: clean, send: !!sendEnter.checked }}),
  }});
  const data = await res.json().catch(() => ({{ ok:false, error:'bad JSON response' }}));
  if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${{res.status}}`);
  setStatus(data.sent ? 'Pasted + Enter sent.' : 'Draft pasted to tmux.');
}}
startBtn.onclick = () => startManual().catch(e => setStatus(String(e.message || e), 'bad'));
stopBtn.onclick = stopCurrent;
chunkBtn.onclick = () => recordChunk(12).catch(e => setStatus(String(e.message || e), 'bad'));
autoBtn.onclick = () => startAuto().catch(e => setStatus(String(e.message || e), 'bad'));
autoStopBtn.onclick = stopAuto;
document.getElementById('copy').onclick = async () => {{ await navigator.clipboard.writeText(out.value); setStatus('Copied transcript buffer.'); }};
document.getElementById('draft').onclick = () => draftText(out.value).catch(e => setStatus(String(e.message || e), 'bad'));
document.getElementById('clear').onclick = () => {{ out.value = ''; setStatus('Cleared.'); }};
if (!navigator.mediaDevices || !window.MediaRecorder) setStatus('This browser lacks MediaRecorder microphone support.', 'bad');
</script>
</body>
</html>
"""


def make_handler(config: RelayConfig) -> type[BaseHTTPRequestHandler]:
    class PhoneVoiceRelayHandler(BaseHTTPRequestHandler):
        server_version = "HermesPhoneVoiceRelay/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:  # pragma: no cover - noise control
            message = fmt % args
            sys.stderr.write("[phone-voice] " + _redact_token_from_text(message, config.token) + "\n")

        def _require_auth(self) -> bool:
            if _authorized(self, config.token):
                return True
            _write_json(self, HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "missing or invalid token"})
            return False

        def do_GET(self) -> None:  # noqa: N802 - stdlib API
            path = urlparse(self.path).path
            if path == "/health":
                _write_json(self, HTTPStatus.OK, {"ok": True, "tmux_target": config.tmux_target, "allow_send": config.allow_send})
                return
            if path not in {"/", "/index.html"}:
                _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
                return
            if not self._require_auth():
                return
            body = render_index(config).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802 - stdlib API
            if not self._require_auth():
                return
            path = urlparse(self.path).path
            if path == "/api/transcribe":
                self._handle_transcribe()
                return
            if path == "/api/draft":
                self._handle_draft()
                return
            _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})

        def _handle_transcribe(self) -> None:
            raw_length = self.headers.get("Content-Length") or "0"
            try:
                length = int(raw_length)
            except ValueError:
                _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid Content-Length"})
                return
            if length <= 0:
                _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "empty audio body"})
                return
            if length > config.max_bytes:
                _write_json(self, HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"ok": False, "error": "audio chunk too large"})
                return

            ext = _extension_for_content_type(self.headers.get("Content-Type", ""))
            Path(config.temp_dir).mkdir(parents=True, exist_ok=True)
            audio_path = Path(config.temp_dir) / f"phone_voice_{uuid.uuid4().hex}{ext}"
            audio_path.write_bytes(self.rfile.read(length))
            try:
                result = config.transcriber(str(audio_path), config.model)
            except Exception as exc:  # pragma: no cover - provider-specific failures
                _write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"transcription failed: {exc}"})
                return
            finally:
                try:
                    audio_path.unlink(missing_ok=True)
                except Exception:
                    pass
            if not result.get("success"):
                _write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": result.get("error") or "transcription failed"})
                return
            transcript = (result.get("transcript") or "").strip()
            _write_json(self, HTTPStatus.OK, {"ok": True, "transcript": transcript, "provider": result.get("provider")})

        def _handle_draft(self) -> None:
            try:
                payload = _read_json_body(self)
            except ValueError as exc:
                _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
                return
            text = str(payload.get("text") or "")
            requested_send = bool(payload.get("send"))
            send = requested_send and config.allow_send
            if requested_send and not config.allow_send:
                _write_json(self, HTTPStatus.FORBIDDEN, {"ok": False, "error": "send disabled; restart relay with --allow-send"})
                return
            try:
                draft_to_tmux(text, target=config.tmux_target, send=send)
            except Exception as exc:
                _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
                return
            _write_json(self, HTTPStatus.OK, {"ok": True, "sent": send})

    return PhoneVoiceRelayHandler


def serve(config: RelayConfig) -> None:
    handler = make_handler(config)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    actual_host, actual_port = server.server_address[:2]
    url_host = "127.0.0.1" if actual_host in {"0.0.0.0", "::"} else actual_host
    url = f"http://{url_host}:{actual_port}/?token={config.token}"
    print("Hermes phone voice relay ready", file=sys.stderr)
    print(f"  URL:        {_redact_token_from_text(url, config.token)}", file=sys.stderr)
    print(f"  Bind:       {actual_host}:{actual_port}", file=sys.stderr)
    if not _is_loopback_host(str(actual_host)):
        print("  WARNING:    remote bind enabled; keep this relay behind an SSH tunnel or firewall", file=sys.stderr)
    print(f"  tmux:       {config.tmux_target or '<copy-only / no tmux paste>'}", file=sys.stderr)
    print(f"  auto-send:  {'enabled' if config.allow_send else 'disabled'}", file=sys.stderr)
    print("  SSH tunnel: ssh -L {0}:127.0.0.1:{0} <host>".format(actual_port), file=sys.stderr)
    print("Press Ctrl+C to stop.", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping phone voice relay.", file=sys.stderr)
    finally:
        server.shutdown()
        server.server_close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phone browser microphone relay for SSH Hermes/Pi sessions.")
    parser.add_argument("--host", default=os.getenv("HERMES_PHONE_VOICE_HOST", "127.0.0.1"), help="Bind host; default is localhost only.")
    parser.add_argument("--allow-remote", action="store_true", help="Permit non-loopback --host values. Use only behind an explicit firewall/tunnel.")
    parser.add_argument("--port", type=int, default=int(os.getenv("HERMES_PHONE_VOICE_PORT", "8788")), help="Bind port.")
    parser.add_argument("--token", default=os.getenv("HERMES_PHONE_VOICE_TOKEN"), help="API token; default is random per run.")
    parser.add_argument("--model", default=os.getenv("HERMES_PHONE_VOICE_STT_MODEL"), help="Optional STT model override.")
    parser.add_argument("--temp-dir", default=os.getenv("HERMES_PHONE_VOICE_TEMP_DIR"), help="Audio chunk temp directory.")
    parser.add_argument("--max-mb", type=float, default=float(os.getenv("HERMES_PHONE_VOICE_MAX_MB", "25")), help="Maximum audio chunk size in MiB.")
    parser.add_argument("--tmux-target", default=os.getenv("HERMES_PHONE_VOICE_TMUX_TARGET"), help="tmux target pane for draft paste, e.g. %%3 or session:win.pane.")
    parser.add_argument("--allow-send", action="store_true", help="Allow the web UI to press Enter after tmux paste. Off by default.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.allow_remote and not _is_loopback_host(args.host):
        print("Refusing non-loopback --host without --allow-remote.", file=sys.stderr)
        return 2
    config = RelayConfig(
        host=args.host,
        port=args.port,
        token=args.token or secrets.token_urlsafe(18),
        model=args.model,
        temp_dir=args.temp_dir or os.path.join(tempfile.gettempdir(), "hermes_phone_voice"),
        max_bytes=max(1, int(args.max_mb * 1024 * 1024)),
        tmux_target=args.tmux_target,
        allow_send=args.allow_send,
        allow_remote=args.allow_remote,
    )
    serve(config)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
