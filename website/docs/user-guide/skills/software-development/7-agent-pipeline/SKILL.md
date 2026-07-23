---
name: 7-agent-pipeline
description: "MANDATORY 7-agent collaborative pipeline for all non-trivial feature work: Researcher → Story Writer → Project Manager → Backend/Frontend (parallel) → E2E Verifier → Validator. Source: https://youtube.com/shorts/CVtd7Me_uP4"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
triggers:
  - user asks to build a feature, implement something, or write code
  - non-trivial task requiring planning and delegation
  - any task where AI coding is involved
---

# 7-Agent Collaborative Pipeline

**Core insight:** One AI agent doing 6 roles at once (analyst + architect + backend + frontend + tester + reviewer) causes wrong assumptions to cascade and spread before you notice. The fix is a strict 7-agent pipeline.

**Video source:** ["The Exact Setup to Ship Features Reliably"](https://youtube.com/shorts/CVtd7Me_uP4)

## The 7 Agents

| # | Agent | Read/Write | Role | Output |
|---|-------|-----------|------|--------|
| 1 | **Researcher** | Read-only | Maps entire codebase, finds existing patterns, similar features, risks. Works BEFORE any code is planned. | Research brief |
| 2 | **Story Writer** | Write | Turns rough idea into user story with acceptance criteria + edge cases | User story |
| 3 | **Project Manager** | Write | Turns story into full technical blueprint: data model, API shapes, file changes, migrations | Technical blueprint |
| 4 | **Backend Engineer** | Write | Builds API/services/DB changes + unit tests. Back-end folders ONLY. | Backend implementation |
| 5 | **Frontend Engineer** | Write | Reads backend output, builds matching UI. Frontend folders ONLY. **Parallel with #4.** | Frontend implementation |
| 6 | **E2E Test Verifier** | Write | End-to-end flow tests from user perspective. Not unit tests. | Test suite |
| 7 | **Validator** | Read-only | Reads original story + spec + built code. Reports gaps, security issues, skipped items. **Gates merge.** | Validation report |

## Pipeline Rules

1. **Researcher (#1) ALWAYS runs first.** No code, no plan, no blueprint until research brief is done.
2. **Story Writer (#2) produces user story BEFORE Project Manager (#3) touches anything.**
3. **Backend (#4) and Frontend (#5) run in parallel** after blueprint (#3) is human-approved.
4. **Validator (#7) gates merge.** No PR merged without a validation report.
5. **One agent doing all 6 roles = REFUSED.** When reviewing AI-coded PRs, reject if the agent that wrote the code also reviewed it.

## When to Apply

- **Every non-trivial feature** (anything involving 2+ files, new APIs, new data models)
- **Trivial tasks** (single file, known pattern, <30 min): Researcher brief may be skipped, but all other agents still apply
- **Bug fixes**: Researcher maps the bug's area first, then fix + E2E test + Validator sign-off

## How to Run Each Agent

### Researcher (#1)
```
delegate_task(goal="Map the codebase area for [feature]. Find: existing patterns, similar features, potential risks, relevant files. Be read-only — do not write any code.", role="leaf")
```
Key constraint: **read-only**. Spawn as a separate subagent with no write permissions.

### Story Writer (#2)
Spawn a subagent with the research brief as input. Ask for: user story format, acceptance criteria, edge cases.

### Project Manager (#3)
Spawn a subagent with the user story as input. Ask for: complete technical blueprint with exact file paths, data model changes, API shapes, migrations.

### Backend (#4)
Spawn backend engineer subagent with blueprint. Constrain to backend folders only.

### Frontend (#5)
Spawn frontend engineer subagent with blueprint + backend output. Constrain to frontend folders only. Runs **parallel with #4**.

### E2E Test Verifier (#6)
After #4 and #5 are complete. Spawn subagent to write end-to-end flow tests from user perspective.

### Validator (#7)
After #6 passes. Read-only review of: original story + spec + all code. Report gaps, security issues, skipped items.

## Skill Integration

- Researcher → `delegate_task` as read-only leaf agent
- Story Writer → `plan` skill (user story output format)
- Project Manager → `plan` skill (technical blueprint output)
- Backend/Frontend → `subagent-driven-development` skill (delegate_task with two-stage review)
- E2E Test Verifier → `test-driven-development` skill
- Validator → `requesting-code-review` skill

## Red Flags (Reject the PR/Plan)

- [ ] Same agent wrote code AND reviewed it
- [ ] No research brief before the plan
- [ ] No user story with acceptance criteria
- [ ] Backend and frontend done by one agent without parallel review
- [ ] No E2E tests (only unit tests)
- [ ] No validator sign-off before merge

## Quick Reference

```
1. RESEARCHER  → research brief
2. STORY WRITER → user story + acceptance criteria
3. PROJECT MANAGER → technical blueprint (APPROVED by human)
4+5. BACKEND + FRONTEND → parallel implementation
6. E2E VERIFIER → test suite
7. VALIDATOR → validation report (GATES MERGE)
```
