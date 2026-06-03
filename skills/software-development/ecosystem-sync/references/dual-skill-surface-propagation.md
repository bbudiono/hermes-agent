# Dual skill-surface propagation notes

Use this when a host resolves skill state from more than one local surface.

## Durable pattern

Some user setups split skill consumption across:
- a prompt-builder / snapshot surface (for example `~/.minerva/skills` plus `.skills_prompt_snapshot.json`)
- a runtime slash-command surface (for example `~/.hermes/skills`)

Do not assume editing one tree updates the other.

## Safe propagation workflow

1. Identify the actual local read paths for:
   - prompt/snapshot skill discovery
   - runtime slash-command / skill reload discovery
2. Promote new or edited skills into every active local surface before remote propagation.
3. Prefer `rsync -avn` dry runs first, especially to Linux hosts, to verify directory creation and file lists without overwriting anything.
4. Ensure the remote parent directories exist before live transfer (for example `mkdir -p ~/.hermes/skills/creative`) because first-time skill propagation may fail even when `~/.hermes/skills` already exists.
5. After promotion/copy, verify:
   - `SKILL.md` exists
   - any `references/`, `templates/`, or `scripts/` files also arrived
   - the destination surface can discover the skill after reload/snapshot refresh
   - a host-specific `find ~/.hermes/skills/<category>/<skill> -maxdepth 2 -type f | sort` check matches the expected file list
6. Preserve and merge; do not replace blindly when the destination may contain a better or newer variant.

## Remote copy recipe

Use this pattern when propagating a new skill to remote Hermes installations:

1. Check whether the remote skill already exists.
2. Create the category parent directory on the remote host if needed.
3. Dry-run with `rsync -avn -e 'ssh ...'`.
4. Run the real `rsync -a -e 'ssh ...'` copy.
5. Verify with a remote `find` listing that includes support files under `references/`.

This session validated the recipe on Linux and macOS hosts using the runtime surface `~/.hermes/skills`.

## What to record back into the umbrella

If this pattern appears, add a pitfall to the main skill reminding future agents that local skill state may be split across multiple homes and both must be reconciled before claiming propagation is complete.
