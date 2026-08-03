---
name: ecosystem-sync
description: "Use when maintaining ecosystem parity across devices and repositories, with Nexus-first knowledge flow, daily sync discipline, and GitHub main updates for shared agent dotfiles."
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
changelog:
  - "1.3.0 (2026-06-05): Documented env-isolated daily-cron procedure; captured bare-`python3` shim issue inside ecosync subprocess calls (recommend `sys.executable` or `env -i`); added generated-surface drift rule confirmation (10d observed on `.gemini/GEMINI.md`)."
  - "1.2.0: Pointer-file resolver, `--full/--git-push` flow, checkpoint/lock clearing, device list."
metadata:
  hermes:
    tags: [ecosystem, sync, nexus, parity, github, macos, dotfiles, operations]
    related_skills: [hermes-agent, writing-plans, team-work-deconfliction]
---

# Ecosystem Sync

Reference addendum:
- `references/claude-continue-sync.md` — canonical `/continue` sync guidance when the source of truth is `~/.claude/skills/continue` rather than a Hermes-local skill copy.

## Operational Runner

The canonical ecosystem-sync tool on Bernhard's Macs is:
```
/usr/bin/python3 ~/.claude/skills/ecosystem-sync/ecosync.py sync --standard --verify-all-devices
```

Interpreter pitfall (cron-critical): some hosts have a broken `python3` shim (sitecustomize/usercustomize import path issues) that raises `InterruptedError` before `pathlib` imports. In that case, use `/usr/bin/python3` explicitly for `ecosync.py`, `compile_provider_configs.py`, and any preflight helper scripts.

Quick probe:
```bash
python3 -c 'import pathlib; print("ok")' || /usr/bin/python3 -c 'import pathlib; print("ok")'
```
If the first command fails but `/usr/bin/python3` succeeds, pin all cron invocations to `/usr/bin/python3`.

⚠️ Some hosts expose `~/.claude/skills/ecosystem-sync` as a **pointer file** (content = canonical path, e.g. `~/.agents/skills/ecosystem-sync`) instead of a directory symlink. In that case, resolve the pointer first and run `<resolved_path>/ecosync.py`.

Example resolver:
```bash
TARGET_POINTER="$HOME/.claude/skills/ecosystem-sync"
if [ -f "$TARGET_POINTER" ] && [ ! -d "$TARGET_POINTER" ]; then
  TARGET="$(cat "$TARGET_POINTER")"
else
  TARGET="$TARGET_POINTER"
fi
python3 "$TARGET/ecosync.py" sync --standard --verify-all-devices
```

**Available flags**: `--standard`, `--full`, `--env`, `--show-divergence`, `--verify-all-devices`.
**Lock file**: `~/.claude/temp/ecosync.lock` — if present and the PID inside is dead, remove it before running.
**Nexus-first**: use `nexus-cli` as the baseline direct-auth surface when MCP is unavailable.

**Checkpoint file (cron-critical)**: `~/.claude/temp/ecosync.checkpoint`. If present, ecosync prompts `Resume from checkpoint?` via `click.confirm`, which can block/fail non-interactive cron jobs. For unattended daily runs, clear stale checkpoint + lock before launch:
```bash
rm -f ~/.claude/temp/ecosync.lock ~/.claude/temp/ecosync.checkpoint
```

**Recommended daily-cron procedure (env-isolated, observed 2026-06-05)**:
The cron-internal interpreter matters: `ecosync.py` itself spawns subprocesses via bare `python3` (e.g. for `tailscale_ips.py`), and on hosts with the broken `sitecustomize` shim each subprocess hangs 15s before failing. With 10 devices that's a 150s no-op tax on every run. The fix in caller-side code: invoke ecosync inside `env -i` with a sanitized PATH so subprocesses inherit the working interpreter:
```bash
env -i HOME="$HOME" PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" \
  /usr/bin/python3 ~/.agents/skills/ecosystem-sync/ecosync.py sync \
  --full --git-push --standard --verify-all-devices
```
The `daily-ecosystem-sync` cron (id `7aff77fe49a4`) already uses this pattern. Recommended upstream fix: patch `ecosync.py` to call subprocesses via `sys.executable` or `shutil.which('python3')` rather than a literal `python3` shebang.

