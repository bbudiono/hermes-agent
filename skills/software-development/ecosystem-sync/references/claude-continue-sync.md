# Canonical `/continue` sync notes

Use this when the user refers to the `/continue` skill specifically, especially across multiple devices.

## Durable rule

The canonical `/continue` skill may live under:

- `~/.claude/skills/continue`

Do not assume the Hermes-side `continue` skill is the source of truth.

## Sync procedure

1. Treat `~/.claude/skills/continue` as the authoritative source when the user says `/continue`.
2. Sync the entire directory, not just `SKILL.md`.
3. Create the remote parent directory first:
   - `~/.claude/skills/`
4. Copy the full tree to:
   - `~/.claude/skills/continue/`
5. Verify using at least one content check, not only copy success:
   - hash of `SKILL.md`
   - total file count in the directory
6. Keep Hermes-local `continue` artifacts separate unless the user explicitly wants reconciliation.

## Why this matters

The Claude `continue` skill can contain many support files (`phases/`, `references/`, etc.). A shallow sync of only `SKILL.md` silently leaves devices inconsistent.

## Session-proven verification pattern

- Compare `shasum -a 256 ~/.claude/skills/continue/SKILL.md`
- Compare `find ~/.claude/skills/continue -maxdepth 2 -type f | wc -l`

This caught drift on at least one reachable host and confirmed full parity after sync.
