---
name: oh-my-hermes
description: "An opinionated workflow layer for building, shipping, and operating apps with Hermes Agent. Like Oh My Zsh for Hermes — installs 36 skills and 7 focused agents (CTO loop). Source: https://github.com/Salomondiei08/oh-my-hermes (709 stars, MIT, Shell)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows]
tags: [hermes, workflow, cto-loop, kanban, autonomous-agents, shipping, deployment, monitoring, security-review, github]
source: https://github.com/Salomondiei08/oh-my-hermes
---

# Oh My Hermes (OMH)

An opinionated workflow layer for building, shipping, and operating apps — delivered directly to Hermes. Like Oh My Zsh is to Zsh. You install it once and Hermes becomes genuinely useful for real software projects.

## Install

```bash
# Requires Hermes Agent already installed
# Install Oh My Hermes
git clone https://github.com/salomondiei08/oh-my-hermes /tmp/oh-my-hermes
bash /tmp/oh-my-hermes/install.sh

# Then message your bot:
# "set up the CTO loop"
```

The installer copies 36 skills, 6 workflows, and 7 agent profiles into `~/.hermes/`.

---

## Core Idea

```
Understand -> Design -> Build -> Check -> Ship -> Learn
```

The CTO coordinates seven focused agents through Hermes Kanban. GitHub issues and PRs are useful delivery evidence, but they are not the roadmap or the goal. Work can start from an idea, customer feedback, production logs, analytics, or an issue.

Hermes reads the project before asking anything. It asks at most three useful questions, supplies recommended defaults, and continues when you skip them. Only irreversible actions (production release, rollback, public posting, licensed media, payment, destructive account changes) require your approval.

## 7-Agent CTO Loop

```
Founder
  |
  v
CTO: lifecycle, roadmap, delegation, decisions
  |
  +-- Product: brief, priorities, positioning, SEO, content
  +-- Designer: UX, visual verification, launch assets and video
  +-- Builder: working product increments
  +-- Reviewer: journeys, visual/accessibility checks, PR review
  +-- Security: release risk plus daily/weekly assessment
  +-- Ops: deploy, health, deduplicated logs, incidents
  |
  v
Hermes Kanban + memory + cron + completion evidence
```

## Key Skills (36 total)

### Product & Design
| Skill | What Hermes does |
|-------|-----------------|
| `onboarding` | Infers setup, asks at most three optional questions |
| `clarify-requirements` | Reads first, asks only material questions, continues with defaults |
| `product-brief` | Writes compact product source of truth and acceptance criteria |
| `design-handoff` | Designer creates `DESIGN.md` and verifies implemented UI |
| `product-marketing` | Positioning, website copy, SEO, launch strategy, content schedule |
| `creative-production` | Product assets and HyperFrames launch video |

### Build & Ship
| Skill | What Hermes does |
|-------|-----------------|
| `ship-this-idea` | Flagship idea → brief → design → build → verify → ship flow |
| `implement-with-claude-code` | Scaffolds Claude Code with full context + scope constraints |
| `implement-with-codex` | Scaffolds Codex for targeted single-file fixes |
| `deploy-to-vercel` | Pre-deploy checks → deploy → capture URL |
| `connect-supabase` | Links Supabase, pushes migrations, sets Vercel env vars |
| `setup-monitoring` | Configures Sentry + Uptime Kuma |
| `post-deploy-followup` | Health check + deployment log + notification + summary |

### Operations
| Skill | What Hermes does |
|-------|-----------------|
| `health-check` | Calls `/api/health`, validates response, checks Supabase + Vercel logs |
| `observe-logs` | Deduplicates runtime errors, escalates only actionable changes |
| `failure-recovery` | Saves failed cron/agent context to dead-letter logs |
| `reset-runtime` | Backs up and clears stale Hermes runtime state |
| `rollback` | Rolls back Vercel production to previous deploy (requires founder YES) |
| `server-bootstrap` | Sets up fresh server with Hermes, Telegram, OMH, and CTO loop |
| `backup-hermes-data` | Tarballs `~/.hermes/` to S3, Dropbox, or local |

### GitHub Integration
| Skill | What Hermes does |
|-------|-----------------|
| `manage-github-issues` | Triage, create, label, assign, close GitHub issues |
| `create-github-pr` | Creates PR with secret scan before opening |
| `auto-issue-triage` | Hourly: scores open issues, picks top priority, starts work |
| `review-github-pr` | Verifies product increment, then approves or requests changes |
| `await-merge-approval` | Founder chooses YES, NO, CLOSE, or LATER |

### Meta & Utilities
| Skill | What Hermes does |
|-------|-----------------|
| `create-skill` | Creates a new skill in the correct format (meta-skill) |
| `choose-engine` | Routes tasks to Hermes, Claude Code, or Codex |
| `project-switch` | Switches product context without mixing repo, URL, logs, or approvals |
| `project-status` | Founder-readable status for gateway, model, project, crons, integrations |
| `cto-status-report` | Daily morning report: in progress, done, blocked |
| `kanban-task` | Creates and updates Hermes kanban cards at every stage |
| `send-notification` | Sends Slack webhook with deployment or status info |
| `security-review` | Tool-backed release gate + daily/weekly assessments |

## Getting Started

1. Install Hermes Agent (https://hermes-agent.nousresearch.com)
2. Run `git clone https://github.com/salomondiei08/oh-my-hermes /tmp/oh-my-hermes && bash /tmp/oh-my-hermes/install.sh`
3. Message your bot: `set up the CTO loop`
4. Connect GitHub when useful (issues + PR delivery)
5. Add production URL after deploy (health + log observation)
6. Use `/goal` command for agent focus across long sessions

## Pitfalls

1. **CTO loop needs onboarding** — message "set up the CTO loop" first to configure all 7 agents
2. **Irreversible actions always require approval** — production release, rollback, public posting, licensed media, payment, destructive changes
3. **Project context must be set** — use `project-switch` before working on a different product
4. **Hermes Kanban is the evidence trail** — all work is tracked as cards, not just GitHub issues/PRs
5. **Auto-issue-triage runs hourly** — top priority issue gets work started automatically
