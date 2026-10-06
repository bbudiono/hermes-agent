"""Photon adapter resilience to transient Spectrum/Envoy upstream overflow.

Covers the three behaviors that let the adapter ride through a Photon
"reset reason: overflow" event instead of degrading delivery and silently
dying (issue #50185):

  1. ``_is_retryable_error`` classifies the Envoy/sidecar overflow strings as
     retryable so ``_send_with_retry`` actually engages its backoff loop.
  2. ``send_typing`` is rate-gated per chat, and ``stop_typing`` resets the
     gate so the next turn's typing indicator fires immediately.
  3. ``_supervise_sidecar`` detects an unexpected sidecar exit and raises a
     ``retryable=True`` fatal so the gateway reconnect watcher revives the
     platform — instead of returning silently and leaving ``_inbound_loop``
     spinning against a dead port.
  4. ``_monitor_sidecar_health`` promotes degraded upstream stream health
     reported by ``/healthz`` into the same retryable reconnect path.

No Node sidecar is spawned and no ports are bound.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from gateway.config import PlatformConfig
from plugins.platforms.photon.adapter import PhotonAdapter


def _make_adapter(monkeypatch: pytest.MonkeyPatch) -> PhotonAdapter:
    monkeypatch.setenv("PHOTON_PROJECT_ID", "test-project-id")
    monkeypatch.setenv("PHOTON_PROJECT_SECRET", "test-project-secret")
    cfg = PlatformConfig(enabled=True, token="", extra={})
    return PhotonAdapter(cfg)


# -- Gap 1: retryable classification of overflow errors ---------------------

@pytest.mark.parametrize(
    "error",
    [
        "UNAVAILABLE: internal sidecar error",
        "upstream connect error or disconnect/reset before headers",
        "reset reason: overflow",
        # Case-insensitive: real strings arrive with mixed case.
        "Internal Sidecar Error",
    ],
)
def test_overflow_strings_classified_retryable(error: str) -> None:
    assert PhotonAdapter._is_retryable_error(error) is True


def test_unrelated_error_not_retryable() -> None:
    # A genuine permanent failure must NOT be retried.
    assert PhotonAdapter._is_retryable_error("400 bad request: invalid spaceId") is False
    assert PhotonAdapter._is_retryable_error(None) is False


def test_base_network_patterns_still_match() -> None:
    # The override delegates to the base classifier first, so generic
    # network strings keep working.
    assert PhotonAdapter._is_retryable_error("ConnectError: connection refused") is True


# -- Gap 2: typing-indicator cooldown ---------------------------------------

@pytest.mark.asyncio
async def test_typing_cooldown_suppresses_rapid_repeats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    calls: list[Dict[str, Any]] = []

    async def _fake_call(path: str, payload: Dict[str, Any]) -> Any:
        calls.append(payload)
        return {"ok": True}

    monkeypatch.setattr(adapter, "_sidecar_call", _fake_call)

    # First call fires; immediate repeats are suppressed by the cooldown.
    await adapter.send_typing("chat-1")
    await adapter.send_typing("chat-1")
    await adapter.send_typing("chat-1")

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_typing_cooldown_is_per_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    calls: list[str] = []

    async def _fake_call(path: str, payload: Dict[str, Any]) -> Any:
        calls.append(payload["spaceId"])
        return {"ok": True}

    monkeypatch.setattr(adapter, "_sidecar_call", _fake_call)

    # Different chats have independent cooldowns.
    await adapter.send_typing("chat-1")
    await adapter.send_typing("chat-2")

    assert calls == ["chat-1", "chat-2"]


@pytest.mark.asyncio
async def test_stop_typing_resets_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    starts = 0

    async def _fake_call(path: str, payload: Dict[str, Any]) -> Any:
        nonlocal starts
        if payload.get("state") == "start":
            starts += 1
        return {"ok": True}

    monkeypatch.setattr(adapter, "_sidecar_call", _fake_call)

    # A start, then a stop (end of turn), then a start for the next turn must
    # fire immediately — the cooldown only suppresses rapid consecutive starts
    # without an intervening stop.
    await adapter.send_typing("chat-1")
    await adapter.stop_typing("chat-1")
    await adapter.send_typing("chat-1")

    assert starts == 2


# -- Gap 3: sidecar crash detection -----------------------------------------

class _EofStdout:
    """A proc.stdout whose readline() reports immediate EOF (dead sidecar)."""

    def readline(self) -> bytes:
        return b""


class _DeadProc:
    """Minimal subprocess.Popen stand-in for a sidecar that has exited."""

    def __init__(self, exit_code: int = 1) -> None:
        self.stdout = _EofStdout()
        self.stdin = None
        self._exit_code = exit_code

    def poll(self) -> int:
        return self._exit_code


@pytest.mark.asyncio
async def test_unexpected_sidecar_exit_raises_retryable_fatal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    # Simulate a live session whose sidecar then dies underneath it.
    adapter._inbound_running = True

    notified: list[bool] = []

    async def _fake_notify() -> None:
        notified.append(True)

    monkeypatch.setattr(adapter, "_notify_fatal_error", _fake_notify)

    await adapter._supervise_sidecar(_DeadProc(exit_code=137))  # type: ignore[arg-type]
    await asyncio.gather(*adapter._fatal_notify_tasks)

    assert adapter.has_fatal_error is True
    assert adapter.fatal_error_code == "SIDECAR_CRASHED"
    # retryable=True routes the platform into the reconnect watcher rather
    # than crashing the whole gateway.
    assert adapter.fatal_error_retryable is True
    assert adapter._running is False
    assert notified == [True]


@pytest.mark.asyncio
async def test_clean_shutdown_does_not_raise_fatal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    # disconnect() sets _inbound_running = False before stopping the sidecar,
    # so the detection block must NOT fire on a clean shutdown.
    adapter._inbound_running = False

    notified: list[bool] = []

    async def _fake_notify() -> None:
        notified.append(True)

    monkeypatch.setattr(adapter, "_notify_fatal_error", _fake_notify)

    await adapter._supervise_sidecar(_DeadProc(exit_code=0))  # type: ignore[arg-type]

    assert adapter.has_fatal_error is False
    assert notified == []


@pytest.mark.asyncio
async def test_degraded_stream_health_raises_retryable_fatal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    adapter._inbound_running = True
    adapter._sidecar_health_interval = 0.0

    async def _fake_call(path: str, payload: Dict[str, Any]) -> Any:
        assert path == "/healthz"
        return {
            "ok": True,
            "stream": {
                "ok": False,
                "state": "degraded",
                "degradedForMs": 120000,
                "lastIssue": "[spectrum.stream] stream interrupted; reconnecting",
            },
        }

    notified: list[bool] = []

    async def _fake_notify() -> None:
        notified.append(True)
        adapter._inbound_running = False

    monkeypatch.setattr(adapter, "_sidecar_call", _fake_call)
    monkeypatch.setattr(adapter, "_notify_fatal_error", _fake_notify)

    await adapter._monitor_sidecar_health()
    await asyncio.gather(*adapter._fatal_notify_tasks)

    assert adapter.has_fatal_error is True
    assert adapter.fatal_error_code == "UPSTREAM_STREAM_DEGRADED"
    assert adapter.fatal_error_retryable is True
    assert notified == [True]


# -- repo_hermes_primary#36: the fatal handler tears down the task it came from --
#
# The gateway's handler disconnects the adapter, which cancels the health and
# supervisor tasks. Awaited from inside one of them, the handler was cancelled at
# its next await and never queued the reconnect: Photon stayed down for 57 h on
# 2026-10-03 until a gateway restart. These drive disconnect() the way
# GatewayRunner._await_adapter_cleanup_with_timeout does (a child task + wait).

async def _gateway_handler(queued: list[str], failed: PhotonAdapter) -> None:
    cleanup = asyncio.ensure_future(failed.disconnect())
    await asyncio.wait({cleanup}, timeout=5)
    await cleanup
    queued.append(failed.fatal_error_code)


async def _until(predicate, timeout: float = 5.0) -> None:
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_a_degraded_stream_still_queues_the_reconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    adapter._inbound_running = True
    adapter._sidecar_health_interval = 0.0

    async def _degraded(path: str, payload: Dict[str, Any]) -> Any:
        return {"ok": True, "stream": {"ok": False, "state": "degraded"}}

    async def _stop_sidecar() -> None:
        await asyncio.sleep(0)

    queued: list[str] = []
    monkeypatch.setattr(adapter, "_sidecar_call", _degraded)
    monkeypatch.setattr(adapter, "_stop_sidecar", _stop_sidecar)
    adapter.set_fatal_error_handler(lambda a: _gateway_handler(queued, a))
    adapter._sidecar_health_task = asyncio.get_running_loop().create_task(
        adapter._monitor_sidecar_health()
    )

    await _until(lambda: queued)
    assert queued == ["UPSTREAM_STREAM_DEGRADED"]


@pytest.mark.asyncio
async def test_two_hand_offs_in_one_incident_both_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Review r2 (mercury, hermes): the monitor and the supervisor can both fire;
    # each hand-off must stay referenced until it finishes.
    adapter = _make_adapter(monkeypatch)
    ran: list[int] = []

    async def _fake_notify() -> None:
        await asyncio.sleep(0)
        ran.append(1)

    monkeypatch.setattr(adapter, "_notify_fatal_error", _fake_notify)
    adapter._hand_off_fatal_error()
    adapter._hand_off_fatal_error()
    assert len(adapter._fatal_notify_tasks) == 2

    await asyncio.gather(*adapter._fatal_notify_tasks)
    assert ran == [1, 1]
    await asyncio.sleep(0)  # done-callbacks run on the next loop pass
    assert adapter._fatal_notify_tasks == set()


@pytest.mark.asyncio
async def test_the_real_gateway_handler_queues_photon_after_a_degraded_stream(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from unittest.mock import AsyncMock

    from gateway.config import GatewayConfig
    from gateway.run import GatewayRunner

    adapter = _make_adapter(monkeypatch)
    adapter._inbound_running = True
    adapter._sidecar_health_interval = 0.0

    async def _degraded(path: str, payload: Dict[str, Any]) -> Any:
        return {"ok": True, "stream": {"ok": False, "state": "degraded"}}

    async def _stop_sidecar() -> None:
        await asyncio.sleep(0)

    monkeypatch.setattr(adapter, "_sidecar_call", _degraded)
    monkeypatch.setattr(adapter, "_stop_sidecar", _stop_sidecar)
    runner = GatewayRunner(GatewayConfig(platforms={}, sessions_dir=tmp_path / "sessions"))
    runner.adapters = {adapter.platform: adapter}
    runner.delivery_router.adapters = runner.adapters
    runner.stop = AsyncMock()
    adapter.set_fatal_error_handler(runner._handle_adapter_fatal_error)
    adapter._sidecar_health_task = asyncio.get_running_loop().create_task(
        adapter._monitor_sidecar_health()
    )

    await _until(lambda: adapter.platform in runner._failed_platforms)
    assert runner.adapters == {}
    runner.stop.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_crashed_sidecar_still_queues_the_reconnect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _make_adapter(monkeypatch)
    adapter._inbound_running = True

    async def _stop_sidecar() -> None:  # the real one cancels the supervisor task
        if adapter._sidecar_supervisor_task is not None:
            adapter._sidecar_supervisor_task.cancel()
            adapter._sidecar_supervisor_task = None
        await asyncio.sleep(0)

    queued: list[str] = []
    monkeypatch.setattr(adapter, "_stop_sidecar", _stop_sidecar)
    adapter.set_fatal_error_handler(lambda a: _gateway_handler(queued, a))
    adapter._sidecar_supervisor_task = asyncio.get_running_loop().create_task(
        adapter._supervise_sidecar(_DeadProc(exit_code=137))  # type: ignore[arg-type]
    )

    await _until(lambda: queued)
    assert queued == ["SIDECAR_CRASHED"]
