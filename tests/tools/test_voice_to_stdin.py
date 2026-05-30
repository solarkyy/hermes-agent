"""Tests for command-scoped voice-to-stdin / voice-to-pi wrappers."""

from __future__ import annotations

import struct
import subprocess
import wave
from pathlib import Path

import pytest


class FakeRecorder:
    supports_silence_autostop = True

    def __init__(self, wav_path="/tmp/fake.wav"):
        self.wav_path = wav_path
        self.started = False
        self.stopped = False
        self.shutdown_called = False

    def start(self, on_silence_stop=None):
        self.started = True
        if on_silence_stop:
            on_silence_stop()

    def stop(self):
        self.stopped = True
        return self.wav_path

    def shutdown(self):
        self.shutdown_called = True


class FakeManualRecorder(FakeRecorder):
    supports_silence_autostop = False


class TestPwRecordBackend:
    def test_pw_record_backend_writes_wav_and_returns_path(self, monkeypatch, tmp_path):
        from tools.voice_to_stdin import _record_with_pw_record

        seen = {}

        def fake_run(cmd, **kwargs):
            seen["cmd"] = cmd
            wav_path = Path(cmd[-1])
            wav_path.write_bytes(b"wav-bytes")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr("tools.voice_to_stdin.shutil.which", lambda name: "/usr/bin/pw-record" if name == "pw-record" else None)
        monkeypatch.setattr("tools.voice_to_stdin.tempfile.gettempdir", lambda: str(tmp_path))
        monkeypatch.setattr("tools.voice_to_stdin.subprocess.run", fake_run)

        wav_path = _record_with_pw_record(duration=1.25, quiet=True)

        assert Path(wav_path).read_bytes() == b"wav-bytes"
        assert seen["cmd"][:8] == [
            "/usr/bin/pw-record",
            "--rate",
            "16000",
            "--channels",
            "1",
            "--format",
            "s16",
            "--sample-count",
        ]
        assert seen["cmd"][8] == str(int(16000 * 1.25))


def _write_wav(path: Path, samples: list[int]) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * len(samples), *samples))


class TestRecordAndTranscribeOnce:
    def test_records_transcribes_and_trims_text(self):
        from tools.voice_to_stdin import record_and_transcribe_once

        recorder = FakeRecorder()

        result = record_and_transcribe_once(
            recorder_factory=lambda: recorder,
            transcriber=lambda path, model=None: {
                "success": True,
                "transcript": "  hello pi  ",
                "path": path,
                "model": model,
            },
            model="base",
            require_ready=False,
            quiet=True,
        )

        assert recorder.started is True
        assert recorder.stopped is True
        assert recorder.shutdown_called is True
        assert result["transcript"] == "hello pi"
        assert result["path"] == "/tmp/fake.wav"
        assert result["model"] == "base"
        assert result["audio_path"] == "/tmp/fake.wav"

    def test_duration_supports_recorders_without_silence_autostop(self):
        from tools.voice_to_stdin import record_and_transcribe_once

        recorder = FakeManualRecorder()
        result = record_and_transcribe_once(
            recorder_factory=lambda: recorder,
            transcriber=lambda path, model=None: {"success": True, "transcript": "manual stop"},
            duration=0.001,
            require_ready=False,
            quiet=True,
        )

        assert result["transcript"] == "manual stop"
        assert recorder.stopped is True

    def test_empty_audio_raises(self):
        from tools.voice_to_stdin import VoiceInputError, record_and_transcribe_once

        recorder = FakeRecorder(wav_path=None)
        with pytest.raises(VoiceInputError, match="no usable audio"):
            record_and_transcribe_once(
                recorder_factory=lambda: recorder,
                transcriber=lambda path, model=None: {"success": True, "transcript": "ignored"},
                require_ready=False,
                quiet=True,
            )

    def test_empty_transcript_raises(self):
        from tools.voice_to_stdin import VoiceInputError, record_and_transcribe_once

        with pytest.raises(VoiceInputError, match="empty transcript"):
            record_and_transcribe_once(
                recorder_factory=FakeRecorder,
                transcriber=lambda path, model=None: {"success": True, "transcript": "   "},
                require_ready=False,
                quiet=True,
            )

    def test_failed_transcription_raises_error(self):
        from tools.voice_to_stdin import VoiceInputError, record_and_transcribe_once

        with pytest.raises(VoiceInputError, match="stt down"):
            record_and_transcribe_once(
                recorder_factory=FakeRecorder,
                transcriber=lambda path, model=None: {"success": False, "error": "stt down"},
                require_ready=False,
                quiet=True,
            )

    def test_invalid_backend_raises(self):
        from tools.voice_to_stdin import VoiceInputError, record_and_transcribe_once

        with pytest.raises(VoiceInputError, match="backend must be"):
            record_and_transcribe_once(backend="bad", require_ready=False, quiet=True)

    def test_audio_gate_rejects_low_level_audio_before_transcription(self, tmp_path):
        from tools.voice_to_stdin import VoiceInputError, record_and_transcribe_once

        wav_path = tmp_path / "quiet.wav"
        _write_wav(wav_path, [5, -5] * 100)

        called = False

        def transcriber(path, model=None):
            nonlocal called
            called = True
            return {"success": True, "transcript": "1.8g 1.8g"}

        with pytest.raises(VoiceInputError, match="audio below voice threshold"):
            record_and_transcribe_once(
                recorder_factory=lambda: FakeRecorder(str(wav_path)),
                transcriber=transcriber,
                require_ready=False,
                quiet=True,
                min_rms=80,
                min_peak=300,
            )
        assert called is False

    def test_audio_gate_allows_speech_level_audio(self, tmp_path):
        from tools.voice_to_stdin import record_and_transcribe_once

        wav_path = tmp_path / "speech.wav"
        _write_wav(wav_path, [0, 1200, -1200, 600, -600] * 100)

        result = record_and_transcribe_once(
            recorder_factory=lambda: FakeRecorder(str(wav_path)),
            transcriber=lambda path, model=None: {"success": True, "transcript": "real speech"},
            require_ready=False,
            quiet=True,
            min_rms=80,
            min_peak=300,
        )

        assert result["transcript"] == "real speech"
        assert result["audio_gate"]["rms"] >= 80
        assert result["audio_gate"]["peak"] >= 300


