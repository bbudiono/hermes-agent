"""OpenAI-client-compatible facade over the Google Antigravity CLI (`agy`).

Gemini is reached here only through `agy --print` on the user's Antigravity OAuth
login; no Google API key is read or passed. The rung is chat-only: tools are not
offered and no tool calls are parsed, so a turn that needs tools ends with text.
Any failure raises, so the agent loop retries and then fails over to the next
`fallback_providers` rung (repo_hermes_primary#39). Modelled on CopilotACPClient.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from types import SimpleNamespace
from typing import Any

from agent.copilot_acp_client import _completion_to_stream_chunks
from tools.environments.local import hermes_subprocess_env

AGY_MARKER_BASE_URL = "agy://local"
# Short on purpose: a hung agy must hand the turn to the next rung quickly (#39 review r1).
_DEFAULT_TIMEOUT_SECONDS = 180.0
_GOOGLE_KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY")


def _flatten(messages: list[dict[str, Any]]) -> str:
    """One prompt from an OpenAI message list: system text first, then the turns."""
    parts: list[str] = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):  # multimodal parts: keep the text ones
            content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
        if not content:
            continue
        role = msg.get("role", "user")
        parts.append(content if role == "system" else f"{role.capitalize()}: {content}")
    return "\n\n".join(parts)


def _seconds(timeout: Any) -> float:
    """run_agent may pass an httpx.Timeout; take its largest component."""
    if timeout is None:
        return _DEFAULT_TIMEOUT_SECONDS
    if isinstance(timeout, (int, float)):
        return float(timeout)
    values = [getattr(timeout, a, None) for a in ("read", "write", "connect", "pool", "timeout")]
    numeric = [float(v) for v in values if isinstance(v, (int, float))]
    return max(numeric) if numeric else _DEFAULT_TIMEOUT_SECONDS


class _Completions:
    def __init__(self, client: "AgyCLIClient"):
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        return self._client._create(**kwargs)


class AgyCLIClient:
    """Minimal `client.chat.completions.create(...)` over `agy --print`."""

    def __init__(self, *, command: str | None = None, api_key: str | None = None,
                 base_url: str | None = None, **_: Any):
        self._command = command or shutil.which("agy") or "agy"
        self.api_key = api_key or "agy"
        self.base_url = base_url or AGY_MARKER_BASE_URL
        self.chat = SimpleNamespace(completions=_Completions(self))
        self.is_closed = False

    def close(self) -> None:
        self.is_closed = True

    def _create(self, *, model: str | None = None, messages: list[dict[str, Any]] | None = None,
                timeout: Any = None, stream: bool = False, **_: Any) -> Any:
        seconds = _seconds(timeout)
        # --print=<prompt> keeps any prompt text from being read as a flag; --sandbox plus an
        # empty working directory keep injected text from reading local files (#39 review r1).
        argv = [self._command, f"--print={_flatten(messages or [])}", "--output-format", "text",
                "--disable-slash-commands", "--mode", "plan", "--sandbox",
                f"--print-timeout={int(seconds)}s"]
        if model:
            argv += ["--model", model]
        env = hermes_subprocess_env(inherit_credentials=False)
        for key in _GOOGLE_KEY_VARS:  # OAuth login only (provider-CLI mandate)
            env.pop(key, None)
        try:
            with tempfile.TemporaryDirectory(prefix="hermes-agy-") as workdir:
                proc = subprocess.run(argv, capture_output=True, text=True, timeout=seconds + 15,
                                      env=env, stdin=subprocess.DEVNULL, cwd=workdir)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"agy timed out after {seconds:.0f}s") from exc
        except FileNotFoundError as exc:
            raise RuntimeError(f"agy CLI not found at '{self._command}'") from exc
        text = (proc.stdout or "").strip()
        if proc.returncode != 0:
            raise RuntimeError(f"agy exited {proc.returncode}: {(proc.stderr or '').strip()[-300:]}")
        if not text:
            raise RuntimeError("agy returned an empty response")

        message = SimpleNamespace(content=text, tool_calls=None, reasoning=None,
                                  reasoning_content=None, reasoning_details=None)
        usage = SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=0))
        completion = SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")],
                                     usage=usage, model=model or "agy")
        return _completion_to_stream_chunks(completion) if stream else completion
