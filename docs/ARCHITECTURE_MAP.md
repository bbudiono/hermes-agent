# Architecture Map

Directory-to-responsibility map for the repository. Companion to
[ARCHITECTURE.md](ARCHITECTURE.md).

## Diagram

- Source: [`diagrams/architecture.excalidraw`](diagrams/architecture.excalidraw)
- Export: [`diagrams/architecture.html`](diagrams/architecture.html) (self-contained,
  no external CDN — open it directly in a browser)

Regenerate the export after editing the source:

```bash
python3 ~/.agents/skills/creative/excalidraw/scripts/export_html.py \
  docs/diagrams/architecture.excalidraw docs/diagrams/architecture.html
```

## Top-level map

| Path | Responsibility |
|------|----------------|
| `agent/` | Agent core: turn loop, provider adapters, context assembly, delegation |
| `providers/` | Per-provider shims over a common base; provider neutrality lives here |
| `tools/` | Implementations behind the model-visible tool schema |
| `model_tools.py`, `toolsets.py`, `toolset_distributions.py` | The tool schema itself and how it is bundled per surface |
| `hermes_state.py` | Session/agent persistence |
| `trajectory_compressor.py` | Context compression — the one sanctioned cache-invalidating path |
| `hermes_cli/` | `hermes` CLI: setup, auth, model switch, gateway control, backup |
| `gateway/` | Long-running multi-platform process (see below) |
| `tui_gateway/` | Terminal UI host, compute host, event publisher |
| `acp_adapter/` | Agent Client Protocol adapter for editors, with its own approval model |
| `apps/desktop`, `apps/shared`, `web/` | Electron desktop shell and web frontend |
| `cron/` | Scheduler, jobs, executions, lifecycle guard |
| `skills/`, `optional-skills/` | Agent skills (agentskills.io layout) |
| `plugins/`, `optional-mcps/` | Plugin and MCP extension points |
| `locales/` | i18n catalogues (shipped as wheel data-files) |
| `website/` | Docusaurus documentation site |
| `packaging/`, `docker/`, `nix/`, `scripts/install.*` | Distribution and installers |
| `tests/`, `tests-js/` | Python and JavaScript test suites |
| `scripts/` | Developer and CI utilities |

## Inside `gateway/`

| Path | Responsibility |
|------|----------------|
| `run.py` | Gateway main loop |
| `session.py`, `session_context.py` | Per-conversation state and context |
| `platforms/` | ~20 channel adapters (Telegram, Discord, Slack, Signal, WhatsApp, …) |
| `relay/` | Remote relay connector |
| `slash_commands.py`, `slash_access.py` | Command surface and access control |
| `delivery.py`, `delivery_ledger.py` | Outbound delivery and idempotency |
| `authz_mixin.py`, `pairing.py` | Authorisation and device pairing |
| `drain_control.py`, `scale_to_zero.py`, `shutdown_watchdog.py` | Lifecycle, hibernation, safe shutdown |
| `builtin_hooks/` | Hooks fired at defined gateway lifecycle points |

## Cross-cutting docs

`docs/security/`, `docs/observability/`, `docs/middleware/`, `docs/design/`,
`docs/kanban/` hold subsystem detail; `docs/INDEX.md` lists the full canonical set.