class TestVoiceToStdinCLI:
    def test_main_prints_plain_transcript(self, monkeypatch, capsys):
        import tools.voice_to_stdin as mod

        monkeypatch.setattr(
            mod,
            "record_and_transcribe_once",
            lambda **kwargs: {"success": True, "transcript": "hello from voice"},
        )

        assert mod.main(["--once", "--quiet"]) == 0
        out = capsys.readouterr().out
        assert out == "hello from voice\n"

    def test_main_prints_json(self, monkeypatch, capsys):
        import tools.voice_to_stdin as mod

        monkeypatch.setattr(
            mod,
            "record_and_transcribe_once",
            lambda **kwargs: {"success": True, "transcript": "json voice", "provider": "local"},
        )

        assert mod.main(["--json", "--quiet"]) == 0
        out = capsys.readouterr().out
        assert '"transcript": "json voice"' in out
        assert '"provider": "local"' in out


class TestVoiceToPi:
    def test_run_pi_with_text_builds_safe_arg_vector(self, monkeypatch):
        from tools.voice_to_pi import run_pi_with_text

        seen = {}

        def fake_run(cmd, **kwargs):
            seen["cmd"] = cmd
            seen["kwargs"] = kwargs
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        monkeypatch.setattr("tools.voice_to_pi.subprocess.run", fake_run)
        result = run_pi_with_text(
            "say hi; $(not shell)",
            pi_bin="/bin/pi",
            continue_session=True,
            no_tools=True,
            no_context_files=True,
            no_skills=True,
            extra_args=["--model", "test/model"],
            timeout=9,
        )

        assert result.stdout == "ok"
        assert seen["cmd"] == [
            "/bin/pi",
            "-p",
            "--continue",
            "--no-tools",
            "--no-context-files",
            "--no-skills",
            "--model",
            "test/model",
            "say hi; $(not shell)",
        ]
        assert seen["kwargs"]["text"] is True
        assert seen["kwargs"]["capture_output"] is True
        assert seen["kwargs"]["check"] is False
        assert seen["kwargs"]["timeout"] == 9

    def test_voice_to_pi_timeout_fails_closed(self, monkeypatch, capsys):
        import tools.voice_to_pi as mod

        def fake_run_pi_with_text(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["pi"], timeout=1)

        monkeypatch.setattr(mod, "run_pi_with_text", fake_run_pi_with_text)

        assert mod.main(["--text", "hello", "--timeout", "1", "--json"]) == 124
        out = capsys.readouterr().out
        assert '"ok": false' in out
        assert '"returncode": 124' in out
        assert "Pi timed out after 1s" in out

    def test_voice_to_pi_dry_run_uses_text_without_recording(self, capsys):
        import tools.voice_to_pi as mod

        assert mod.main(["--text", " ask pi ", "--dry-run"]) == 0
        assert capsys.readouterr().out == "ask pi\n"

    def test_voice_to_pi_json_dry_run(self, capsys):
        import tools.voice_to_pi as mod

        assert mod.main(["--text", "hello", "--dry-run", "--json"]) == 0
        out = capsys.readouterr().out
        assert '"ok": true' in out
        assert '"transcript": "hello"' in out

    def test_voice_to_pi_empty_text_fails(self, capsys):
        import tools.voice_to_pi as mod

        assert mod.main(["--text", "   "]) == 4
        assert "empty transcript" in capsys.readouterr().err
