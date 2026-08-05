# Architecture

Hermes is one agent core with several transports bolted onto it. Everything below is a
description of what is in the tree today, not an aspiration.

## Layers

**Entry points** (`pyproject.toml [project.scripts]`)

| Command | Module | Role |
|---------|--------|------|
| `hermes` | `hermes_cli.main:main` | User-facing CLI: setup, model selection, gateway control, backups |
| `hermes-agent` | `run_agent:main` | Runs a single agent session directly |
| `hermes-acp` | `acp_adapter.entry:main` | Agent Client Protocol adapter for external editors |

**Agent core** (`agent/`, ~120 modules) — the turn loop, provider adapters
(`anthropic_adapter.py` and friends), context assembly, compression, subagent
delegation, and usage accounting. Sibling top-level modules carry the shared state and
schema: `hermes_state.py` (persistence), `model_tools.py` / `toolsets.py` (the tool
schema sent to the model), `hermes_constants.py`, `trajectory_compressor.py`.

**Providers** (`providers/`) — a thin base class plus per-provider shims so any
OpenAI-compatible endpoint, Nous Portal, OpenRouter or Anthropic works unchanged.

**Tools** (`tools/`) — the implementations behind the model-visible tool schema: shell,
browser (Camoufox), file editing, delegation, approval flows.

**Transports**

- `gateway/` — the long-running multi-platform process. `run.py` is the loop,
  `session.py` holds per-conversation state, `platforms/` has the ~20 channel adapters,
  `relay/` the remote connector, `slash_commands.py` the command surface, plus delivery
  ledger, pairing, drain control, scale-to-zero and shutdown watchdogs.
- `tui_gateway/` — terminal UI host and event publisher.
- `acp_adapter/` — editor integration over ACP with its own permission/approval model.
- `apps/desktop`, `web/` — Electron shell and web frontend (TypeScript/Vite).

**Scheduling** (`cron/`) — jobs, executions, lifecycle guard and scheduler providers, so
automations run unattended and deliver to any platform.

**Extension surface** (`skills/`, `optional-skills/`, `plugins/`,
`optional-mcps/`) — where new capability is meant to land. Skills follow the
agentskills.io layout; plugins register their own tools and hooks.

**Docs site** (`website/`) — Docusaurus source for the published documentation.

## Request path

A message arrives on a platform adapter in `gateway/platforms/`, is normalised into a
gateway session (`gateway/session.py`), and handed to the agent core. The core assembles
the cached prompt prefix plus the new turn, calls the provider, and dispatches any tool
calls into `tools/` (or a plugin). Output streams back through the delivery layer to the
originating channel. The CLI and TUI paths skip the gateway and call the core directly.

## Invariants

1. The cached prompt prefix is never invalidated mid-conversation except by explicit
   context compression.
2. Transports do not implement agent behaviour — behaviour changes go in `agent/`.
3. A new capability defaults to a skill or plugin; a new core model tool needs an
   argued case, because it costs tokens on every call for every user.

## Persistence and configuration

Session and agent state live in `hermes_state.py`-managed local storage; configuration
comes from `cli-config.yaml` / environment (`.env.example` documents every variable).
Secrets are never committed. Deployment topologies (local, Docker, SSH, Singularity,
Modal, Daytona) are selected per terminal backend and share the same core.

See `docs/ARCHITECTURE_MAP.md` for the directory-to-responsibility map and the diagram.
