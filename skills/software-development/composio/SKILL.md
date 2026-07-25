---
name: composio
description: "Use 1000+ external apps (Gmail, Slack, GitHub, Notion, etc.) via Composio CLI or SDK. For agents and apps that need to automate external service actions. Source: https://github.com/composiohq/skills (Composio community skills)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows]
tags: [automation, tools, external-apps, cli, mcp, agents, gmail, slack, github, notion]
source: https://github.com/composiohq/skills
---

# Composio

## Install

```bash
# Install CLI
curl -fsSL https://composio.dev/install | bash

# Authenticate (OAuth — interactive)
composio login

# Verify
composio whoami
```

**Requirements:** Node.js (for SDK use), shell access for CLI.

---

Composio gives AI agents **1000+ tool integrations** across external apps — Gmail, Slack, GitHub, Notion, Jira, Salesforce, and more. Agents use the CLI to search, link accounts, and execute tools on behalf of users.

## Core Workflow

```
composio search "<use case>"     # Find tools
composio link <toolkit>           # Connect user account
composio execute "<TOOL_SLUG>" -d '{...params}'   # Run a tool
composio listen                   # Listen for trigger events
```

## Key Commands

| Command | Description |
|---------|-------------|
| `composio search "<query>"` | Find tools by use case |
| `composio execute "<TOOL>" -d '{...}'` | Execute a tool with input params |
| `composio link <toolkit>` | Connect user account to an app |
| `composio listen` | Real-time trigger event listener |
| `composio init` | Set up API key in a project directory |
| `composio whoami` | Verify auth state (org_id, project_id, user_id) |

## Two Usage Modes

### 1. CLI (no code)
Use when the user wants to take action directly — search → link → execute.

```bash
# Find GitHub tools
composio search "create github issue"

# Connect GitHub
composio link github

# Execute
composio execute "GITHUB_CREATE_ISSUE" -d '{"owner":"me","repo":"myrepo","title":"Bug","body":"..."}'
```

### 2. SDK (for AI apps/agents)
Use when writing code that integrates external tools.

```bash
cd my-project
composio init   # Sets up API key in project
```

Then use the Composio SDK in your code:
```javascript
import { Composio } from 'composio-core';
const client = new Composio();
```

## Reference Docs

- `references/composio-cli.md` — Full Composio CLI reference
- `references/building-with-composio.md` — SDK integration guide

## Pitfalls

1. **Browser-less auth** — agents without browser use `composio login --no-wait | jq` to get URL/key for user to complete OAuth out-of-band
2. **Tool slugs** — exact slugs from `composio search` must be used in `execute`
3. **Per-user linking** — each user account connection requires `composio link <toolkit>` run once
4. **API key setup** — SDK use requires `composio init` in the project directory first
