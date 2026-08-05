# Hermes Agent — BLUEPRINT

<P0_PROJECT_REQUIREMENTS>

Hermes Agent is a personal AI agent whose single agent core is reused across four
surfaces: the `hermes` CLI, the messaging gateway (Telegram, Discord, Slack, WhatsApp,
Signal and ~20 more platforms), the terminal UI, and the Electron desktop app. These are
the non-negotiable requirements every change is measured against.

1. **One agent core, many surfaces.** `agent/` owns the turn loop, provider adapters and
   tool dispatch. CLI (`hermes_cli/`), gateway (`gateway/`), TUI (`tui_gateway/`), ACP
   adapter (`acp_adapter/`) and the desktop app (`apps/desktop`) are transports over that
   core, never forks of it.
2. **Per-conversation prompt caching is sacred.** A long-lived conversation reuses a
   cached prefix on every turn. Mutating past context, swapping toolsets mid-conversation
   or rebuilding the system prompt invalidates the cache and multiplies the user's cost.
   Context compression is the single sanctioned exception.
3. **Narrow waist, capability at the edges.** Every model tool is sent on every API call,
   so new *core* tools carry a high bar. New capability arrives as a CLI command plus a
   skill, a service-gated tool, or a plugin under `plugins/`.
4. **Provider neutrality.** Any OpenAI-compatible endpoint, Nous Portal, OpenRouter,
   Anthropic or a self-hosted model must work with no core code change — backends ship as
   plugins under `plugins/model-providers/`, registered through the `providers/` ABC.
   Switching is a `hermes model` operation.
5. **Runs anywhere.** Six terminal backends (local, Docker, SSH, Singularity, Modal,
   Daytona) must stay interchangeable, including the serverless hibernate/wake paths.
6. **The learning loop stays closed.** Agent-curated memory, autonomous skill creation,
   in-use skill improvement and FTS5 session search are product-defining; a change that
   silently degrades any of them is a regression even when tests pass.
7. **Tests are headless, silent and automated.** `scripts/run_tests.sh` is the only
   sanctioned Python invocation (it enforces CI parity); `-m 'not integration'` is the
   default lane, and integration tests are opt-in and must never be required to prove a
   normal change works.

8. **`.env` is secrets only.** Behavioural settings live in `~/.hermes/config.yaml`,
   resolved profile-aware via `get_hermes_home()`. New `HERMES_*` env vars for non-secret
   config are rejected.

</P0_PROJECT_REQUIREMENTS>

## Scope Boundaries

In scope: the agent core, the transports above, the tool/skill/plugin system, the cron
scheduler, the documentation site under `website/`, and the packaging/installer paths.

Out of scope: model training, hosted inference infrastructure, and per-user secrets —
credentials live in the user's environment or config, never in this repository.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Core / CLI / gateway | Python 3.11–3.13, `uv` |
| Desktop + web UI | Electron, TypeScript, Vite (`apps/desktop`, `web/`) |
| Docs site | Docusaurus (`website/`) |
| Packaging | setuptools wheel, Docker, Nix flake, `scripts/install.sh` / `scripts/install.ps1` |
| Tests | pytest via `scripts/run_tests.sh` (`tests/`), vitest per JS workspace |
| Lint | ruff (PLW1514 enforced), eslint, hadolint, prettier |

## Delivery Criteria

A change ships when: `pytest` is green on the non-integration lane, the affected CI
sub-workflows pass, no new core model tool was added without an explicit justification,
and the docs listed in `docs/INDEX.md` still describe what the code does.
