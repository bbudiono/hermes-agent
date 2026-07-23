---
name: execution-preflight-governance
description: Use when starting any non-trivial feature, bugfix, or multi-agent task in a shared repo or ecosystem surface. Enforces deconfliction, registered planning, A2A verification, Symphony follow-up for Nexus gaps, and isolated worktrees for large features.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [preflight, deconfliction, planning, a2a, symphony, worktree, governance]
    related_skills: [plan-quality-mode, isolated-git-worktree-sop, operator-coordination-surfaces, markdown-plan-governance]
---

# Execution Preflight Governance

## Overview
This skill is the mandatory preflight for non-trivial work in Bernhard's ecosystem.

The job does not start just because someone has an idea or a backlog item. Before implementation begins, the assigned agent must deconflict scope, create a registered plan that passes the required template/gate, verify ownership and blockers with other agents through Nexus A2A, log Nexus product gaps as Symphony tasks, and use an isolated git worktree for large features.

If those gates are not satisfied, the correct action is to stop and fix the preconditions instead of starting anyway.

## When to Use
Use this skill when:
- starting a feature, bugfix, refactor, migration, deploy track, or automation task with more than trivial scope
- multiple agents may touch the same repo, service, UI, API, doc set, or operational surface
- work involves Nexus, Symphony, A2A, or any shared coordination path
- a task could create file ownership collisions or duplicate implementation
- a large feature needs a fresh branch/worktree before coding

Do not use this skill for:
- tiny single-file edits with no overlap risk and no shared-surface impact
- pure read-only reconnaissance with no intent to execute changes yet

## Core Rules
1. **Always deconflict work before execution.**
2. **Always have a plan.** The plan must be saved in the canonical location, registered properly in the workflow, and follow the required template/validator gate.
3. **Always verify with other agents using Nexus A2A.** Do not assume ownership alignment silently.
4. **If Nexus needs improvement, log it as a Symphony task.** Product debt discovered during execution is not a reason to hand-wave the issue away.
5. **If there is no plan, do not start.**
6. **If a large feature does not have an isolated worktree, do not start.**

## Mandatory Preflight Checklist
Before execution, confirm all of the following:
- [ ] Scope is defined clearly enough to separate in-scope vs out-of-scope work.
- [ ] File/service/surface ownership is deconflicted across agents.
- [ ] The task has an active plan in the canonical plans location.
- [ ] The plan follows the required template and passes the plan-quality gate.
- [ ] A2A verification has happened in Nexus with relevant agents.
- [ ] Blockers, dependencies, and overlaps are documented explicitly.
- [ ] Large-feature work has a fresh isolated git worktree.
- [ ] Any Nexus/Symphony/A2A product gap discovered has a Symphony task logged.

## Standard Workflow
### 1. Deconflict first
- Identify the exact repo, branch lane, files, services, dashboards, docs, jobs, and APIs that may be touched.
- Identify which other agents could reasonably touch the same surfaces.
- Produce explicit ownership boundaries: who owns what, what is shared, and what is blocked.
- If overlap exists, resolve it before coding.

### 2. Create the plan before implementation
- Write the plan in the canonical plans location.
- Use the required template and quality gate from `plan-quality-mode`.
- Treat a missing or invalid plan as a hard blocker.
- If the plan is cross-agent, include the deconfliction and sync contract inside the plan.

### 3. Verify through Nexus A2A
- Post the ownership/scope check in Nexus A2A.
- Ask for confirmation from affected agents when overlap, dependency, or review coupling exists.
- Use A2A for deconfliction, blocker resolution, and execution alignment.
- Telegram is visibility only; agent coordination lives in Nexus A2A.

### 4. Create Symphony follow-up for Nexus gaps
When you discover missing functionality in Nexus, Symphony, or A2A:
- log a Symphony task for the improvement
- describe the observed gap, why it blocks or weakens the workflow, and the expected behavior
- link it from the active plan or execution notes when relevant

### 5. Use isolated worktrees for large features
A large feature must not start in a dirty or shared checkout.
Required pattern:
1. `git fetch origin --prune`
2. create a dedicated worktree from the correct base
3. do implementation only inside that worktree
4. verify the worktree is clean and on the intended ref before coding

## What Counts as a Large Feature
Treat the task as a large feature if any of these are true:
- touches multiple files or directories with behavioral coupling
- changes shared contracts, workflows, data flow, or coordination surfaces
- spans multiple agents or repos
- introduces new dependencies or deployment risk
- requires a formal plan to reason about safely

When in doubt, classify upward and use a worktree.

## Failure Conditions
Stop execution immediately if:
- there is no plan
- the plan fails the quality gate
- ownership is ambiguous
- another agent may already be working the same surface and A2A has not resolved it
- the feature is large and no isolated worktree exists
- you found a Nexus/Symphony gap that must be tracked and have not logged it yet

## Evidence to Capture
Keep evidence lightweight but explicit:
- plan path
- validator result
- worktree path and base ref
- Nexus A2A thread/message IDs used for deconfliction
- Symphony task ID for any Nexus improvement logged
- named blockers and owners

## Common Pitfalls
1. **Starting because the task feels obvious.** Shared ecosystems produce collision risk even when the coding path seems clear.
2. **Treating Telegram as coordination.** It is not the canonical A2A lane.
3. **Writing a plan that exists but does not pass the gate.** Invalid plans do not satisfy the preflight.
4. **Using the main checkout for a large feature.** That invites drift, overlap, and bad provenance.
5. **Seeing Nexus friction and not logging it.** If the platform is missing a required behavior, capture it in Symphony.
6. **Assuming silence means agreement.** Deconfliction requires explicit verification where overlap is plausible.

## Verification Checklist
- [ ] I can point to the exact plan file.
- [ ] The plan uses the required template and passed validation.
- [ ] I know which agents were checked with in Nexus A2A.
- [ ] I have explicit ownership boundaries for overlapping surfaces.
- [ ] The worktree exists for large-feature work and is clean.
- [ ] Any Nexus improvement need was logged to Symphony.
- [ ] Implementation has not started before all of the above are true.