**Generated-surface drift rule (2026-06-05 confirmation)**: `~/.gemini/GEMINI.md` mtime is the highest-signal drift detector. Observed today: 10 days behind `CLAUDE.md`. Cron should compare mtimes nightly and emit a `Symphony` task when any generated surface exceeds the per-surface threshold in the Parity Targets table.

## Known Generated Surface Drift Pattern

**`.gemini/GEMINI.md` is the most drift-prone surface** — it can lag 60+ days behind CLAUDE.md.
- Root cause: it contains hand-authored P0 Critical Rules (SYMPHONY/GPU-GATEWAY mandates, SYNCHRO+ mandates, Claude Code Compatibility) that `compile_provider_configs.py` would overwrite on full regeneration.
- Operators avoid `--all` regeneration because it erases these hand-authored blocks.
- **Mitigation**: always run `compile_provider_configs.py --all --dry-run --diff` first; manually merge P0 blocks back after regeneration.
- **Threshold per SKILL.md drift-suspicion rules**: `.gemini/GEMINI.md` > 48h behind = red flag; > 7 days = active drift to report.
- **Nexus lesson logged**: `gemini-gemini-md-drift-2026-05-28` — confirms 72-day drift event on 2026-05-28.

## Overview

Use this skill to keep the ecosystem aligned across devices, knowledge systems, and repository-backed agent configuration. The default operating mode is **Nexus first**: consult Nexus for lessons learned, guides, SOPs, research, and knowledge graph context before reaching for external web fetch tools.

This skill also defines the minimum recurring sync standard: **run ecosystem sync at least once per day**. At minimum, verify parity on macOS devices and ensure the canonical shared agent artifacts are updated in **GitHub `main`** when changes are intended to become ecosystem defaults.

The goal is to prevent configuration drift across agent surfaces like `.claude`, `.agents`, `.codex`, `.gemini`, and adjacent shared operating files.

## When to Use

Use this when:
- Running `/ecosystem-sync`
- Performing daily ecosystem maintenance
- Checking parity across devices, especially macOS
- Updating shared agent instructions or dotfiles
- Reconciling lessons learned, SOPs, guides, and research findings
- Preparing changes that should become ecosystem-wide defaults in GitHub `main`

Do not skip this when:
- Shared instructions changed in one place but not others
- A device may have drifted from the canonical setup
- Research or lessons learned were generated during work and have not been written back into Nexus
- You are about to rely on web fetch tools without first checking Nexus knowledge sources

## Core Rules

1. **Nexus first.**
   - Check Nexus for lessons learned, guides, SOPs, research, and knowledge graph context before using external web fetch tools.
   - If the required information exists in Nexus, use that as the source of truth first.

2. **Ingest durable knowledge into Nexus.**
   - Put guides, SOPs, lessons learned, and research findings into Nexus.
   - Do not let durable operational knowledge remain trapped in ephemeral chats or local notes.

3. **Run at least daily.**
   - `/ecosystem-sync` must be performed at least once per day.
   - If no explicit schedule exists yet, create one.

4. **Maintain device parity.**
   - At minimum, verify parity on macOS devices.
   - Expand beyond macOS when additional devices are available in scope.
   - Verify the Tailscale control path itself is healthy before assuming propagation is possible.

5. **Keep canonical shared artifacts aligned in GitHub `main`.**
   - When shared defaults change, ensure the ecosystem-facing files are reconciled in the canonical repository and land on `main`.
   - This includes shared agent surfaces such as `.claude`, `.agents`, `.codex`, `.gemini`, skill registries, and similar cross-tool instruction/config files.

6. **Propagate and verify skill changes across devices.**
   - Any created or edited skill must be propagated and verified across all in-scope macOS and Linux devices on the Tailscale network.
   - Verify registry entries and discovery surfaces as part of the propagation, not just the skill files themselves.
   - Prefer careful merges over destructive replacement so no skill is wiped or lost; when variants differ, preserve the best-written/coded version and merge missing value from the others.

7. **Deconflict and plan before substantial changes.**
   - Follow the team deconfliction and planning rules before major sync operations.
   - Verify with other agents through Nexus A2A when the sync impacts shared work.

8. **Maintain this skill.**
   - If the ecosystem sync workflow changes, update this skill immediately.
   - Do not leave this skill stale after discovering new steps, pitfalls, or required artifacts.

