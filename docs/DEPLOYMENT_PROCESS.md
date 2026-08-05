# Deployment Process

Hermes deploys as a user-installed process, not a hosted service. "Deploying" means
getting the CLI and (optionally) the long-running gateway onto a machine — a laptop, a
$5 VPS, a GPU box, or serverless infrastructure — and keeping it running.

## Install paths

| Target | Command |
|--------|---------|
| Linux / macOS / WSL2 / Termux | `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash` |
| Windows (native, PowerShell) | `iex (irm https://hermes-agent.nousresearch.com/install.ps1)` |
| Docker | `docker compose up -d` (see `docker-compose.yml`, `docker/`) |
| Nix | `nix develop` / the flake in `flake.nix` |
| From source | `uv sync && uv run hermes` |

The installer provisions uv, Python 3.11, Node.js, ripgrep and ffmpeg; on Windows it also
unpacks a portable MinGit under `%LOCALAPPDATA%\hermes\git` rather than touching a system
Git install.

## Configure

1. Copy `.env.example` and fill in only what you use — it documents every variable.
   Credentials stay in the environment or the local config; never commit them.
2. `cli-config.yaml.example` is the reference for the full config surface.
3. Pick a model with `hermes model` — no code change, any supported provider.
4. Pair the channels you want (`gateway/pairing.py` drives this from the CLI).

## Run the gateway

```bash
hermes gateway start        # long-running multi-platform process
hermes gateway status       # readiness and channel state
hermes gateway stop         # drains in-flight work before exiting
```

Under Docker, `scripts/hermes-gateway` and the compose file own the lifecycle. The
gateway supports drain control and scale-to-zero, so a serverless or hibernating host
wakes on demand instead of idling at full cost.

## Terminal backends

The agent's execution environment is selected per session: `local`, `docker`, `ssh`,
`singularity`, `modal`, `daytona`. Modal and Daytona hibernate between sessions. Choosing
a backend never changes agent behaviour — that is the point of the single core.

## Upgrade

Re-run the installer, or `uv sync` from source at the new tag. Check
[`../CHANGELOG.md`](../CHANGELOG.md) for the version being installed. Session state is
forward-compatible within a major version.

## Verify after deploying

1. `hermes --version` reports the version you intended.
2. `hermes gateway status` reaches ready with every paired channel connected.
3. Send one message on a real channel and confirm a reply — a started process is not a
   working one.
4. Check the logs for provider auth failures; a bad key surfaces as a silent non-reply.

## Rollback

Reinstall the previous version or pull the previous container tag, then re-run the
verification steps above. See [`../RELEASING.md`](../RELEASING.md) for release mechanics.
