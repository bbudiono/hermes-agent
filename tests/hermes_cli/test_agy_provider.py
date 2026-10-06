"""agy is an external-process provider a fallback rung can reach (repo_hermes_primary#39)."""
from __future__ import annotations

import pytest

from hermes_cli import auth
from hermes_cli.auth import AuthError, PROVIDER_REGISTRY, resolve_external_process_provider_credentials


def test_agy_is_registered_as_an_external_process_provider_without_api_keys():
    cfg = PROVIDER_REGISTRY["agy"]
    assert cfg.auth_type == "external_process"
    assert not getattr(cfg, "api_key_env_vars", ())  # OAuth via the CLI only, never a key


def test_credentials_resolve_the_agy_command_on_path(monkeypatch):
    monkeypatch.setattr(auth.shutil, "which", lambda name: "/opt/homebrew/bin/agy" if name == "agy" else None)
    creds = resolve_external_process_provider_credentials("agy")
    assert creds["provider"] == "agy"
    assert creds["command"] == "/opt/homebrew/bin/agy"


def test_a_missing_agy_cli_is_a_clear_auth_error(monkeypatch):
    monkeypatch.setattr(auth.shutil, "which", lambda name: None)
    with pytest.raises(AuthError) as err:
        resolve_external_process_provider_credentials("agy")
    assert err.value.code == "missing_agy_cli"


def test_a_fallback_rung_resolves_an_agy_client(monkeypatch):
    from agent import auxiliary_client
    from agent.agy_cli_client import AgyCLIClient

    monkeypatch.setattr(auth.shutil, "which", lambda name: "/opt/homebrew/bin/agy" if name == "agy" else None)
    client, model = auxiliary_client.resolve_provider_client("agy", "gemini-3-pro")
    assert isinstance(client, AgyCLIClient)
    assert model == "gemini-3-pro"


def test_a_fallback_rung_without_agy_is_skipped_not_fatal(monkeypatch):
    from agent import auxiliary_client

    monkeypatch.setattr(auth.shutil, "which", lambda name: None)
    assert auxiliary_client.resolve_provider_client("agy", "gemini-3-pro") == (None, None)
