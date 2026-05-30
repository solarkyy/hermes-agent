#!/usr/bin/env python3
"""Send one voice utterance to the Pi CLI.

This is deliberately tiny: it reuses ``tools.voice_to_stdin`` for capture/STT
and passes the resulting transcript to ``pi -p`` as normal text.  Pi does not
need native microphone support for this path.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Optional

from tools.voice_to_stdin import VoiceInputError, record_and_transcribe_once


def run_pi_with_text(
    transcript: str,
    *,
    pi_bin: str = "pi",
    continue_session: bool = False,
    no_tools: bool = False,
    no_context_files: bool = False,
    no_skills: bool = False,
    extra_args: Optional[list[str]] = None,
    timeout: Optional[float] = None,
) -> subprocess.CompletedProcess[str]:
    """Run Pi non-interactively with ``transcript`` as the user prompt."""
    cmd = [pi_bin, "-p"]
    if continue_session:
        cmd.append("--continue")
    if no_tools:
        cmd.append("--no-tools")
    if no_context_files:
        cmd.append("--no-context-files")
    if no_skills:
        cmd.append("--no-skills")
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(transcript)
    return subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=timeout)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture one voice utterance and send it to Pi.")
    parser.add_argument("--text", help="Bypass recording; send this text to Pi (useful for tests).")
    parser.add_argument("--model", help="STT model override for recording.")
    parser.add_argument("--max-seconds", type=float, default=120.0, help="Hard recording timeout.")
    parser.add_argument("--duration", type=float, help="Record a fixed number of seconds.")
    parser.add_argument("--backend", choices=["auto", "hermes", "pw-record"], default="auto", help="Audio backend for recording.")
    parser.add_argument("--pi-bin", default="pi", help="Pi executable path/name.")
    parser.add_argument("--continue", dest="continue_session", action="store_true", help="Pass --continue to Pi.")
    parser.add_argument("--no-tools", action="store_true", help="Pass --no-tools to Pi.")
    parser.add_argument("--no-context-files", action="store_true", help="Pass --no-context-files to Pi.")
    parser.add_argument("--no-skills", action="store_true", help="Pass --no-skills to Pi.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Seconds to wait for Pi before failing closed.")
    parser.add_argument("--json", action="store_true", help="Print JSON with transcript/stdout/stderr/returncode.")
    parser.add_argument("--dry-run", action="store_true", help="Print transcript without invoking Pi.")
    parser.add_argument("--quiet", action="store_true", help="Suppress recording status text.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args, extra = parser.parse_known_args(argv)

    try:
        if args.text is not None:
            transcript = args.text.strip()
            if not transcript:
                raise VoiceInputError("empty transcript")
            stt_result = {"success": True, "transcript": transcript, "source": "--text"}
        else:
            stt_result = record_and_transcribe_once(
                model=args.model,
                max_seconds=args.max_seconds,
                duration=args.duration,
                quiet=args.quiet,
                backend=args.backend,
            )
            transcript = stt_result["transcript"]
    except VoiceInputError as exc:
        print(f"voice-to-pi: {exc}", file=sys.stderr)
        return 4
    except KeyboardInterrupt:
        print("voice-to-pi: interrupted", file=sys.stderr)
        return 130

    if args.dry_run:
        if args.json:
            print(json.dumps({"ok": True, "transcript": transcript, "dry_run": True}, ensure_ascii=False))
        else:
            print(transcript)
        return 0

    try:
        result = run_pi_with_text(
            transcript,
            pi_bin=args.pi_bin,
            continue_session=args.continue_session,
            no_tools=args.no_tools,
            no_context_files=args.no_context_files,
            no_skills=args.no_skills,
            extra_args=extra,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired as exc:
        timeout_payload = {
            "ok": False,
            "transcript": transcript,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"Pi timed out after {args.timeout:g}s",
            "stt": stt_result,
        }
        if args.json:
            print(json.dumps(timeout_payload, ensure_ascii=False))
        else:
            print(timeout_payload["stderr"], file=sys.stderr)
        return 124

    if args.json:
        print(json.dumps({
            "ok": result.returncode == 0,
            "transcript": transcript,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "stt": stt_result,
        }, ensure_ascii=False))
    else:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
