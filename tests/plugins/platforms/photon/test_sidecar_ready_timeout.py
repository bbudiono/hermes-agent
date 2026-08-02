"""Sidecar readiness timeout: env-configurable, load-tolerant default.

The hardcoded 15s window failed every reconnect attempt while the host was
under CI load (2026-08-02): healthy baseline startup is ~3s, but the node
sidecar's module import + top-level Spectrum init couldn't finish in 15s at
loadavg 25+. The timeout must be configurable via PHOTON_SIDECAR_READY_TIMEOUT
with a default that survives a busy host.
"""
from __future__ import annotations

import pytest

from plugins.platforms.photon import adapter as photon_adapter


def test_ready_timeout_default_is_60s(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PHOTON_SIDECAR_READY_TIMEOUT", raising=False)
    assert photon_adapter._sidecar_ready_timeout() == 60.0


def test_ready_timeout_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHOTON_SIDECAR_READY_TIMEOUT", "120")
    assert photon_adapter._sidecar_ready_timeout() == 120.0


@pytest.mark.parametrize("raw", ["", "not-a-number", "0", "-5", "nan", "inf", "-inf"])
def test_ready_timeout_invalid_values_fall_back_to_default(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    monkeypatch.setenv("PHOTON_SIDECAR_READY_TIMEOUT", raw)
    assert photon_adapter._sidecar_ready_timeout() == 60.0


def test_ready_timeout_is_clamped_to_upper_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHOTON_SIDECAR_READY_TIMEOUT", "99999999")
    assert (
        photon_adapter._sidecar_ready_timeout()
        == photon_adapter._MAX_SIDECAR_READY_TIMEOUT
    )
