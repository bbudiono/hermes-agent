---
name: isolated-git-worktree-sop
description: Use isolated git worktrees as the default SOP for reviews, deploys, hotfixes, and automation when the main checkout is dirty or shared.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Isolated Git Worktree SOP

## When to use
Use this SOP whenever:
1. The primary checkout has unrelated local changes
2. Multiple agents may touch the same repo
3. Reviewing a PR without disturbing current work
4. Preparing a deploy from a known clean commit
5. Running risky automation, builds, migrations, or release validation

## Core rule
Never reuse a dirty/shared primary checkout for review or deployment work when a clean worktree can isolate the task.

## Standard procedure
1. Capture context first:
   - current branch
   - `git status --short`
   - target ref/PR/commit
2. Fetch the latest remote refs:
   - `git fetch origin --prune`
3. Create a dedicated worktree from the exact target ref:
   - PR review: `git worktree add <path> <pr-branch-or-fetch-head>`
   - deploy: `git worktree add <path> origin/master`
   - hotfix: `git worktree add <path> <release-tag-or-commit>`
4. Run build/test/review/deploy only from that worktree
5. Keep the main checkout untouched unless the task explicitly targets it
6. Remove the worktree after the task if it is no longer needed:
   - `git worktree remove <path> --force`

## Path conventions
- Prefer a dedicated temp/build area such as `~/Temp/Builds/` for deploy worktrees
- Use clearly named directories containing the repo + purpose + ref, e.g.:
  - `~/Temp/Builds/repo_nexus-deploy-<sha>`
  - `/tmp/repo_nexus-pr<id>`

## Deployment usage
For deploys:
1. Create a clean worktree from the exact production candidate commit
2. Build from the worktree, not the primary checkout
3. Deploy from the worktree
4. Validate the deployed version against the intended SHA/release

## Review usage
For PR review:
1. Fetch PR branch
2. Create/check out an isolated worktree
3. Inspect diffs, run tests, and reproduce failures there
4. Comment with exact commit/SHA evidence

## Why this is the SOP
- Prevents clobbering unrelated local work
- Avoids cross-agent collisions
- Makes deploy provenance explicit
- Keeps review and release validation reproducible
- Reduces accidental drift between what was reviewed and what was shipped

## Pitfalls
- Do not assume the main checkout is safe if `git status` is dirty
- Do not deploy from a branch with unpublished local modifications unless that is explicitly intended
- Do not forget to verify the worktree points at the intended commit/SHA before building or deploying

## Verification checklist
Before acting from a worktree, verify:
- `git rev-parse --short HEAD`
- `git status --short` is clean in the worktree
- target branch/commit/PR matches the intended release or review target
- build/test/deploy commands are being run from the worktree path, not the primary checkout
