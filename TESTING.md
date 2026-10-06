# Testing

All tests are headless, silent and automated — no prompts, no manual steps, no browser
windows opening on a developer's desktop.

## Running the suites

**Always use `scripts/run_tests.sh`. Never call `pytest` directly.** The wrapper is what
gives you CI parity: it unsets credential env vars, pins `TZ=UTC`, `LANG=C.UTF-8` and
`PYTHONHASHSEED=0`, redirects `HERMES_HOME` to a temp dir, and runs each test file in its
own freshly-spawned subprocess so module-level state cannot leak between files. Bare
`pytest` on a developer machine with API keys set has repeatedly produced
works-locally-fails-in-CI incidents (and the reverse).

```bash
# Full suite, CI parity
scripts/run_tests.sh

# One directory or one test — pytest paths pass straight through
scripts/run_tests.sh tests/gateway/
scripts/run_tests.sh tests/agent/test_foo.py::test_x

# pytest flags pass through too
scripts/run_tests.sh -v --tb=long

# Integration tests (external services, API keys, Modal) — opt in explicitly
scripts/run_tests.sh -m integration
```

`pyproject.toml` sets `testpaths = ["tests"]` and `addopts = "-m 'not integration'"`, so
the default run is the fast lane. Integration tests are never a requirement for proving
an ordinary change works.

JavaScript and TypeScript are per-workspace — there is no root `test` script:

```bash
npm test --workspace ui-tui
npm test --workspace apps/desktop     # or: cd apps/desktop && npx vitest run
npm test --workspace web
```

Workspace dependencies install from the repo root (`npm run install:tui`,
`install:desktop`, `install:web`).

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

## Flake policy

The runner auto-retries a failing test **file** once in a fresh subprocess
(`--file-retries`, default 1; `HERMES_TEST_FILE_RETRIES=0` disables it). A pass on retry
counts as green but is printed in a `⚠ FLAKY` summary with both attempts' output. FLAKY is
a bug to fix, not noise to ignore — timing-sensitive tests must not assume a quiet runner:
use loose wall-clock bounds (≥ 2s), event-based synchronisation, and no negative-timing
races like `assert not _wait_until(...)`.

## What a change must prove

1. The non-integration suite is green before and after, run through
   `scripts/run_tests.sh`.
2. New behaviour has a test that fails without the change. A passing suite proves nothing
   about code no test touches.
3. Name one thing that should *not* have changed and verify it — regressions in the
   learning loop (memory, skill creation, session search) are the ones tests miss.
4. Cache behaviour: if the change touches prompt assembly, toolsets or system prompt
   construction, confirm the cached prefix still survives a multi-turn conversation.

## Lint and static checks

```bash
uv run ruff check .      # PLW1514 (explicit encoding) is enforced
npm run --ws check       # eslint + prettier across the JS workspaces
hadolint Dockerfile      # container lint
```

## CI

`.github/workflows/ci.yml` is the orchestrator: it classifies the diff once and calls
only the sub-workflows a change can affect (`js-tests`, `lint`, `docker`, `docs-site-checks`
and others), then aggregates into a single `all-checks-pass` gate for branch protection.
On `push` the classifier fails open so post-merge validation is never weakened.
