# Claude skill surface propagation

Use this when the canonical artifact to sync lives under `~/.claude/skills/` rather than Hermes-native skill trees.

## Durable rule from this session
For this user, the canonical `/continue` skill lives at:
- `~/.claude/skills/continue`

Do not substitute a Hermes-native `continue` skill when the request is to synchronize the user's real `/continue` skill.

## Recommended verification pattern
1. Verify the canonical local path exists.
2. Sync the full directory tree, not just `SKILL.md`.
3. Verify `SKILL.md` hash matches on each target host.
4. Verify file count for the whole skill tree when the skill contains nested content such as:
   - `phases/`
   - `references/`
5. Record any host that had a different pre-sync hash as drift that was corrected.

## Why this matters
A skill can look present while still being incomplete or stale if only `SKILL.md` was copied. Hash + file-count verification catches missing support files and partially updated trees.