9. **7-Agent Pipeline is mandatory pre-work for all non-trivial features.**
   - Before any code is written, planned, or delegated for a feature, the 7-agent pipeline MUST be followed.
   - One agent doing 6 roles = the root cause of broken AI code (source: https://youtube.com/shorts/CVtd7Me_uP4).
   - Pipeline: Researcher (#1) → Story Writer (#2) → Project Manager (#3) [human approval] → Backend (#4) + Frontend (#5) [parallel] → E2E Verifier (#6) → Validator (#7) [gates merge].
   - Researcher (#1) runs first, read-only, before any code or plan is written.
   - Skill reference: `7-agent-pipeline` (software-development/7-agent-pipeline).

## Daily Sync Checklist

Run this checklist each day:

- [ ] Check Nexus first for new lessons learned, guides, SOPs, research, and knowledge graph context
- [ ] Identify new knowledge that should be ingested into Nexus
- [ ] Verify whether shared agent instructions changed anywhere else
- [ ] Compare canonical artifacts for drift: `.claude`, `.agents`, `.codex`, `.gemini`, and related files
- [ ] Verify at least macOS parity
- [ ] Propagate and verify skill files plus skill registry/discovery entries across all in-scope macOS and Linux devices on the Tailscale network
- [ ] Identify any repo changes that should be reflected in GitHub `main`
- [ ] Log Nexus improvement needs as Symphony tasks when discovered
- [ ] Update this skill if the procedure itself changed

## Recommended Workflow

### Step 1: Read Nexus First
- Look for lessons learned
- Check guides and SOPs
- Query Nexus knowledge graphs for related context
- Review stored research before using web fetch tools

### Step 2: Deconflict Scope
- Confirm whether another agent or teammate is already handling the same sync area
- If shared ownership is involved, verify via Nexus A2A

### Step 3: Inspect Canonical Artifacts
Review the ecosystem-controlled files and directories that define agent behavior, including but not limited to:
- `.claude`
- `.agents`
- `.codex`
- `.gemini`
- Other shared instruction/config surfaces that act as ecosystem defaults

### Step 4: Check Device Parity
- Verify that macOS is at parity at minimum
- Propagate skill changes across all in-scope macOS and Linux devices on the Tailscale network
- Create the remote category parent directory before rsync/scp when the target tree may not exist yet
- Prefer `rsync -avn` dry runs before the first write to a host, especially on macOS
- Verify both skill files and registry/discovery surfaces after propagation
- Confirm support files (`references/`, `templates/`, `scripts/`) arrived, not just `SKILL.md`
- When syncing user-owned Claude skills, treat `~/.claude/skills/` as its own surface; do not assume Hermes-native trees (`~/.hermes`, `~/.minerva`) are sufficient
- For the user's canonical `/continue` workflow, use `~/.claude/skills/continue` as the source of truth and sync the full directory tree, not just `SKILL.md`
- Prefer hash verification plus file-count verification when a skill has nested `phases/` or `references/` content
- If multiple variants exist, merge carefully rather than replacing blindly so no skill is lost
- Record drift explicitly rather than assuming it will be remembered

### Step 5: Reconcile to GitHub Main
- If changes should become shared defaults, ensure they are represented in the canonical repository
- Move them through the proper workflow so that `main` reflects the intended ecosystem state
- Do not leave canonical defaults split between local-only state and repo state

### Step 6: Write Learnings Back to Nexus
- Store new lessons learned
- Ingest new SOPs and guides
- Save research findings and useful conclusions
- Update knowledge graph inputs where applicable

### Step 7: Maintain the Procedure
- If a new parity target, artifact class, or sync rule is discovered, patch this skill
- If Nexus needs improvements, log Symphony tasks

## Parity Targets

Minimum required parity target:
- **macOS**

| Common artifact families to verify:
|- Agent instruction surfaces: `.claude`, `.agents`, `.codex`, `.gemini`
|- Shared repo-backed operating conventions
|- Any ecosystem-level bootstrap/config files used across devices or agents
|- Canonical user-owned skills that live outside Hermes-native trees (for this user, `~/.claude/skills/continue` is a required minimum sync target)

### Generated surfaces (compile_provider_configs.py)

The canonical CLAUDE.md generates several derived surfaces. Check each for staleness:
- `~/.claude/AGENTS.md` — generated from CLAUDE.md (auto-generation marker at top)
- `~/.claude/GEMINI.md` — generated from CLAUDE.md
- `~/.claude/.cursorrules` — generated from CLAUDE.md (compact P0 subset)
- `~/.codex/AGENTS.md` — generated from CLAUDE.md
- `~/.gemini/GEMINI.md` — generated from CLAUDE.md (⚠️ most likely to drift)

Regenerate all: `cd ~/.claude && python3 scripts/compile_provider_configs.py --all`

Drift suspicion triggers:
- Any generated surface more than 24h behind CLAUDE.md's mtime
- `.gemini/GEMINI.md` more than 48h behind (most commonly stale surface — 67 days observed in one audit)
- `.codex/AGENTS.md` more than 48h behind

Pitfall: `.gemini/GEMINI.md` may contain hand-authored P0 Critical Rules that the compile script would overwrite. Regeneration is safe but operator should review the diff first with `--dry-run --diff`.

## GitHub Main Policy

Treat GitHub `main` as the canonical published baseline for ecosystem-wide defaults when the change is meant to apply broadly.

Questions to answer during sync:
- Is this change only local, or should it become a shared default?
- If it is shared, has the canonical repo been updated?
- If the repo has been updated, has it actually landed on `main`?
- Are equivalent agent surfaces aligned, or is one tool's instruction file ahead of the others?

## Nexus Knowledge Flow

### Read path
1. Lessons learned in Nexus
2. Guides and SOPs in Nexus
3. Nexus knowledge graph context
4. Nexus-stored research
5. External web fetch tools only after the above is exhausted or insufficient

### Write path
1. New lessons learned
2. New or updated guides/SOPs
3. Research findings and conclusions
4. Cross-links or graph-worthy entities/relationships when applicable

## Supporting References

- `references/dual-skill-surface-propagation.md` — checklist for setups where prompt/snapshot discovery and runtime slash-command discovery read from different local skill trees.
- `references/tailscale-ssh-rsync-propagation.md` — host-by-host propagation workflow over Tailscale SSH/rsync, including prechecks, dry runs, parent-directory creation, and file verification.
- `references/claude-skill-surface-propagation.md` — when a canonical skill lives under `~/.claude/skills/`, including full-tree sync and hash/file-count verification.

## Common Pitfalls

1. **Going to the web first.**
   This bypasses the ecosystem memory. Nexus should be checked before external fetches.

2. **Syncing one surface but not the others.**
   Updating only one skill tree leaves other consumers stale. In some setups, prompt/snapshot discovery and runtime slash-command discovery read from different local homes, so reconcile every active local surface before remote propagation.
   Also do not assume every remote host has the same surface layout: some hosts may only have `~/.hermes`, while others expose both `~/.hermes` and `~/.minerva` with a prompt snapshot.

3. **Assuming local changes are canonical.**
   If a change is supposed to be ecosystem-wide, it must be reconciled into GitHub `main`.

4. **Skipping device parity checks.**
   At minimum, macOS parity must be checked deliberately.

5. **Forgetting to write findings back into Nexus.**
   A sync that reads but does not write back loses much of its value.

6. **Letting the skill go stale.**
   If `/ecosystem-sync` evolves, this skill must evolve with it.

7. **Assuming Tailscale propagation is available just because `tailscale` exists.**
   Validate the control path first. On this macOS host, `/usr/local/bin/tailscale` (the app-bundled symlink) crashes with `Fatal error: The current bundleIdentifier is unknown to the registry`.
   Workaround discovered: the Homebrew CLI at `/opt/homebrew/bin/tailscale` works and can query network state, though it currently warns about a client/server version mismatch (`1.94.2` client vs `1.96.5` server/app).

## Verification Checklist

- [ ] Nexus was consulted before external web fetch tools
- [ ] New guides, SOPs, lessons learned, and research findings were ingested back into Nexus
- [ ] `/ecosystem-sync` is scheduled to run at least daily
- [ ] macOS parity was checked at minimum
- [ ] Shared agent files such as `.claude`, `.agents`, `.codex`, and `.gemini` were reviewed for drift
- [ ] Canonical ecosystem changes intended for everyone were reconciled to GitHub `main`
- [ ] Any Nexus improvements were logged as Symphony tasks
- [ ] This skill was updated if the workflow changed

## One-Shot Recipe

Use this operating summary:

1. Check Nexus first
2. Deconflict with A2A if shared scope is involved
3. Inspect shared agent surfaces for drift
4. Verify macOS parity at minimum
5. Reconcile intended shared defaults to GitHub `main`
6. Write learnings and research back into Nexus
7. Patch this skill if the procedure changed
