---
name: deconflicted-plan-first-execution
description: Use when starting multi-agent or large-feature work that must be deconflicted, planned, registered, coordinated via Nexus A2A, and isolated in a dedicated git worktree before execution.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, deconfliction, a2a, symphony, worktrees, nexus, execution-discipline]
    related_skills: [writing-plans, multi-agent-ecosystem-coordination, isolated-git-worktree-sop]
---

# Deconflicted Plan-First Execution

## Overview

Use this skill as the default execution gate for substantial work in Bernhard's ecosystem. Before implementation starts, work must be deconflicted with other agents, anchored in a proper registered plan using the required template, coordinated through Nexus A2A, and isolated in a dedicated git worktree when the scope is large enough to justify one.

This skill exists to stop unplanned collisions, undocumented execution, and repo contamination. If Nexus is missing workflow support needed to do this correctly, log the gap as a Symphony task rather than inventing an off-book workaround.

## When to Use

Use this skill when:
- starting a large feature, refactor, integration, migration, or multi-step fix
- more than one agent may touch the same repo, task, or execution surface
- the work needs a formal plan, deconfliction, or work ownership clarity
- the work will span enough files/risk that an isolated worktree is the safe default
- Nexus workflow gaps are discovered during execution planning

Do not use this skill for:
- trivial one-file edits with no overlap risk
- pure read-only inspection or short answers with no execution
- tasks the user explicitly says to do immediately without the normal planning lane

## Core Rules

1. **Always deconflict work first.** Confirm overlap, ownership, and boundaries before editing.
2. **Always have a proper plan.** The plan must use the required template, be saved in the required location, and be registered where the ecosystem expects it.
3. **Always verify with other agents via Nexus A2A.** Team coordination belongs in A2A, not ad hoc Telegram chatter.
4. **If Nexus needs improvements, log them as Symphony tasks.** Missing workflow support is product work, not a reason to skip the workflow.
5. **If there is no plan, do not start.**
6. **If large-feature work lacks an isolated worktree, do not start.**

## Standard Workflow

### 1. Deconfliction preflight
- identify the repo, task, owning agent, and likely overlap surfaces
- check whether another agent is already working the same lane
- state file/surface ownership clearly before implementation
- use Nexus A2A to verify alignment with the team

### 2. Plan gate
- read the active plan rules before drafting
- write the plan using the required ecosystem template
- save it in the canonical plan location(s)
- make ownership, non-goals, verification, and overlap risks explicit
- register or surface the saved plan where the workflow expects it

### 3. A2A confirmation
- post the execution intent, ownership, and overlap boundaries in Nexus A2A
- confirm the plan is the active source of truth for the work
- resolve conflicts before code changes begin

### 4. Worktree gate for large features
- create a dedicated isolated git worktree for the effort
- name it clearly for the feature/task
- verify the worktree points at the correct base branch/ref
- run implementation, tests, and reviews from the worktree, not the shared checkout

### 5. Nexus improvement capture
If the correct workflow cannot be completed because Nexus lacks a needed capability:
- document the exact missing capability
- log it as a Symphony task
- link the missing capability to the blocked or degraded workflow
- proceed only within safe policy boundaries

## Minimum Checklist Before Execution

- [ ] Work is deconflicted
- [ ] Ownership is clear
- [ ] Plan exists and follows the required template
- [ ] Plan is saved/registered in the canonical location
- [ ] Other agents were checked via Nexus A2A
- [ ] Large-feature work has a dedicated isolated worktree
- [ ] Any Nexus workflow gaps were logged as Symphony tasks

## Common Pitfalls

1. Writing a plan in chat instead of a real plan file.
2. Assuming no overlap because nobody complained yet.
3. Using Telegram as the main coordination surface instead of Nexus A2A.
4. Starting from the shared checkout because creating a worktree feels slower.
5. Discovering a Nexus gap and patching around it locally without logging a Symphony task.
6. Treating "small for me" as "small enough to skip the plan gate" when the blast radius is actually multi-agent or multi-file.

## Verification Checklist

- [ ] A saved plan path exists and uses the mandated template
- [ ] A2A contains the deconfliction/ownership check
- [ ] The repo work is happening from the intended isolated worktree when required
- [ ] Any discovered Nexus workflow deficiency has a corresponding Symphony task
- [ ] Execution did not begin before the gates above were satisfied
