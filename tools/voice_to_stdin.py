#!/usr/bin/env python3
"""Record one voice utterance and print the transcript to stdout.

This is a small command-scoped wrapper around Hermes' existing voice mode
primitives.  Unlike ``/voice on`` inside the Hermes CLI, this module does not
own a chat UI, prompt-toolkit keybinding, or response loop.  It just captures
one utterance, transcribes it, and returns text that any CLI can consume:

    python tools/voice_to_stdin.py --once | pi -p
    pi -p "$(python tools/voice_to_stdin.py --once)"

The implementation intentionally reuses ``tools.voice_mode`` so Linux, macOS,
WSL-with-PulseAudio, and Termux microphone paths stay in one place.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
from typing import Any, Callable, Optional

from tools.voice_mode import (
    check_voice_requirements,
    create_audio_recorder,
    transcribe_recording,
)


class VoiceInputError(RuntimeError):
    """Raised when voice capture or transcription cannot produce text."""


def _write_status(message: str, *, quiet: bool) -> None:
    if not quiet:
        print(message, file=sys.stderr, flush=True)


def _wait_for_enter_or_timeout(done: threading.Event, max_seconds: float) -> None:
    """Wait for Enter in a daemon thread, bounded by ``max_seconds``."""

    def _reader() -> None:
        try:
            input()
            done.set()
        except EOFError:
            done.set()
        except Exception:
            # Best effort only; max_seconds still bounds the recording.
            pass

    threading.Thread(target=_reader, daemon=True).start()
    done.wait(max_seconds)


def _audio_level_stats(wav_path: str) -> dict[str, float]:
    """Return simple PCM level stats for a WAV file.

    The gate is intentionally conservative: if audio cannot be parsed as a
    normal PCM WAV, callers should skip gating rather than reject speech.
    """
    with wave.open(wav_path, "rb") as wav:
        channels = max(1, wav.getnchannels())
        sample_width = wav.getsampwidth()
        frame_count = wav.getnframes()
        raw = wav.readframes(frame_count)

    if sample_width != 2 or not raw:
        return {"rms": -1.0, "peak": -1.0, "samples": 0.0}

    sample_count = len(raw) // 2
    samples = struct.unpack("<" + "h" * sample_count, raw[: sample_count * 2])
    # Use the first channel for simple gating; pw-record path is mono.
    mono = samples[::channels]
    if not mono:
        return {"rms": 0.0, "peak": 0.0, "samples": 0.0}

    total = sum(float(v) * float(v) for v in mono)
    rms = (total / len(mono)) ** 0.5
    peak = float(max(abs(v) for v in mono))
    return {"rms": rms, "peak": peak, "samples": float(len(mono))}


def _passes_audio_gate(wav_path: str, *, min_rms: float, min_peak: float) -> tuple[bool, dict[str, float]]:
    if min_rms <= 0 and min_peak <= 0:
        return True, {"rms": -1.0, "peak": -1.0, "samples": 0.0}
    try:
        stats = _audio_level_stats(wav_path)
    except Exception:
        return True, {"rms": -1.0, "peak": -1.0, "samples": 0.0}
    if stats["samples"] <= 0:
        return False, stats
    if min_rms > 0 and stats["rms"] < min_rms:
        return False, stats
    if min_peak > 0 and stats["peak"] < min_peak:
        return False, stats
    return True, stats


def _record_with_pw_record(*, duration: float, quiet: bool, target: Optional[str] = None) -> str:
    """Capture a fixed-duration WAV via PipeWire's ``pw-record``.

    Args:
        duration: Fixed capture duration in seconds.
        quiet: Suppress user-facing stderr hints.
        target: Optional PipeWire/Pulse source node name or serial for ``--target``.
            When omitted, ``pw-record`` uses the current default source.
    """
    pw_record = shutil.which("pw-record")
    if not pw_record:
        raise VoiceInputError("pw-record backend requested but pw-record is not installed")
    if duration <= 0:
        raise VoiceInputError("pw-record backend requires duration > 0")

    os.makedirs(os.path.join(tempfile.gettempdir(), "hermes_voice"), exist_ok=True)
    wav_path = os.path.join(
        tempfile.gettempdir(),
        "hermes_voice",
        f"voice_to_stdin_{int(time.time() * 1000)}.wav",
    )
    sample_rate = 16000
    sample_count = max(1, int(sample_rate * duration))
    cmd = [pw_record]
    if target:
        cmd.extend(["--target", target])
    cmd.extend([
        "--rate",
        str(sample_rate),
        "--channels",
        "1",
        "--format",
        "s16",
        "--sample-count",
        str(sample_count),
        wav_path,
    ])
    _write_status(f"Recording for {duration:g}s with pw-record...", quiet=quiet)
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    has_audio_file = os.path.isfile(wav_path) and os.path.getsize(wav_path) > 0
    if result.returncode != 0 and not has_audio_file:
        detail = (result.stderr or result.stdout or "pw-record failed").strip()
        raise VoiceInputError(detail)
    if not has_audio_file:
        raise VoiceInputError("pw-record produced no audio")
    return wav_path


def record_and_transcribe_once(
    *,
    model: Optional[str] = None,
    max_seconds: float = 120.0,
    duration: Optional[float] = None,
    quiet: bool = False,
    backend: str = "auto",
    target: Optional[str] = None,
    recorder_factory: Callable[[], Any] = create_audio_recorder,
    transcriber: Callable[..., dict[str, Any]] = transcribe_recording,
    require_ready: bool = True,
    min_rms: float = 0.0,
    min_peak: float = 0.0,
) -> dict[str, Any]:
    """Capture one utterance and return the STT result dict.

    Args:
        model: Optional STT model override.
        max_seconds: Hard ceiling for recording.
        duration: If set, record exactly this many seconds instead of waiting
            for silence/Enter.
        quiet: Suppress user-facing stderr hints.
        target: Optional PipeWire/Pulse source target for the ``pw-record`` backend.
        recorder_factory: Dependency injection for tests.
        transcriber: Dependency injection for tests.
        require_ready: Run ``check_voice_requirements`` first.

    Returns:
        Dict containing at least ``success`` and ``transcript`` when successful.

    Raises:
        VoiceInputError: capture/transcription failed or produced empty text.
    """

    if max_seconds <= 0:
        raise VoiceInputError("max_seconds must be > 0")
    if duration is not None and duration <= 0:
        raise VoiceInputError("duration must be > 0")

    if backend not in {"auto", "hermes", "pw-record"}:
        raise VoiceInputError("backend must be one of: auto, hermes, pw-record")

    reqs: dict[str, Any] = {"available": False}
    if require_ready and backend != "pw-record":
        reqs = check_voice_requirements()
        if not reqs.get("available") and backend == "hermes":
            raise VoiceInputError(reqs.get("details") or "voice requirements not met")

    wav_path: Optional[str] = None
    if backend == "pw-record" or (backend == "auto" and require_ready and not reqs.get("available") and shutil.which("pw-record")):
        wav_path = _record_with_pw_record(duration=duration or min(max_seconds, 8.0), quiet=quiet, target=target)
    else:
        if require_ready and not reqs.get("available"):
            raise VoiceInputError(reqs.get("details") or "voice requirements not met")

        recorder = recorder_factory()
        done = threading.Event()

        try:
            supports_silence = bool(getattr(recorder, "supports_silence_autostop", True))
            recorder.start(on_silence_stop=done.set if supports_silence and duration is None else None)

            if duration is not None:
                _write_status(f"Recording for {duration:g}s...", quiet=quiet)
                time.sleep(duration)
            elif supports_silence:
                _write_status("Recording... speak now; auto-stops on silence.", quiet=quiet)
                done.wait(max_seconds)
            else:
                _write_status(
                    "Recording... press Enter to stop (or wait for timeout).",
                    quiet=quiet,
                )
                _wait_for_enter_or_timeout(done, max_seconds)

            wav_path = recorder.stop()
        finally:
            try:
                recorder.shutdown()
            except Exception:
                pass

        if not wav_path:
            raise VoiceInputError("no usable audio captured")

    gate_ok, audio_stats = _passes_audio_gate(wav_path, min_rms=min_rms, min_peak=min_peak)
    if not gate_ok:
        raise VoiceInputError(
            "audio below voice threshold "
            f"(rms={audio_stats['rms']:.1f}, peak={audio_stats['peak']:.0f})"
        )

    result = transcriber(wav_path, model=model)
    if not result.get("success"):
        raise VoiceInputError(result.get("error") or "transcription failed")

    transcript = (result.get("transcript") or "").strip()
    if not transcript:
        raise VoiceInputError("empty transcript")

    result = dict(result)
    result["transcript"] = transcript
    result["audio_path"] = wav_path
    if audio_stats.get("samples", 0.0) > 0:
        result["audio_gate"] = audio_stats
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record one utterance and print its transcript.")
    parser.add_argument("--once", action="store_true", help="Record one utterance (default behavior).")
    parser.add_argument("--model", help="STT model override (for example: base, whisper-1).")
    parser.add_argument("--max-seconds", type=float, default=120.0, help="Hard recording timeout.")
    parser.add_argument("--duration", type=float, help="Record a fixed number of seconds.")
    parser.add_argument("--backend", choices=["auto", "hermes", "pw-record"], default="auto", help="Audio backend (auto falls back to pw-record when PortAudio is unavailable).")
    parser.add_argument("--target", help="PipeWire/Pulse source node name or serial for pw-record --target.")
    parser.add_argument("--min-rms", type=float, default=float(os.getenv("VOICE_TO_STDIN_MIN_RMS", "80")), help="Reject audio below this RMS before transcription (0 disables).")
    parser.add_argument("--min-peak", type=float, default=float(os.getenv("VOICE_TO_STDIN_MIN_PEAK", "300")), help="Reject audio below this peak amplitude before transcription (0 disables).")
    parser.add_argument("--json", action="store_true", help="Print the full STT result as JSON.")
    parser.add_argument("--quiet", action="store_true", help="Suppress status text on stderr.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = record_and_transcribe_once(
            model=args.model,
            max_seconds=args.max_seconds,
            duration=args.duration,
            quiet=args.quiet,
            backend=args.backend,
            target=args.target,
            min_rms=args.min_rms,
            min_peak=args.min_peak,
        )
    except VoiceInputError as exc:
        print(f"voice-to-stdin: {exc}", file=sys.stderr)
        return 4
    except KeyboardInterrupt:
        print("voice-to-stdin: interrupted", file=sys.stderr)
        return 130

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["transcript"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
