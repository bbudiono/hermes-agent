---
name: ecosystem-skill-publication-guard
description: Use after creating, installing, or editing a skill. Reconciles skill publication into the canonical ~/.agents tree, registers it, mirrors provider copies, runs ecosystem sync, and verifies no duplicate drift remains.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, ecosystem-sync, hooks, registries, propagation, canonicalization]
    related_skills: [ecosystem-sync, ecosystem-hooks, hermes-agent-skill-authoring, skill-library-maintenance]
---

# Ecosystem Skill Publication Guard

## Overview

This skill captures Bernhard's required model for creating or modifying skills in the shared agent ecosystem: **one canonical source, generated or symlinked mirrors, no independent duplicates, and verification after propagation**.

It exists because simply creating a local `SKILL.md` is not enough. A skill is not live until it is canonicalized under `~/.agents/skills/`, registered, mirrored where provider surfaces need it, synced across reachable devices, and verified by content checks.

A companion post-tool hook, `skill_creation_ecosystem_reconciler.py`, fires after skill creation/edit tools and writes a pending reconciliation receipt under `~/.agents/state/skill_creation_ecosystem_reconciler/pending/`. The hook is advisory and lightweight; the agent must then complete the heavier sync/verification workflow from this skill.

## When to Use

Use this skill whenever any agent:

- creates a new skill
- installs a skill
- edits or patches an existing skill
- writes a `SKILL.md` under any provider/agent home
- modifies skill registries
- migrates a user-local skill into the shared ecosystem
- says "skill created", "skill updated", "skill live", or "skill synced"

Do **not** use this for one-off notes, memories, temporary plans, or repository-local docs that are not reusable skills.

## Canonical Model

Correct sync is **not** "copy one new skill into 3 places" and not "duplicate everything everywhere." Correct sync is:

1. **One canonical source** per skill:
   - default: `~/.agents/skills/<category>/<skill-name>/SKILL.md`
   - user-local experiments only: `~/.hermes/skills/...`
   - package-shipped Hermes skills only when explicitly requested: `~/.hermes/hermes-agent/skills/...`
2. **Generated or symlinked mirrors** for provider surfaces:
   - `~/.claude/skills/...`
   - `~/.gemini/skills/...`
   - `~/.codex/skills/...`
   - `~/.kimi/skills/...`
   - other live homes only when needed
3. **Registries match disk**:
   - `~/.agents/registries/skills.md`
   - `~/.claude/registry_skills.md`
4. **Two-way sync means reconcile first, then publish**:
   - scan canonical homes
   - detect drift/stale duplicates/provider-only edits
   - promote intentional edits into `~/.agents`
   - replace stale provider copies with mirrors or generated shims
   - publish from canonical to targets
5. **Verification must check content**, not just command exit status.

## Canonical Homes in Scope

Scan these homes for skill drift:

- `~/.hermes`
- `~/.mercury`
- `~/.minerva`
- `~/.athena`
- `~/.openclaw`
- `~/.nano`
- `~/.claude`
- `~/.agents`
- `~/.gemini`
- `~/.kimi`
- `~/.codex`
- `~/.antigravity`
- `~/.antigravitycli`
- `~/.cursor`
- `~/.kilocode`

Excluded invalid/guessed paths: `~/.agy`, `~/.glm`, `~/.minimax`, `~/.antigravity-ide`, `/.anything`, duplicate `~/.openclaw` paths.

## Workflow

### 1. Identify the skill event

If the hook fired, inspect pending receipts:

```bash
find ~/.agents/state/skill_creation_ecosystem_reconciler/pending -type f -name '*.json' -maxdepth 1
```

Each receipt includes:

- tool name
- detected action (`skill_manage_create`, `skill_file_write`, `skill_shell_command`, etc.)
- affected path if detectable
- timestamp
- required next steps

### 2. Canonicalize

For shared skills, ensure the skill lives at:

```bash
~/.agents/skills/<category>/<skill-name>/SKILL.md
```

