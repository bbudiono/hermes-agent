# Tailscale SSH + rsync propagation pattern

Use this when propagating user-created skills across reachable macOS and Linux hosts on the Tailscale network.

## Durable workflow

1. Verify the destination host is reachable with non-interactive SSH.
2. Check whether the destination already has the target skill(s) before copying.
3. Create the remote parent directory first when needed:
   - `~/.hermes/skills/creative`
   - or the appropriate category directory for the skill class
4. Prefer a dry run before first write to a host, especially on macOS:
   - `rsync -avn -e 'ssh ...' <src>/ <host>:<dest>/`
5. Copy the skill directory contents with `rsync -a`.
6. Verify not just `SKILL.md` but support files too:
   - `references/...`
   - `templates/...`
   - `scripts/...`
7. Record hosts that were verified, and separately record hosts that were offline or had auth gaps.

## Verified file pattern from this session

For the new video skills, the useful verification set was:
- `gemini-veo-video-generation/SKILL.md`
- `gemini-veo-video-generation/references/api-polling-notes.md`
- `hyperframes-test-render/SKILL.md`
- `remotion-quickstart-render/SKILL.md`
- `remotion-quickstart-render/references/local-validation-notes.md`

## Practical notes

- Linux hosts in this environment used `/home/bernhard-budiono/.hermes/skills/...`
- macOS hosts in this environment used `/Users/bernhardbudiono/.hermes/skills/...`
- Creating the remote category directory before `rsync` avoids receiver-side mkdir failures when the parent tree does not yet exist.
- Permission or key gaps should be recorded as coverage gaps, not treated as successful propagation.
