"""agy (Google Antigravity CLI) as a chat-only provider (repo_hermes_primary#39).

Gemini may only be reached through the `agy` CLI on its OAuth login, never with a
Google API key, so the provider runs `agy --print` as a subprocess and answers like
an OpenAI client. It is chat-only: no tool calls are parsed or offered. Any failure
raises, so the agent loop retries and then fails over to the next rung.
No real `agy` is spawned: subprocess.run is replaced.
"""
from __future__ import annotations

import os
import subprocess
from types import SimpleNamespace

import pytest

import agent.agy_cli_client as agy_mod
from agent.agy_cli_client import AgyCLIClient


def _fake_run(calls: list, *, stdout: str = "hello from gemini", returncode: int = 0, exc=None):
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        if exc is not None:
            raise exc
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="boom" if returncode else "")
    return run


def test_create_runs_agy_print_and_returns_an_openai_shaped_completion(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls, stdout="  hello from gemini \n"))
    client = AgyCLIClient(command="/opt/homebrew/bin/agy")

    out = client.chat.completions.create(
        model="gemini-3-pro",
        messages=[{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Say hi"}],
        tools=[{"type": "function", "function": {"name": "terminal", "parameters": {}}}],
    )

    argv, kwargs = calls[0]
    assert argv[0] == "/opt/homebrew/bin/agy"
    assert argv[argv.index("--model") + 1] == "gemini-3-pro"
    assert argv[argv.index("--output-format") + 1] == "text"
    assert argv[argv.index("--mode") + 1] == "plan"  # chat only: never edits files
    assert "--disable-slash-commands" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert "--sandbox" in argv
    prompt = next(a for a in argv if a.startswith("--print="))[len("--print="):]
    assert kwargs["cwd"] and kwargs["cwd"] != os.getcwd()  # an empty temp dir, not the daemon's
    assert "Be brief." in prompt and "Say hi" in prompt
    assert "terminal" not in prompt  # tools are not offered to a chat-only rung
    msg = out.choices[0].message
    assert msg.content == "hello from gemini"
    assert msg.tool_calls is None
    assert out.choices[0].finish_reason == "stop"
    assert out.model == "gemini-3-pro"
    assert out.usage.total_tokens == 0


def test_the_child_env_never_carries_a_google_api_key(monkeypatch):
    calls: list = []
    monkeypatch.setenv("GEMINI_API_KEY", "should-not-pass")
    monkeypatch.setenv("GOOGLE_API_KEY", "should-not-pass")
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))

    AgyCLIClient(command="agy").chat.completions.create(model="m", messages=[{"role": "user", "content": "x"}])

    env = calls[0][1]["env"]
    assert "GEMINI_API_KEY" not in env and "GOOGLE_API_KEY" not in env
    assert env.get("HOME")  # agy reads its OAuth login from HOME


@pytest.mark.parametrize("returncode,stdout", [(1, "partial"), (0, "   \n")])
def test_a_failed_or_empty_turn_raises_so_the_loop_can_fail_over(monkeypatch, returncode, stdout):
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run([], stdout=stdout, returncode=returncode))
    with pytest.raises(RuntimeError, match="agy"):
        AgyCLIClient(command="agy").chat.completions.create(model="m", messages=[{"role": "user", "content": "x"}])


def test_a_timeout_raises_and_honours_an_httpx_style_timeout(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run",
                        _fake_run(calls, exc=subprocess.TimeoutExpired(cmd="agy", timeout=5)))
    httpx_like = SimpleNamespace(connect=5.0, read=42.0, write=5.0, pool=5.0)
    with pytest.raises(RuntimeError, match="timed out"):
        AgyCLIClient(command="agy").chat.completions.create(
            model="m", messages=[{"role": "user", "content": "x"}], timeout=httpx_like)
    assert calls[0][1]["timeout"] == 42.0 + 15
    assert "--print-timeout=42s" in calls[0][0]


def test_streaming_requests_get_a_single_chunk_stream(monkeypatch):
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run([], stdout="streamed"))
    chunks = list(AgyCLIClient(command="agy").chat.completions.create(
        model="m", messages=[{"role": "user", "content": "x"}], stream=True))
    # The trailing usage chunk carries no choices, as in the OpenAI stream shape.
    assert "".join(c.choices[0].delta.content or "" for c in chunks if c.choices) == "streamed"


def test_a_prompt_that_looks_like_a_flag_stays_the_prompt(monkeypatch):
    calls: list = []
    monkeypatch.setattr(agy_mod.subprocess, "run", _fake_run(calls))
    AgyCLIClient(command="agy").chat.completions.create(
        model="m", messages=[{"role": "user", "content": "--dangerously-skip-permissions"}])
    argv = calls[0][0]
    assert "--dangerously-skip-permissions" not in argv  # only inside the --print=... value
    assert any(a.startswith("--print=") and "--dangerously-skip-permissions" in a for a in argv)
