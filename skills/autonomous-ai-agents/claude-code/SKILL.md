---
name: claude-code
description: "Use when you need Claude Code via the Claude CLI only — interactive/tmux orchestration, never Claude print mode or the Anthropic agent SDKs."
version: 3.0.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Anthropic, Code-Review, Refactoring, PTY, Automation]
    related_skills: [codex, hermes-agent, opencode]
---

# Claude Code — Hermes Orchestration Guide

> **Bernhard ecosystem override:** Do **not** use Anthropic agent SDKs or Claude print mode / `claude --print` in this ecosystem's skills, hooks, scripts, implementations, or code. Treat May 2026 Claude Max pricing as separate from Anthropic API billing. If Claude is used here at all, keep it CLI-only and outside print-mode/programmatic automation. The print-mode examples below are upstream/general-reference material, not approved Bernhard-ecosystem practice.

Delegate coding tasks to [Claude Code](https://code.claude.com/docs/en/cli-reference) (Anthropic's autonomous coding agent CLI) via the Hermes terminal. Claude Code v2.x can read files, write code, run shell commands, spawn subagents, and manage git workflows autonomously.

## Hard Rule

This ecosystem does **not** allow:
- Claude print mode
- Anthropic agent SDKs
- direct Anthropic programmatic API patterns as the default Claude lane
- skills, scripts, or hooks that rely on Claude API-key billing behind the user's back

Approved Claude invocation path:
- `claude` CLI
- interactive session
- usually orchestrated through `tmux` when Hermes needs to drive it
- OAuth/subscription-backed usage through the CLI surface only

Reason:
- programmatic Claude usage has a separate billing/cost/credit surface from the chat subscription lane
- Claude print mode and SDK/API flows are easy to misuse in automation and violate Bernhard's current policy

## When to Use

Use this skill when:
- you want Claude's coding help on a repo
- you need a multi-turn Claude coding session
- you want Hermes to drive Claude in a durable tmux session
- you need Claude review/refactor/test help without switching to API/SDK patterns

Do **not** use this skill for:
- headless one-shot Claude print mode runs
- Anthropic SDK integrations
- server-side automation that depends on Anthropic API keys
- wrappers that try to treat Claude Max as blanket-free API access

## Preferred Operating Pattern

### Mode 1: Interactive CLI in tmux

This is the default approved pattern.

```bash
# Start a tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code inside it
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")

# Wait for startup, then send the task
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor the auth module to use JWT tokens' Enter")

# Monitor progress
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -80")

# Send follow-up
terminal(command="tmux send-keys -t claude-work 'Now add unit tests for the new JWT code' Enter")

# Exit cleanly
terminal(command="tmux send-keys -t claude-work '/exit' Enter")
```

Why this is preferred:
- stays on the approved CLI lane
- preserves conversational context
- avoids Claude print mode
- keeps the billing/auth path explicit

### Mode 2: Interactive CLI with explicit permissions bypass

Only use `--dangerously-skip-permissions` when the task truly needs it and the user has already asked for that level of autonomy.

```bash
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude --dangerously-skip-permissions' Enter")
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Review the repository and propose the smallest safe fix for the failing tests' Enter")
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -80")
```

## First-Launch Dialog Handling

Claude Code can show confirmation dialogs on first launch.

### Workspace trust

Default choice is usually correct.

```bash
terminal(command="sleep 4 && tmux send-keys -t claude-work Enter")
```

### Permissions bypass warning

If `--dangerously-skip-permissions` triggers a warning, the safe automation pattern is:

```bash
terminal(command="sleep 3 && tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter")
```

## Useful CLI Commands

| Command | Purpose |
|---|---|
| `claude` | Start interactive REPL |
| `claude "query"` | Start REPL with an initial prompt |
| `claude -c` | Continue the most recent conversation in this directory |
| `claude -r "id"` | Resume a specific session |
| `claude auth login` | Sign in |
| `claude auth status` | Check login status |
| `claude doctor` | Run health checks |
| `claude update` / `claude upgrade` | Update Claude Code |
| `claude mcp list` | Inspect MCP configuration |
| `claude agents` | List configured agents |

## Session Recipes

### Start a repo review session

```bash
terminal(command="tmux new-session -d -s claude-review -x 140 -y 40")
terminal(command="tmux send-keys -t claude-review 'cd /path/to/repo && claude' Enter")
terminal(command="sleep 5 && tmux send-keys -t claude-review 'Review the current branch for correctness, risks, and missing tests. Give findings first.' Enter")
terminal(command="sleep 20 && tmux capture-pane -t claude-review -p -S -120")
```

### Resume an existing session

```bash
terminal(command="tmux new-session -d -s claude-resume -x 140 -y 40")
terminal(command="tmux send-keys -t claude-resume 'cd /path/to/repo && claude -c' Enter")
terminal(command="sleep 5 && tmux send-keys -t claude-resume 'Continue from the prior context and finish the test fixes.' Enter")
```

### Parallel work with separate tmux sessions

```bash
# Task 1
terminal(command="tmux new-session -d -s claude-task1 -x 140 -y 40")
terminal(command="tmux send-keys -t claude-task1 'cd ~/project && claude' Enter")
terminal(command="sleep 5 && tmux send-keys -t claude-task1 'Fix the auth bug in src/auth.py' Enter")

# Task 2
terminal(command="tmux new-session -d -s claude-task2 -x 140 -y 40")
terminal(command="tmux send-keys -t claude-task2 'cd ~/project && claude' Enter")
terminal(command="sleep 5 && tmux send-keys -t claude-task2 'Write integration tests for the API endpoints' Enter")
```

## Cost and Billing Guardrail

As of May 2026, treat Claude programmatic/API usage as a **separate billing surface** from ordinary Claude subscription chat usage unless Anthropic documentation explicitly proves otherwise for the exact path you are using.

Operational rule for this ecosystem:
- do **not** rely on Max/Pro subscription assumptions to justify SDK/API automation
- do **not** build skills around Anthropic API credits unless Bernhard explicitly approves that lane
- prefer other providers for true programmatic wrapper automation
- keep Claude on the CLI lane only

## Common Pitfalls

1. **Using Claude print mode because it looks convenient.**
   Not allowed here.

2. **Assuming Max covers API/SDK automation.**
   Dangerous assumption. Treat programmatic billing separately.

3. **Building a wrapper around the Anthropic agent SDKs.**
   Not allowed in this ecosystem.

4. **Trying to force Claude into a stateless one-shot subprocess pattern.**
   Use tmux + interactive CLI instead.

5. **Skipping verification after Claude changes code.**
   Claude output is still a claim until tests, diffs, and files are verified.

## Verification Checklist

- [ ] No Claude print mode used anywhere in commands, scripts, or notes
- [ ] No Anthropic agent SDKs introduced
- [ ] Claude was invoked through the CLI only
- [ ] Session was run interactively, usually through tmux when automated by Hermes
- [ ] Result was verified with repo reads/tests/diffs, not trusted blindly
- [ ] Any billing assumptions were stated conservatively
