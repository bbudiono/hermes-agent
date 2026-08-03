---
name: agent-cli-plan-validation
description: Use when creating, validating, changing, or closing plans. Invoke Claude Opus and Gemini CLI/TUI critique before Hermes main-agent synthesis, with GLM/MiniMax/Kimi support and the mandatory closure codebase review gate.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, validation, agents, cli, tui, code-review, closure]
    related_skills: [plan-quality-mode, plan-closure-review-gate, isolated-git-worktree-sop]
---

# Agent CLI Plan Validation

## Overview

This skill turns multi-agent support into a routine part of planning and plan completion. Hermes should not rely only on its own judgment for substantive plans: it should invoke additional agents through their CLI/TUI surfaces, collect critique, and synthesize the final plan only after external validation.

Default validation agents:
- `claude` using Opus when available (`claude --model opus` in interactive/PTY mode)
- `gemini`
- `glm`
- `minimax`
- `kimi`

Claude Opus and Gemini are the first-line validators for plans and should be invoked before main-agent synthesis. GLM, MiniMax, and Kimi are additional reviewers for high-risk, ambiguous, or architecture-heavy work.

Important Claude constraint: use Claude through the `claude` CLI/TUI only. Do **not** use `claude -p`, `claude --print`, the Anthropic Agents SDK, or direct Anthropic API/SDK patterns unless Bernhard explicitly re-authorises them.

## When to Use

Use this skill routinely when:
- writing a new implementation plan
- changing a plan after new constraints appear
- validating a plan before execution
- evaluating a risky feature, deploy, migration, auth, SSO, data, or production change
- a plan is about to move to closed/completed/archived
- your confidence is below high or the blast radius is non-trivial
- Bernhard asks for validation, second opinions, council review, or extra agent support

Do not use this skill for:
- trivial one-step tasks with no plan artifact
- pure read-only lookups
- emergency mitigation where delay would increase damage; document skipped validation afterward

## Required Validators

For any substantive plan:
1. Invoke Claude Opus and Gemini before main-agent synthesis when available.
2. If Claude Opus is unavailable, record the command check and use the best available Claude CLI/TUI mode or substitute one of `glm`, `minimax`, or `kimi`.
3. If Gemini is unavailable, record the command check and substitute one of `glm`, `minimax`, or `kimi`.
4. For high-risk plans, invoke at least three validators total.
5. For plan closure, combine this skill with `plan-closure-review-gate`; validator agreement does not replace codebase review.

## Preflight

Check available CLIs without exposing secrets:

```bash
for c in claude gemini glm minimax kimi; do
  printf '%s=' "$c"
  command -v "$c" || true
done
```

If a tool supports only an interactive TUI, use a PTY session and paste the validation prompt. Do not invent non-interactive flags. For Claude, prefer interactive `claude --model opus` when Opus is available; avoid `-p` / `--print` even if installed.

## Validation Packet Template

Send validators a compact packet. Include paths and constraints, not secrets.

```text
You are validating a Hermes implementation plan. Be skeptical and specific.

Task: <one-line objective>
Plan path: <path if any>
Repo/path scope: <paths/repos>
Current status: <draft/in-progress/pre-closure>
Constraints:
- <security/auth/deploy/SSO/worktree/Nexus constraints>

Plan summary:
<bullets or pasted plan section>

Please return:
1. Missing prerequisites or dependency walls
2. Likely bugs or implementation traps
3. Larger-codebase anomalies or convention conflicts to check
4. Unforeseen integration/deploy/security risks
5. Duplicate or unclean design concerns
6. Tests/validation that must run
7. Verdict: approve / approve with changes / block
Keep it concise and cite exact files/sections when possible.
```

## Standard Workflow

1. **Prepare the plan packet.** Include objective, scope, relevant files, constraints, and current plan text.
2. **Get Claude Opus critique first.** Use CLI/TUI interactive mode, preferably `claude --model opus`; do not use banned direct/API/non-interactive print modes.
3. **Get Gemini critique second.** Use Gemini CLI/TUI and ask for skeptical plan validation, not implementation.
4. **Only after both critiques, synthesize.** Compare Claude/Gemini findings before writing the main-agent plan synthesis.
5. **Invoke GLM/MiniMax/Kimi when needed.** Use them for tie-breaks, high-risk work, or when Claude/Gemini disagree.
6. **Compare responses.** Extract concrete blockers, risks, missed tests, and design objections. Ignore vague style commentary unless it maps to a real risk.
7. **Patch the plan.** Reflect valid feedback directly in the plan: tasks, acceptance criteria, rollback, tests, ownership, and blockers.
8. **Record validation evidence.** Add a section to the plan or task note:
   - validators used
   - unavailable validators and substitutions
   - key findings
   - plan changes made
   - remaining disagreements or accepted risks
9. **Only then proceed.** If validators identify a hard blocker, stop and resolve/escalate before execution.

## Plan Closure Gate

Mandatory plan-completion policy:

After every plan completion and before moving a plan from active to closed/completed/archived, run a codebase review.

That review must look for:
1. obvious bugs
2. anomalies against the larger codebase
3. unforeseen implementation issues
4. duplicate or unclean code

Do not close/archive a plan until that review has been performed and reflected in the work.

Validator approval is not enough. The closure review must inspect the delivered code and surrounding codebase, then leave durable evidence in the plan, PR, task, AAR, or commits. Use `plan-closure-review-gate` for the closure note shape.

## Evidence Note Shape

Add this to plans after validation:

```markdown
## Multi-Agent CLI/TUI Validation

- Validators requested: Claude Opus, Gemini, <others>
- Validators completed: <list>
- Unavailable/substituted: <list + reason>
- Key objections:
  - <finding + source validator>
- Plan changes made:
  - <change>
- Remaining accepted risks:
  - <risk or none>
- Validation verdict: approved / approved with changes / blocked
```

For closure, also add:

```markdown
## Closure Codebase Review

- Scope reviewed: <files/subsystem>
- Obvious bugs: none found / fixed <...>
- Larger-codebase anomalies: none found / fixed <...>
- Unforeseen implementation issues: none found / fixed <...>
- Duplicate or unclean code: none found / fixed <...>
- Validation rerun: <tests/checks>
- Closure decision: ready / blocked
```

## Common Pitfalls

1. Treating validator output as authority. It is evidence, not a substitute for Hermes judgment or source inspection.
2. Asking validators vague questions. Give them the plan text, paths, constraints, and expected verdict shape.
3. Forgetting Claude's constraint. Do not use `claude -p`, `claude --print`, Anthropic Agents SDK, or direct API calls.
4. Skipping Gemini because Claude Opus agreed. For substantive plans, Claude Opus + Gemini are the default baseline.
5. Closing a plan because validators approved it. Closure still requires the codebase review gate.
6. Failing to record evidence. If validation findings are only in terminal scrollback, the plan was not validated in a durable way.
7. Sending secrets. Validation packets must not include tokens, credentials, API keys, or private secret material.

## Verification Checklist

- [ ] Checked which validator CLIs are available
- [ ] Used Claude Opus and Gemini before main-agent synthesis, or recorded why a substitute was needed
- [ ] Used additional validators for high-risk plans
- [ ] Gave validators a concrete plan packet with paths and constraints
- [ ] Compared findings and patched the plan where appropriate
- [ ] Recorded validation evidence in the plan/task artifact
- [ ] For closure: ran the mandatory codebase review gate
- [ ] For closure: explicitly checked the four required code review categories
- [ ] For closure: reflected review results in durable evidence before closing/archive
