"""OpenAI-compatible shim for Google's Antigravity CLI (``agy``).

The Antigravity CLI owns its Google OAuth/subscription state under
``~/.gemini/antigravity-cli``.  Hermes should not copy those tokens or ask for
an AI Studio API key when the user selects the ``agy`` provider; it should exec
``agy --model <model> --print <prompt>`` and let Antigravity use the logged-in
account.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from agent.redact import redact_sensitive_text

AGY_MARKER_BASE_URL = "agy://antigravity"
_DEFAULT_TIMEOUT_SECONDS = 900.0

# ``agy`` currently accepts unknown ``--model`` values by silently falling back
# to its default model. Hermes must not hide that from Kyle, so validate model
# names before launch. Keep both the stable slugs Hermes stores and the display
# names returned by ``agy models``.
_STATIC_AGY_MODELS = {
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "claude-sonnet-4.6",
    "claude-opus-4.6",
    "gpt-oss-120b",
    "Gemini 3.5 Flash (Low)",
    "Gemini 3.5 Flash (Medium)",
    "Gemini 3.5 Flash (High)",
    "Gemini 3.1 Pro (Low)",
    "Gemini 3.1 Pro (High)",
    "Claude Sonnet 4.6 (Thinking)",
    "Claude Opus 4.6 (Thinking)",
    "GPT-OSS 120B (Medium)",
}


def _resolve_command() -> str:
    return (
        os.getenv("HERMES_AGY_COMMAND", "").strip()
        or os.getenv("AGY_CLI_PATH", "").strip()
        or "agy"
    )


def _resolve_args() -> list[str]:
    raw = os.getenv("HERMES_AGY_ARGS", "").strip()
    return shlex.split(raw) if raw else []


def _resolve_home_dir() -> str:
    """Return the HOME that should be visible to ``agy``.

    In profile/docker modes Hermes may run with an overridden home.  Use the
    same helper as other subprocess-backed providers when available, otherwise
    fall back to the current process HOME so Antigravity can find its own
    ``~/.gemini/antigravity-cli`` OAuth state.
    """

    try:
        from hermes_constants import get_subprocess_home

        profile_home = get_subprocess_home()
        if profile_home:
            return profile_home
    except Exception:
        pass

    home = os.environ.get("HOME", "").strip()
    if home:
        return home

    expanded = os.path.expanduser("~")
    if expanded and expanded != "~":
        return expanded

    return "/tmp"


def _build_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = _resolve_home_dir()
    return env


@lru_cache(maxsize=8)
def _live_agy_models(command_path: str, home: str) -> frozenset[str]:
    """Return model display names from ``agy models`` if available."""

    env = _build_subprocess_env()
    if home:
        env["HOME"] = home
    try:
        completed = subprocess.run(
            [command_path, "models"],
            text=True,
            capture_output=True,
            timeout=15,
            env=env,
            check=False,
        )
    except Exception:
        return frozenset()
    if completed.returncode != 0:
        return frozenset()
    return frozenset(line.strip() for line in (completed.stdout or "").splitlines() if line.strip())


def _validate_model_or_raise(command_path: str, model: str | None) -> None:
    requested = (model or "").strip()
    if not requested:
        return
    static_lower = {item.lower() for item in _STATIC_AGY_MODELS}
    if requested.lower() in static_lower:
        return
    live = _live_agy_models(command_path, _resolve_home_dir())
    if requested.lower() in {item.lower() for item in live}:
        return
    examples = ", ".join(sorted(_STATIC_AGY_MODELS)[:6])
    raise RuntimeError(
        "Antigravity CLI model validation failed before launch: "
        f"{requested!r} is not in `agy models` / Hermes' known agy catalog. "
        "This prevents agy from silently falling back to its default model. "
        f"Use `agy models` to choose an exact model. Known examples: {examples}"
    )


def _render_message_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return str(content.get("text") or "").strip()
        if isinstance(content.get("content"), str):
            return str(content.get("content") or "").strip()
        return json.dumps(content, ensure_ascii=True)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
        return "\n".join(part.strip() for part in parts if part and part.strip()).strip()
    return str(content).strip()


def _format_messages_as_prompt(
    messages: list[dict[str, Any]],
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: Any = None,
) -> str:
    sections: list[str] = [
        "You are being used as the active Antigravity (agy) backend for Hermes.",
        "Answer the latest user request using the conversation transcript below.",
    ]
    if model:
        sections.append(f"Hermes requested model: {model}")

    if isinstance(tools, list) and tools:
        tool_specs: list[dict[str, Any]] = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            fn = tool.get("function") or {}
            if not isinstance(fn, dict):
                continue
            name = fn.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            tool_specs.append(
                {
                    "name": name.strip(),
                    "description": fn.get("description", ""),
                    "parameters": fn.get("parameters", {}),
                }
            )
        if tool_specs:
            sections.append(
                "Hermes tools are available as OpenAI-style function schemas. "
                "If you need a Hermes tool, emit ONLY a tool call block in this exact form: "
                "<tool_call>{\"id\":\"call_1\",\"type\":\"function\","
                "\"function\":{\"name\":\"tool_name\",\"arguments\":\"{}\"}}</tool_call>. "
                "The function.arguments value must be a JSON string.\n"
                + json.dumps(tool_specs, ensure_ascii=False)
            )
    if tool_choice is not None:
        sections.append(f"Tool choice hint: {json.dumps(tool_choice, ensure_ascii=False)}")

    transcript: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "context").strip().lower()
        label = {
            "system": "System",
            "user": "User",
            "assistant": "Assistant",
            "tool": "Tool",
            "function": "Tool",
        }.get(role, "Context")
        rendered = _render_message_content(message.get("content"))
        if rendered:
            transcript.append(f"{label}:\n{rendered}")

    if transcript:
        sections.append("Conversation transcript:\n\n" + "\n\n".join(transcript))
    sections.append("Continue from the latest user request.")
    return "\n\n".join(section.strip() for section in sections if section and section.strip())


def _extract_tool_calls_from_text(text: str) -> tuple[list[SimpleNamespace], str]:
    """Parse optional ``<tool_call>{...}</tool_call>`` blocks from agy text."""

    # Reuse the well-tested parser from the ACP subprocess shim.  Import lazily
    # to keep this module independent at import time and to avoid duplicating
    # the JSON repair heuristics.
    from agent.copilot_acp_client import _extract_tool_calls_from_text as _extract

    return _extract(text)


def _usage() -> SimpleNamespace:
    return SimpleNamespace(
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        prompt_tokens_details=SimpleNamespace(cached_tokens=0),
    )


def _coerce_timeout_seconds(timeout: Any) -> float:
    if timeout is None:
        return _DEFAULT_TIMEOUT_SECONDS
    if isinstance(timeout, (int, float)):
        return float(timeout)
    candidates = [getattr(timeout, attr, None) for attr in ("read", "write", "connect", "pool", "timeout")]
    numeric = [float(value) for value in candidates if isinstance(value, (int, float))]
    return max(numeric) if numeric else _DEFAULT_TIMEOUT_SECONDS


class _AgyChatCompletions:
    def __init__(self, client: "AgyCliClient") -> None:
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        return self._client._create_chat_completion(**kwargs)


class _AgyChatNamespace:
    def __init__(self, client: "AgyCliClient") -> None:
        self.completions = _AgyChatCompletions(client)


class AgyCliClient:
    """Minimal OpenAI-client-compatible facade over ``agy --print``."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        agy_command: str | None = None,
        agy_args: list[str] | None = None,
        agy_cwd: str | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        **_: Any,
    ) -> None:
        self.api_key = api_key or "agy-external"
        self.base_url = base_url or AGY_MARKER_BASE_URL
        self._default_headers = dict(default_headers or {})
        self._agy_command = agy_command or command or _resolve_command()
        self._agy_args = list(agy_args or args or _resolve_args())
        self._agy_cwd = str(Path(agy_cwd or os.getcwd()).resolve())
        self.chat = _AgyChatNamespace(self)
        self.is_closed = False

    def close(self) -> None:
        self.is_closed = True

    def _create_chat_completion(
        self,
        *,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        stream: bool = False,
        timeout: Any = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: Any = None,
        **_: Any,
    ) -> Any:
        prompt_text = _format_messages_as_prompt(
            messages or [],
            model=model,
            tools=tools,
            tool_choice=tool_choice,
        )
        timeout_seconds = _coerce_timeout_seconds(timeout)
        response_text = self._run_prompt(
            prompt_text,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        tool_calls, cleaned_text = _extract_tool_calls_from_text(response_text)
        finish_reason = "tool_calls" if tool_calls else "stop"

        if stream:
            return self._stream_response(
                content=cleaned_text,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                model=model,
            )

        assistant_message = SimpleNamespace(
            role="assistant",
            content=cleaned_text or None,
            tool_calls=tool_calls or None,
            reasoning=None,
            reasoning_content=None,
            reasoning_details=None,
        )
        choice = SimpleNamespace(index=0, message=assistant_message, finish_reason=finish_reason)
        return SimpleNamespace(
            id="agy-" + uuid.uuid4().hex,
            object="chat.completion",
            created=int(time.time()),
            model=model or "agy",
            choices=[choice],
            usage=_usage(),
        )

    def _run_prompt(self, prompt_text: str, *, model: str | None, timeout_seconds: float) -> str:
        command_path = shutil.which(self._agy_command) or self._agy_command
        _validate_model_or_raise(command_path, model)
        cmd = [command_path] + self._agy_args
        if model:
            cmd += ["--model", model]
        # Keep print timeout below subprocess timeout so agy can exit cleanly and
        # report its own timeout error first. Go duration syntax accepts "900s".
        if timeout_seconds > 1:
            cmd += ["--print-timeout", f"{max(1, int(timeout_seconds - 1))}s"]
        cmd += ["--print", prompt_text]

        try:
            completed = subprocess.run(
                cmd,
                cwd=self._agy_cwd,
                env=_build_subprocess_env(),
                text=True,
                capture_output=True,
                timeout=max(1.0, timeout_seconds),
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Could not start Antigravity CLI command '{self._agy_command}'. "
                "Install agy or set HERMES_AGY_COMMAND/AGY_CLI_PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Antigravity CLI timed out after {int(timeout_seconds)}s while running agy --print."
            ) from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if completed.returncode != 0:
            tail = "\n".join((stderr or stdout).splitlines()[-20:]).strip()
            tail = redact_sensitive_text(tail) if tail else "no output"
            raise RuntimeError(
                f"Antigravity CLI failed with exit code {completed.returncode}: {tail}"
            )
        return stdout.strip()

    def _stream_response(
        self,
        *,
        content: str,
        tool_calls: list[SimpleNamespace],
        finish_reason: str,
        model: str | None,
    ) -> Iterator[Any]:
        def _chunks() -> Iterator[Any]:
            if content:
                yield SimpleNamespace(
                    id="agy-stream-" + uuid.uuid4().hex,
                    object="chat.completion.chunk",
                    created=int(time.time()),
                    model=model or "agy",
                    choices=[
                        SimpleNamespace(
                            index=0,
                            delta=SimpleNamespace(
                                role="assistant",
                                content=content,
                                tool_calls=None,
                                reasoning=None,
                                reasoning_content=None,
                            ),
                            finish_reason=None,
                        )
                    ],
                    usage=None,
                )
            for index, tool_call in enumerate(tool_calls or []):
                fn = getattr(tool_call, "function", SimpleNamespace(name="", arguments="{}"))
                yield SimpleNamespace(
                    id="agy-stream-" + uuid.uuid4().hex,
                    object="chat.completion.chunk",
                    created=int(time.time()),
                    model=model or "agy",
                    choices=[
                        SimpleNamespace(
                            index=0,
                            delta=SimpleNamespace(
                                role="assistant",
                                content=None,
                                tool_calls=[
                                    SimpleNamespace(
                                        index=index,
                                        id=getattr(tool_call, "id", "") or f"agy_call_{index + 1}",
                                        type="function",
                                        function=SimpleNamespace(
                                            name=getattr(fn, "name", "") or "tool",
                                            arguments=getattr(fn, "arguments", "{}") or "{}",
                                        ),
                                    )
                                ],
                                reasoning=None,
                                reasoning_content=None,
                            ),
                            finish_reason=None,
                        )
                    ],
                    usage=None,
                )
            yield SimpleNamespace(
                id="agy-stream-" + uuid.uuid4().hex,
                object="chat.completion.chunk",
                created=int(time.time()),
                model=model or "agy",
                choices=[
                    SimpleNamespace(
                        index=0,
                        delta=SimpleNamespace(
                            role="assistant",
                            content=None,
                            tool_calls=None,
                            reasoning=None,
                            reasoning_content=None,
                        ),
                        finish_reason=finish_reason,
                    )
                ],
                usage=_usage(),
            )

        return _chunks()
