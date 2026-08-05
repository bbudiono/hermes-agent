# Testing

All tests are headless, silent and automated — no prompts, no manual steps, no browser
windows opening on a developer's desktop.

## Running the suites

```bash
# Python (default lane: integration tests excluded via pyproject addopts)
uv run pytest

# A single area
uv run pytest tests/gateway
uv run pytest tests/agent -x

# Integration tests (external services, API keys, Modal) — opt in explicitly
uv run pytest -m integration

# JavaScript / TypeScript
npm test
```

`pyproject.toml` sets `testpaths = ["tests"]` and `addopts = "-m 'not integration'"`, so
the default run is the fast lane. Integration tests are never a requirement for proving
an ordinary change works.

## Layout

| Path | Covers |
|------|--------|
| `tests/agent` | Agent core: turn loop, context assembly, compression |
| `tests/gateway` | Gateway sessions, platform adapters, delivery, authz |
| `tests/hermes_cli` | CLI commands and argument parsing |
| `tests/cron` | Scheduler, jobs, lifecycle guard |
| `tests/acp`, `tests/acp_adapter` | ACP adapter and permissions |
| `tests/hermes_state` | Persistence |
| `tests/computer_use`, `tests/dashboard`, `tests/docker` | Subsystem suites |
| `tests/e2e`, `tests/integration` | End-to-end and external-service paths |
| `tests/fakes`, `tests/fixtures`, `conftest.py` | Shared doubles and fixtures |
| `tests-js/` | Node-side tests for the desktop/web code |

## Markers

- `integration` — requires external services or API keys; excluded by default.
- `real_concurrent_gate` — opts out of the autouse stub disabling concurrent-instance
  detection.
- `real_agent_prewarm` — opts out of the autouse stub disabling the TUI pre-warm timer.

## What a change must prove

1. The non-integration suite is green before and after.
2. New behaviour has a test that fails without the change. A passing suite proves nothing
   about code no test touches.
3. Name one thing that should *not* have changed and verify it — regressions in the
   learning loop (memory, skill creation, session search) are the ones tests miss.
4. Cache behaviour: if the change touches prompt assembly, toolsets or system prompt
   construction, confirm the cached prefix still survives a multi-turn conversation.

## Lint and static checks

```bash
uv run ruff check .      # PLW1514 (explicit encoding) is enforced
npx eslint .             # JS/TS
hadolint Dockerfile      # container lint
```

## CI

`.github/workflows/ci.yml` is the orchestrator: it classifies the diff once and calls
only the sub-workflows a change can affect (`js-tests`, `lint`, `docker`, `docs-site-checks`
and others), then aggregates into a single `all-checks-pass` gate for branch protection.
On `push` the classifier fails open so post-merge validation is never weakened.
