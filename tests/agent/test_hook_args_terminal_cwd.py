"""pre_tool_call hook args carry the terminal session's effective cwd
(repo_ecosystem_agents#700): the consent-boundary plugin's script-file email
lane resolves RELATIVE script paths against args cwd/workdir — without this
enrichment the lane is inert whenever the model omits workdir."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent.tool_executor import _hook_args_with_terminal_cwd  # noqa: E402


class _Env:
    def __init__(self, cwd):
        self.cwd = cwd


def test_terminal_without_workdir_gains_session_cwd(monkeypatch):
    import tools.terminal_tool as tt
    monkeypatch.setattr(tt, "get_active_env", lambda tid: _Env("/srv/daemon"))
    args = {"command": "python3 send.py"}
    out = _hook_args_with_terminal_cwd("terminal", args, "t1")
    assert out["cwd"] == "/srv/daemon"
    assert "cwd" not in args  # original execution args never mutated


def test_explicit_workdir_wins(monkeypatch):
    import tools.terminal_tool as tt
    monkeypatch.setattr(tt, "get_active_env", lambda tid: _Env("/other"))
    args = {"command": "x", "workdir": "/explicit"}
    assert _hook_args_with_terminal_cwd("terminal", args, "t1") is args


def test_non_terminal_passthrough(monkeypatch):
    args = {"command": "x"}
    assert _hook_args_with_terminal_cwd("todo", args, "t1") is args


def test_no_env_or_error_degrades_to_original(monkeypatch):
    import tools.terminal_tool as tt
    monkeypatch.setattr(tt, "get_active_env", lambda tid: None)
    args = {"command": "x"}
    assert _hook_args_with_terminal_cwd("terminal", args, "t1") is args
    def boom(tid):
        raise RuntimeError("env store down")
    monkeypatch.setattr(tt, "get_active_env", boom)
    assert _hook_args_with_terminal_cwd("terminal", args, "t1") is args