If the skill was created under a provider/local path, promote it into `~/.agents/skills/` and leave the provider copy as a mirror or generated shim only.

### 3. Register

Add or update entries in both registries:

```bash
~/.agents/registries/skills.md
~/.claude/registry_skills.md
```

Minimum registry fields:

- name
- canonical path
- description
- triggers
- complexity
- state
- date added or updated

### 4. Mirror provider surfaces

Provider surfaces should resolve to canonical content. Prefer symlinks where safe; otherwise use generated copies. Avoid self-referential symlink loops.

Local mirror targets to check:

```bash
~/.claude/skills/
~/.gemini/skills/
~/.codex/skills/
~/.kimi/skills/
~/.hermes/skills/
```

### 5. Run ecosystem sync

Use the canonical ecosync script from `~/.agents`:

```bash
python3 ~/.agents/skills/ecosystem-sync/ecosync.py sync   --category agents_skills,agents_registries,registries   --no-git-push   --preflight auto   --skip-audit
```

Do not use `env -i` on macOS. It breaks Tailscale.

### 6. Verify content on reachable hosts

At minimum verify each reachable macOS/Linux host reports:

- canonical `SKILL.md` exists
- registry contains the skill entry
- provider mirror/symlink resolves if the provider home exists
- content marker or checksum matches source

A successful `rsync` or `scp` is not evidence. SSH back and check files.

### 7. Close hook receipt

After verification, move the pending receipt to `done/` and include verification details:

```bash
mkdir -p ~/.agents/state/skill_creation_ecosystem_reconciler/done
mv ~/.agents/state/skill_creation_ecosystem_reconciler/pending/<receipt>.json    ~/.agents/state/skill_creation_ecosystem_reconciler/done/
```

If a target is unreachable, keep the receipt pending or move it to `blocked/` with a blocker note. Do not call the skill fully propagated.

## Hook Contract

Hook file:

```bash
~/.agents/hooks/post-tool-use/skill_creation_ecosystem_reconciler.py
~/.claude/hooks/post-tool-use/skill_creation_ecosystem_reconciler.py
```

It fires on post-tool events matching skill creation/edit patterns:

- `skill_manage` with `action=create|edit|patch|write_file`
- `write_file`, `Write`, `Edit`, `MultiEdit`, or `patch` touching `SKILL.md` under a skills directory
- shell commands that mention `SKILL.md`, `hermes skills install`, or `skills add`

The hook is deliberately lightweight. It does not run full fleet sync inside the hook timeout. It records a receipt and emits an advisory telling the agent to run this skill's workflow.

## Common Pitfalls

1. **Calling a local skill creation done** — a skill under `~/.hermes/skills/` is not ecosystem-live.
2. **Registry drift** — a skill can exist on disk but remain invisible if registries are stale.
3. **Blind rsync** — copying provider directories can create stale independent copies instead of mirrors.
4. **No content verification** — command success is not proof the remote has the right skill.
5. **Symlink loops** — compare resolved paths before linking provider mirrors.
6. **Heavy work inside hooks** — post-tool hooks should write receipts and advisory messages, not long-running fleet syncs.
7. **Synology/Windows false confidence** — some targets may fail SSH or lack Unix tools; report them separately.

## Verification Checklist

- [ ] Skill exists under `~/.agents/skills/<category>/<name>/SKILL.md`
- [ ] `SKILL.md` frontmatter has `name` and `description`
- [ ] `~/.agents/registries/skills.md` contains the skill
- [ ] `~/.claude/registry_skills.md` contains the skill
- [ ] Hook file exists under `~/.agents/hooks/post-tool-use/`
- [ ] Hook mirror exists under `~/.claude/hooks/post-tool-use/`
- [ ] `~/.claude/settings.json` registers the hook under `PostToolUse`
- [ ] `~/.agents/hooks/hooks_registry.json` registers the hook
- [ ] Hook smoke test creates a pending receipt for a fake skill write
- [ ] Ecosystem sync ran or blockers are explicitly recorded
- [ ] Pending receipt moved to done/blocked only after verification
