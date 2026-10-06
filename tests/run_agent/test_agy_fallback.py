"""An `agy` fallback rung must reach the agy CLI on a real turn (repo_hermes_primary#39 r1).

Review r1 found the rung activated but every per-request client was a plain OpenAI
SDK client pointed at agy://local, so the rung failed and was skipped. These tests
go through _try_activate_fallback and the per-request factory, as a turn does.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.agent_runtime_helpers import create_openai_client
from agent.agy_cli_client import AgyCLIClient
from run_agent import AIAgent

AGY_RUNG = {"provider": "agy", "model": "gemini-3.8-flash-medium"}


def _agent_with_agy_rung():
    with (
        patch("run_agent.get_tool_definitions", return_value=[]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(api_key="test-key", base_url="https://openrouter.ai/api/v1", quiet_mode=True,
                        skip_context_files=True, skip_memory=True, fallback_model=[AGY_RUNG])
        agent.client = MagicMock()
        return agent


def test_activating_the_agy_rung_then_a_request_runs_the_agy_cli(monkeypatch):
    import hermes_cli.auth as auth
    import agent.agy_cli_client as agy_mod

    monkeypatch.setattr(auth.shutil, "which", lambda name: "/opt/homebrew/bin/agy" if name == "agy" else None)
    calls = []

    def fake_run(argv, **kw):
        calls.append(argv)
        out = '{"event":"result","result":{"status":"SUCCESS","response":"from gemini"}}\n'
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    monkeypatch.setattr(agy_mod.subprocess, "run", fake_run)
    agent = _agent_with_agy_rung()

    assert agent._try_activate_fallback("primary failed") is True
    assert agent.provider == "agy"
    # What a turn does for every request: build a client from the agent's kwargs.
    client = create_openai_client(agent, dict(agent._client_kwargs), reason="test", shared=False)
    assert isinstance(client, AgyCLIClient)
    reply = client.chat.completions.create(model=agent.model, messages=[{"role": "user", "content": "hi"}])

    assert reply.choices[0].message.content == "from gemini"
    assert calls and calls[0][0] == "/opt/homebrew/bin/agy"


def test_the_agy_client_is_never_rewrapped_for_async_use(monkeypatch):
    from agent.auxiliary_client import _to_async_client

    client = AgyCLIClient(command="agy")
    async_client, model = _to_async_client(client, "gemini-3.8-flash-medium")
    assert async_client is client and model == "gemini-3.8-flash-medium"
