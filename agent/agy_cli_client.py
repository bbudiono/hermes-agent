"""OpenAI-client-compatible facade over the Google Antigravity CLI (`agy`).

Gemini is reached here only through `agy` on the user's Antigravity OAuth login;
no Google API key is read or passed. The rung is chat-only: tools are not offered
and no tool calls are parsed, so a turn that needs tools ends with text. Any
failure raises, so the agent loop retries and then fails over to the next
`fallback_providers` rung (repo_hermes_primary#39). Modelled on CopilotACPClient.

The conversation goes in on stdin as one stream-json `user` event, never on the
command line: a single argv element over 128 KiB fails with E2BIG on Linux, and
anything on the command line is visible in `ps` (review r2).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
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
_GRACE_SECONDS = 15  # past agy's own --print-timeout before the process group is killed


def _run(argv: list[str], *, input: str, timeout: float, env: dict, cwd: str) -> SimpleNamespace:
    """subprocess.run, but a timeout kills agy's whole process group and returns at once.

    subprocess.run kills only agy and then waits on the pipes again, so a child that
    inherited them (a plan-mode shell) would hang the turn instead of failing over (#40).
    """
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            encoding="utf-8", errors="replace", env=env, cwd=cwd, start_new_session=True)
    try:
        out, err = proc.communicate(input, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:  # agy already exited
            pass
        raise
    return SimpleNamespace(returncode=proc.returncode, stdout=out, stderr=err)


def _text(content: Any) -> str:
    if isinstance(content, list):  # multimodal parts: keep text, name what was dropped
        parts = [p.get("text", "") if p.get("type", "text") == "text" else "[non-text attachment omitted]"
                 for p in content if isinstance(p, dict)]
        return "\n".join(p for p in parts if p)
    return content or ""


def _flatten(messages: list[dict[str, Any]]) -> str:
    """One prompt from an OpenAI message list: system text first, then the turns."""
    parts: list[str] = []
    for msg in messages:
        content = _text(msg.get("content"))
        calls = [c.get("function", {}).get("name", "?") for c in msg.get("tool_calls") or []]
        if calls:  # keep the call so a following tool result is not orphaned
            content = (content + "\n" if content else "") + f"[called tools: {', '.join(calls)}]"
        if not content:
            continue
        role = msg.get("role", "user")
        parts.append(content if role == "system" else f"{role.capitalize()}: {content}")
    return "\n\n".join(parts)


def _usable(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _seconds(timeout: Any) -> float:
    """run_agent may pass an httpx.Timeout; take its largest component.

    A missing, zero, negative or boolean value means the default: subprocess.run
    raises ValueError on a negative timeout instead of a failover RuntimeError.
    """
    if _usable(timeout):
        return float(timeout)
    values = [getattr(timeout, a, None) for a in ("read", "write", "connect", "pool", "timeout")]
    numeric = [float(v) for v in values if _usable(v)]
    return max(numeric) if numeric else _DEFAULT_TIMEOUT_SECONDS


def _response(stdout: str) -> str:
    """The answer from agy's stream-json `result` event; raises on an error or no result."""
    for line in reversed((stdout or "").splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("event") == "result":
            result = event.get("result") or {}
            if result.get("status") != "SUCCESS":
                raise RuntimeError(f"agy reported {result.get('status')}: {str(result.get('error', ''))[:300]}")
            response = result.get("response") or ""
            if not isinstance(response, str):  # keep every failure a RuntimeError (#39 review)
                raise RuntimeError(f"agy returned a non-text response: {type(response).__name__}")
            return response.strip()
    raise RuntimeError("agy returned no result event")


class _Completions:
    def __init__(self, client: "AgyCLIClient"):
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        return self._client._create(**kwargs)


class AgyCLIClient:
    """Minimal `client.chat.completions.create(...)` over the agy CLI."""

    def __init__(self, *, command: str | None = None, api_key: str | None = None,
                 base_url: str | None = None, timeout: Any = None, **_: Any):
        self._command = command or shutil.which("agy") or "agy"
        self._timeout = timeout  # the agent's configured request timeout, from client_kwargs
        self.api_key = api_key or "agy"
        self.base_url = base_url or AGY_MARKER_BASE_URL
        self.chat = SimpleNamespace(completions=_Completions(self))
        self.is_closed = False

    def close(self) -> None:
        self.is_closed = True

    def _create(self, *, model: str | None = None, messages: list[dict[str, Any]] | None = None,
                timeout: Any = None, stream: bool = False, **_: Any) -> Any:
        seconds = _seconds(timeout if timeout is not None else self._timeout)
        # --sandbox plus an empty working directory keep injected text from reading
        # local files (#39 review r1). `--print=` with stream-json input reads stdin.
        argv = [self._command, "--print=", "--input-format", "stream-json", "--output-format", "stream-json",
                "--disable-slash-commands", "--mode", "plan", "--sandbox",
                f"--print-timeout={max(1, int(seconds))}s"]
        if model:
            argv += ["--model", model.removeprefix("google/")]
        stdin = json.dumps({"event": "user", "message": {"content": _flatten(messages or [])}}) + "\n"
        env = hermes_subprocess_env(inherit_credentials=False)
        for key in _GOOGLE_KEY_VARS:  # OAuth login only (provider-CLI mandate)
            env.pop(key, None)
        try:
            with tempfile.TemporaryDirectory(prefix="hermes-agy-") as workdir:
                proc = _run(argv, input=stdin, timeout=seconds + _GRACE_SECONDS, env=env, cwd=workdir)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"agy timed out after {seconds:.0f}s") from exc
        except OSError as exc:  # missing, not executable, or the OS refused to start it
            raise RuntimeError(f"agy could not start '{self._command}': {exc}") from exc
        if proc.returncode != 0:
            raise RuntimeError(f"agy exited {proc.returncode}: {(proc.stderr or '').strip()[-300:]}")
        text = _response(proc.stdout)
        if not text:
            raise RuntimeError("agy returned an empty response")

        message = SimpleNamespace(content=text, tool_calls=None, reasoning=None,
                                  reasoning_content=None, reasoning_details=None)
        usage = SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=0))
        completion = SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")],
                                     usage=usage, model=model or "agy")
        return _completion_to_stream_chunks(completion) if stream else completion
