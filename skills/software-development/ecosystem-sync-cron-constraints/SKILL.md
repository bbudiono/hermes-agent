---
name: ecosystem-sync-cron-constraints
description: "Session-shaped learnings from running the daily ecosystem-sync procedure under scheduled-cron constraints. Captures the skill-loader ambiguity, the SKILL.md patch-safety pitfall when bumping the in-repo procedure, and the externally-owned-skill read-only constraint that blocks cron-mode skill edits. Use when running ecosystem-sync as a cron job or diagnosing why the procedure doesn't pick up the in-repo skill."
version: 1.0.0
author: Hermes Agent (cron-session 2026-07-21)
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [ecosystem-sync, cron, skill-loader, patch-safety, session-learnings]
    related_skills: [skill-library-maintenance, macos-cron-pitfalls, ecosystem-sync]
---

# ecosystem-sync — cron-constraints notes (2026-07-21)

Session-shaped learnings captured during the 2026-07-21 daily cron run of the ecosystem-sync procedure. These are NOT a replacement for the canonical in-repo `skills/software-development/ecosystem-sync/SKILL.md` (v1.0.9). They are the operator's view of *why* the procedure had to be executed manually and what blocked the canonical bump.

## 1. Skill-loader ambiguity persists (3-way collision)

Three copies of `SKILL.md` with identical `name: ecosystem-sync` frontmatter exist at:
- `~/.hermes/skills/software-development/ecosystem-sync/SKILL.md` (v3.2.0, 988.5h old)
- `~/.minerva/skills/software-development/ecosystem-sync/SKILL.md` (v1.3.0, 603.5h old) — discovered today, NOT in yesterday's table
- `~/.hermes-shared-skills/software-development/ecosystem-sync/SKILL.md` (4-byte "test" stub, 575.8h old)

Plus a 4th umbrella at `~/.minerva/skills/ecosystem-sync/SKILL.md` (v3.2.0, 319.7h old) using the bare-name frontmatter — making it effectively a 4-way collision.

The in-repo canonical at `/Users/bernhardbudiono/.hermes/hermes-agent/skills/software-development/ecosystem-sync/SKILL.md` (v1.0.8, 71.96h old) is **NOT visible** to the skill loader from cron mode because it lives outside the active profile's indexed skill directories. Symptom: `⚠️ Skill(s) not found and skipped: ecosystem-sync` at cron start.

**Workaround used today:** execute the procedure manually by reading the in-repo SKILL.md with `read_file` (which IS callable from interactive sessions but NOT from cron mode), or via the `terminal` tool with `cat`. From cron mode the only escape hatch is to write a fresh user-owned skill under `~/.athena/skills/` (canonical home) that covers the same territory.

## 2. SKILL.md patch-safety pitfall (long single-quoted YAML strings)

The in-repo ecosystem-sync `SKILL.md` uses single-quoted YAML strings for changelog entries, each 800-2000 chars on one line. When bumping the version with `patch` tool (mode=replace, replace_all=false), the substring match can fail across the boundary between two long entries, leaving the YAML file syntactically broken even though greppable markers still appear intact.

This pitfall is already documented in `skill-library-maintenance` `references/skill-md-patch-safety.md` (see "Local Patch-Tool Failure Mode: Quoted-String YAML Changelog Blocks"). The fix pattern is:
1. Read the file with line numbers first to confirm where each YAML list item starts.
2. Use Python text-replacement (load → split by lines → find line starting with `  - "X.Y.Z ` → replace whole entry → skip continuation lines until next `  - "X.Y.Z `).
3. Verify after edit with `grep -n '^  - "1.3'` and a structural count of `  - "` occurrences.

**Today:** the in-repo bump from v1.0.8 → v1.0.9 was NOT performed because (a) cron mode blocks `patch` and `write_file`, and (b) `skill_manage(name='software-development/ecosystem-sync')` returned "not found in active profile 'default'" since the in-repo skill isn't indexed.

## 3. Externally-owned skills are read-only to autonomous curation

Empirically observed in this cron session: every skill returned by `skills_list(category='software-development')` lives in `~/.hermes-shared-skills/` (the `external_dirs` tree) and is treated as **read-only** by the background curator. Attempting `skill_manage(action='patch')` on any of them returns:

> Refusing background curator patch for skill 'X': the skill lives in skills.external_dirs, which are externally owned and read-only to autonomous curation.

This applies to: `skill-library-maintenance`, `bernhard-ecosystem-onboarding`, `bernhard-ecosystem-deconfliction`, `bernhard-agent-environment-conventions`, `macos-cron-pitfalls`, `ecosystem-skill-publication-guard`, and likely most other class-level umbrellas. Bundled skills (shipped with Hermes) and hub-installed skills are also protected per the standard rule. Pinned skills CAN be improved but only through interactive sessions, not cron mode.

**Practical consequence for cron-mode skill maintenance:** if the durable learning belongs to an externally-owned umbrella (which covers most class-level skills in this ecosystem), the curator cannot patch it from cron. Options:
- Defer the edit to an interactive session.
- Capture the learning in a NEW user-owned skill under `~/.athena/skills/` (the canonical home per `bernhard-agent-environment-conventions`).
- Capture the learning in a session-shaped reference file under an existing user-owned umbrella that IS writable.

## 4. Today-specific durable learnings that DID land

These were captured in Nexus (not in skills) because the canonical umbrella targets are read-only:
- Daily guide ingested to Nexus as `Daily Ecosystem Sync Report 2026-07-21` (id `8fbabe3c-c54d-4001-958f-b9ff05981a8f`).
- 3 Symphony tasks filed: `56326171-...` (P3 cron-store), `05c12700-...` (P3 in-repo skill PR), `37c9fa17-...` (P2 downstream cluster priority bump).
- Local-fallback report at `~/.agents/knowledge/ecosystem-sync/2026-07-21-daily/report.md`.

Carry-over tasks eligible for closure today: `a535e0af`, `68301614`, `aa8c0f3f`, `7180a984` (origin/main inversion resolved — 0/0 parity).

## 5. Recommendations for the next interactive session

1. Bump the in-repo `skills/software-development/ecosystem-sync/SKILL.md` from v1.0.8 → v1.0.9 (or v1.1.0) using the Python text-replacement recipe. Capture the changelog for: cron-store 7th firing, 5th-umbrella discovery, `~/.claude/GEMINI.md` path-bug verification need, origin/main inversion resolution, in-repo skill PR path.
2. File the in-repo skill PR (task `05c12700`) so the canonical procedure is reachable from `main`.
3. Populate or formally retire `~/.hermes-shared-skills/software-development/ecosystem-sync/SKILL.md` (24-day-old stub) and `.../ecosystem-sync-procedure/` (missing entirely).
4. Bump `a5fe8f2d` from P1 to P0 (jobs.json still empty 7+ days; no in-tree cron job is running on this host).
5. Bump `73fd57f1` P3 → P2 and `f5258766` P3 → P2 (downstream cluster at 12.5d, .openclaw/workspace/AGENTS.md at 127.7d).