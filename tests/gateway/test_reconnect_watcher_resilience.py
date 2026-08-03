"""Reconnect-watcher resilience: the 2026-07-30 photon 3-day outage class.

A runtime fatal error on a platform that was ALREADY queued in
``_failed_platforms`` was silently skipped by ``_handle_adapter_fatal_error``
(no re-queue, no next_retry refresh), and a concurrent removal from
``_failed_platforms`` during the watcher's iteration raised KeyError OUTSIDE
the per-attempt try/except — killing the unsupervised watcher task forever.
Either path leaves the platform state stuck on "retrying" while nothing ever
retries. These tests pin the fixes:

1. already-queued + retryable fatal → next_retry refreshed to "now"
2. platform missing from gateway config → fall back to the adapter's config
3. the per-pass loop tolerates concurrent ``_failed_platforms`` mutation
4. the watcher task is supervised — a crash schedules a replacement
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.run import GatewayRunner


class _FakeAdapter:
    def __init__(
        self,
        platform: Platform,
        *,
        retryable: bool = True,
        config: PlatformConfig | None = None,
    ) -> None:
        self.platform = platform
        self.fatal_error_code = "TEST_ERR"
        self.fatal_error_message = "boom"
        self.fatal_error_retryable = retryable
        self.config = config or PlatformConfig(enabled=True, token="t")
        self.disconnect = AsyncMock()


def _make_runner() -> GatewayRunner:
    runner = GatewayRunner(GatewayConfig())
    runner._update_platform_runtime_status = lambda *a, **k: None
    return runner


@pytest.mark.asyncio
async def test_fatal_error_refreshes_next_retry_when_already_queued() -> None:
    runner = _make_runner()
    platform = Platform.TELEGRAM
    cfg = PlatformConfig(enabled=True, token="t")
    runner.config.platforms[platform] = cfg
    # Queued earlier with a retry scheduled far in the future (backoff cap).
    runner._failed_platforms[platform] = {
        "config": cfg,
        "attempts": 5,
        "next_retry": time.monotonic() + 3600,
    }

    adapter = _FakeAdapter(platform)
    await runner._handle_adapter_fatal_error(adapter)

    info = runner._failed_platforms[platform]
    assert info["next_retry"] <= time.monotonic(), (
        "an already-queued platform hit by a new retryable fatal error must "
        "be retried promptly, not left waiting out a stale backoff"
    )


@pytest.mark.asyncio
async def test_fatal_error_queues_with_adapter_config_fallback() -> None:
    runner = _make_runner()
    platform = Platform.TELEGRAM
    # Gateway config has NO entry for this platform (plugin/runtime-registered
    # platforms can miss the static map) — the adapter's own config must be
    # used so the platform is still queued for reconnection.
    adapter = _FakeAdapter(platform)

    await runner._handle_adapter_fatal_error(adapter)

    assert platform in runner._failed_platforms, (
        "retryable fatal error must queue the platform for reconnection even "
        "when gateway config lacks an entry — silent drop caused a 3-day "
        "outage with state stuck on 'retrying'"
    )
    assert runner._failed_platforms[platform]["config"] is adapter.config


@pytest.mark.asyncio
async def test_reconnect_pass_tolerates_concurrent_removal() -> None:
    runner = _make_runner()
    runner._running = True
    gone = Platform.TELEGRAM
    stays = Platform.SLACK
    cfg = PlatformConfig(enabled=True, token="t")
    runner._failed_platforms[gone] = {
        "config": cfg,
        "attempts": 0,
        "next_retry": time.monotonic(),
    }
    runner._failed_platforms[stays] = {
        "config": cfg,
        "attempts": 0,
        # Not due yet — must simply be skipped, not KeyError'd.
        "next_retry": time.monotonic() + 3600,
    }

    # Simulate another coroutine removing `gone` after the pass snapshots keys.
    class _RacingDict(dict):
        def get(self, key, default=None):
            if key is gone and key in self:
                del self[gone]
                return None
            return super().get(key, default)

    runner._failed_platforms = _RacingDict(runner._failed_platforms)

    # Must not raise — a KeyError here used to kill the watcher task forever.
    await runner._reconnect_pass()

    assert stays in runner._failed_platforms


@pytest.mark.asyncio
async def test_watcher_task_is_supervised_and_restarts_after_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _make_runner()
    runner._running = True
    monkeypatch.setattr(type(runner), "_WATCHER_RESTART_DELAY", 0.0, raising=False)

    spawns = []

    async def _crashing_watcher() -> None:
        spawns.append(1)
        if len(spawns) == 1:
            raise RuntimeError("watcher crashed")
        # Second incarnation: stay alive briefly, then exit quietly after the
        # test flips _running off.
        while runner._running:
            await asyncio.sleep(0.01)

    monkeypatch.setattr(
        runner, "_platform_reconnect_watcher", _crashing_watcher
    )

    runner._start_reconnect_watcher()
    await asyncio.sleep(0.05)

    assert len(spawns) >= 2, (
        "a crashed reconnect watcher must be restarted — an unsupervised "
        "create_task dies silently and nothing ever reconnects again"
    )

    runner._running = False
    await asyncio.sleep(0.05)


def test_watcher_restart_backoff_grows_and_caps() -> None:
    """A deterministically-crashing watcher must not respawn at a fixed 5s
    forever — the restart delay backs off exponentially to a cap, and resets
    once the streak is cleared (after a stable run)."""
    runner = _make_runner()
    runner._watcher_crash_streak = 0
    assert runner._watcher_restart_backoff() == 5.0
    runner._watcher_crash_streak = 3
    assert runner._watcher_restart_backoff() == 40.0
    runner._watcher_crash_streak = 50
    assert runner._watcher_restart_backoff() == 300.0
