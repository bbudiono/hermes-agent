"""agy (Google Antigravity CLI) as a chat-only provider (repo_hermes_primary#39).

Gemini may only be reached through the `agy` CLI on its OAuth login, never with a
Google API key, so the provider runs `agy` as a subprocess and answers like an
OpenAI client. The conversation goes in on stdin as one stream-json `user` event
(review r2: a single argv element hits E2BIG on long turns and shows the text in
`ps`). It is chat-only. Any failure raises, so the loop retries and fails over.
No real `agy` is spawned: subprocess.run is replaced.
"""
from __future__ import annotations

import json
import os
import subprocess
from types import SimpleNamespace

import pytest

import agent.agy_cli_client as agy_mod
from agent.agy_cli_client import AgyCLIClient


def _result(response="hello from gemini", status="SUCCESS", error=""):
    init = json.dumps({"event": "init", "conversation_id": "c1", "init": {"model": "m"}})
    res = json.dumps({"event": "result", "result": {"status": status, "response": response, "error": error}})
    return f"{init}\n{res}\n"


def _fake_run(calls: list, *, stdout: str | None = None, returncode: int = 0, exc=None):
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        if exc is not None:
            raise exc
        return SimpleNamespace(returncode=returncode, stdout=_result() if stdout is None else stdout,
                               stderr="boom" if returncode else "")
    return run


def _sent(calls) -> dict:
    """The stream-json event written to agy's stdin."""
    return json.loads(calls[0][1]["input"].strip())


def _create(client, **kw):
    kw.setdefault("model", "m")
    kw.setdefault("messages", [{"role": "user", "content": "x"}])
    return client.chat.completions.create(**kw)


def test_the_conversation_goes_in_on_stdin_and_the_result_comes_back(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls, stdout=_result("  hello from gemini \n")))

    out = _create(AgyCLIClient(command="/opt/homebrew/bin/agy"), model="gemini-3-pro",
                  messages=[{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Say hi"}],
                  tools=[{"type": "function", "function": {"name": "terminal", "parameters": {}}}])

    argv, kwargs = calls[0]
    assert argv[0] == "/opt/homebrew/bin/agy"
    assert "--print=" in argv
    assert argv[argv.index("--input-format") + 1] == "stream-json"
    assert argv[argv.index("--output-format") + 1] == "stream-json"
    assert argv[argv.index("--model") + 1] == "gemini-3-pro"
    assert argv[argv.index("--mode") + 1] == "plan"  # chat only: never edits files
    assert "--sandbox" in argv and "--disable-slash-commands" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert kwargs["cwd"] and kwargs["cwd"] != os.getcwd()  # an empty temp dir, not the daemon's
    event = _sent(calls)
    assert event["event"] == "user"
    prompt = event["message"]["content"]
    assert "Be brief." in prompt and "Say hi" in prompt
    assert "terminal" not in prompt  # tools are not offered to a chat-only rung
    msg = out.choices[0].message
    assert msg.content == "hello from gemini"
    assert msg.tool_calls is None
    assert out.choices[0].finish_reason == "stop"
    assert out.model == "gemini-3-pro"


def test_a_long_or_secret_conversation_never_reaches_the_command_line(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    huge = "token=sk-secret " + "x" * 300_000  # past Linux MAX_ARG_STRLEN (128 KiB)

    _create(AgyCLIClient(command="agy"), messages=[{"role": "user", "content": huge}])

    argv = calls[0][0]
    assert max(len(a) for a in argv) < 1000
    assert not any("sk-secret" in a for a in argv)
    assert "sk-secret" in _sent(calls)["message"]["content"]


def test_a_prompt_that_looks_like_a_flag_stays_the_prompt(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    _create(AgyCLIClient(command="agy"), messages=[{"role": "user", "content": "--dangerously-skip-permissions"}])
    assert "--dangerously-skip-permissions" not in calls[0][0]
    assert "--dangerously-skip-permissions" in _sent(calls)["message"]["content"]


def test_the_child_env_never_carries_a_google_api_key(monkeypatch):
    calls: list = []
    monkeypatch.setenv("GEMINI_API_KEY", "should-not-pass")
    monkeypatch.setenv("GOOGLE_API_KEY", "should-not-pass")
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    _create(AgyCLIClient(command="agy"))
    env = calls[0][1]["env"]
    assert "GEMINI_API_KEY" not in env and "GOOGLE_API_KEY" not in env
    assert env.get("HOME")  # agy reads its OAuth login from HOME


@pytest.mark.parametrize("returncode,stdout", [
    (1, "partial"),                                       # non-zero exit
    (0, _result(response="   \n")),                       # empty answer
    (0, _result(response="", status="ERROR", error="quota")),  # agy reported an error
    (0, '{"event":"init"}\n'),                            # no result event at all
])
def test_a_failed_or_empty_turn_raises_so_the_loop_can_fail_over(monkeypatch, returncode, stdout):
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run([], stdout=stdout, returncode=returncode))
    with pytest.raises(RuntimeError, match="agy"):
        _create(AgyCLIClient(command="agy"))


@pytest.mark.parametrize("exc", [OSError(7, "Argument list too long"), PermissionError(13, "denied")])
def test_any_os_error_becomes_a_runtime_error(monkeypatch, exc):
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run([], exc=exc))
    with pytest.raises(RuntimeError, match="agy"):
        _create(AgyCLIClient(command="agy"))


def test_a_timeout_raises_and_honours_an_httpx_style_timeout(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run",
                        _fake_run(calls, exc=subprocess.TimeoutExpired(cmd="agy", timeout=5)))
    httpx_like = SimpleNamespace(connect=5.0, read=42.0, write=5.0, pool=5.0)
    with pytest.raises(RuntimeError, match="timed out"):
        _create(AgyCLIClient(command="agy"), timeout=httpx_like)
    assert calls[0][1]["timeout"] == 42.0 + 15
    assert "--print-timeout=42s" in calls[0][0]


def test_a_sub_second_timeout_never_becomes_zero(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    _create(AgyCLIClient(command="agy"), timeout=0.4)
    assert "--print-timeout=1s" in calls[0][0]


def test_a_provider_prefixed_model_is_passed_bare(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    out = _create(AgyCLIClient(command="agy"), model="google/gemini-3.8-flash-medium")
    assert calls[0][0][calls[0][0].index("--model") + 1] == "gemini-3.8-flash-medium"
    assert out.model == "google/gemini-3.8-flash-medium"


def test_tool_calls_and_attachments_are_named_not_silently_dropped(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    _create(AgyCLIClient(command="agy"), messages=[
        {"role": "user", "content": [{"type": "text", "text": "What is in this?"},
                                     {"type": "image_url", "image_url": {"url": "data:..."}}]},
        {"role": "assistant", "content": None,
         "tool_calls": [{"function": {"name": "read_file", "arguments": "{}"}}]},
        {"role": "tool", "content": "file body"},
    ])
    prompt = _sent(calls)["message"]["content"]
    assert "[non-text attachment omitted]" in prompt
    assert "read_file" in prompt and "file body" in prompt


def test_streaming_requests_get_a_single_chunk_stream(monkeypatch):
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run([], stdout=_result("streamed")))
    chunks = list(_create(AgyCLIClient(command="agy"), stream=True))
    # The trailing usage chunk carries no choices, as in the OpenAI stream shape.
    assert "".join(c.choices[0].delta.content or "" for c in chunks if c.choices) == "streamed"
