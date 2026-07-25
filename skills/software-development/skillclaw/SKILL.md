---
name: skillclaw
description: "SkillClaw: collective skill evolution for AI agents. Auto-evolves, deduplicates, and improves skills across sessions, agents, and devices. Native Hermes/Claude Code/OpenClaw support. Source: https://github.com/AMAP-ML/SkillClaw (2.2K stars)"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux, windows]
tags: [skills, evolution, hermes, claude-code, openclaw, multi-agent]
source: https://github.com/AMAP-ML/SkillClaw
---

# SkillClaw

## Install

```bash
# Clone
git clone https://github.com/AMAP-ML/SkillClaw.git && cd SkillClaw

# Install (requires Python 3.10+)
uv venv ~/.skillclaw_env --python 3.11
~/.skillclaw_env/bin/pip install -e ".[evolve,sharing,server]"

# Setup (choose 'hermes' for CLI agent integration)
~/.skillclaw_env/bin/skillclaw setup

# Start daemon
~/.skillclaw_env/bin/skillclaw start --daemon
~/.skillclaw_env/bin/skillclaw status
```

**Requirements:** Python 3.10+, Git, uv (`pip install uv` if not present)

**Binary location:** `~/.skillclaw_env/bin/skillclaw` (add to PATH or alias in shell profile)

---

SkillClaw runs a **post-task evolution loop** that automatically improves your skill library from every real session — without interrupting your workflow.

**Key benefit:** Skills evolve collectively. Every session, every agent, every device feeds the same evolution loop. Skills auto-deduplicate, improve, and distribute back.

## Quick Commands

```bash
skillclaw setup                    # First-time wizard (choose hermes CLI agent)
skillclaw start --daemon          # Start the evolution proxy
skillclaw status                  # Check running state
skillclaw doctor hermes           # Verify Hermes integration
skillclaw skills list             # List local skills
skillclaw skills push             # Upload local skills to shared storage
skillclaw skills pull             # Download shared skills
skillclaw dashboard serve         # Visual dashboard (local)
```

## How It Works

1. **Task loop** — You work with Hermes/Claude Code normally
2. **Evolution loop** — SkillClaw silently processes session data post-task
3. **Skill improvement** — Skills are auto-merged, deduplicated, improved
4. **Distribution** — Updated skills sync across all your agents and devices

## Hermes Integration

After `skillclaw setup` + `skillclaw start --daemon`, SkillClaw rewrites `~/.hermes/config.yaml` to route through its local proxy. Hermes uses `~/.hermes/skills` as the default local skill library.

```bash
# Verify integration
skillclaw doctor hermes

# Restore original Hermes config if needed
skillclaw restore hermes
```

## Ecosystem Architecture

```
Multiple Hermes agents
  ├── Hermes (Mac Mini)  ──┐
  ├── Hermes (MBP)       ──┼── SkillClaw ──► unified skill library
  └── Hermes (Server)   ──┘         │
                                     ▼
                              skillclaw-evolve-server
                                   (optional, for team)
```

## Verification

```bash
skillclaw status
PROXY_PORT="$(skillclaw config proxy.port | awk '{print $2}')"
curl "http://127.0.0.1:${PROXY_PORT}/healthz"
# Expected: {"ok": true}
```

## Pitfalls

1. **First run needs `skillclaw setup`** — without it, no config exists and the daemon won't start
2. **Proxy port** — defaults to `30000` but check with `skillclaw config show`
3. **Hermes config backup** — SkillClaw rewrites `~/.hermes/config.yaml`; use `skillclaw restore hermes` to undo
4. **Evolution server** — optional for single user; required for team shared storage
5. **Shared storage** — supports OSS (Alibaba) and Nacos backends; not required for solo use
