---
name: improve-system
description: >
  Five-mode ecosystem improvement engine: audit stale/conflicting/duplicate memories and notes;
  review and enhance skills with cross-agent telemetry; capture stories, wins, and lessons;
  mine conversations for missed learnings; and fill missing foundational content.
  Picks mode from context or asks when unclear.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [improve, audit, memory, skills, knowledge, foundation, experience, lessons, ecosystem]
    related_skills:
      - nightly-knowledge-harvest
      - nexus-knowledge
      - skill-ecosystem-auditor
      - skill-review
      - ecosystem-sync
trigger_keywords:
  - improve system
  - improve-system
  - /improve-system
  - audit memories
  - audit notes
  - review skill
  - skill review
  - capture experience
  - capture story
  - capture win
  - capture lesson
  - historical review
  - mine conversations
  - missed learnings
  - fill foundation
  - foundation content
  - system audit
  - ecosystem improvement
  - knowledge gap
---

# Improve System

Five-mode engine for continuously improving the agent ecosystem. Detects mode from context or asks the user to pick.

## Modes at a Glance

| # | Mode | Purpose |
|---|------|---------|
| 1 | **audit** | Find stale, conflicting, or duplicate memories, notes, and knowledge artifacts |
| 2 | **skill-review** | Improve a skill using cross-agent telemetry and multi-device conversations |
| 3 | **experience** | Capture a story, win, or lesson the user just shared |
| 4 | **historical-review** | Mine recent conversations across the whole ecosystem for missed learnings |
| 5 | **foundation** | Fill in missing foundational content (rules, guides, SOPs, knowledge gaps) |

## Mode Selection

1. Scan the user's request for trigger keywords matching a mode.
2. If exactly one mode matches, proceed with that mode.
3. If ambiguous or no match, ask: *"Which mode? (1) audit (2) skill-review (3) experience (4) historical-review (5) foundation"*
4. The user may also invoke directly: `/improve-system audit`, `/improve-system skill-review`, etc.

---

## Mode 1 — Audit

Find and surface stale, conflicting, or duplicate memories, notes, and knowledge artifacts across the ecosystem.

### Scan Targets

| Target | Location | Method |
|--------|----------|--------|
| Agent memories | `memory` tool (user + memory stores) | `memory(action='list')` equivalent — read all entries |
| Nexus knowledge | `mcp_nexus_kb_nexus_query` | Semantic search for overlapping topics |
| Nexus guides | `mcp_nexus_kb_nexus_guides_list` | List all, check for duplicates/stale |
| Nexus documents | `mcp_nexus_kb_nexus_documents` | List all, check for duplicates |
| Apple Notes | `memo find` or skill | Search for stale/duplicate notes |
| Obsidian vault | Obsidian skill | Search for stale/duplicate notes |
| Scratchpads | `~/.claude/temp/scratchpad/` | List files, check age |
| Plans | `~/.claude/plans/`, `~/.agents/plans/`, `~/.mercury/plans/` | Check for completed/stale plans |
| Agent config notes | `~/.agents/rules/`, `~/.agents/memory/` | Cross-reference with Nexus |

### Audit Dimensions

1. **Staleness** — Content older than 30 days with no references, or superseded by newer content.
2. **Conflicts** — Two entries making contradictory claims (e.g., "use X" vs "never use X").
3. **Duplicates** — Same knowledge stored in multiple locations (memory + Nexus + notes).
4. **Orphans** — Skills, plans, or docs referenced nowhere else and never triggered.
5. **Drift** — Content that contradicts current ecosystem state (e.g., references deleted repos, old servers).

### Output

1. Categorized findings table: `stale | conflicting | duplicate | orphaned | drifted`
2. For each finding: location, age, recommended action (archive, merge, delete, update)
3. Execute fixes only after user confirmation
4. Log results to `~/.agents/knowledge/improve-system-audits/YYYY-MM-DD-audit.md`

---

## Mode 2 — Skill Review

Improve a specific skill using telemetry and cross-agent conversations from the entire ecosystem.

### Data Sources

| Source | What to Extract |
|--------|----------------|
| Nexus telemetry | `mcp_nexus_kb_nexus_events_list` — skill usage events, errors, failures |
| Session DB (session_search) | Search for the skill name across ALL agent sessions |
| Cross-agent sessions | Hermes: `~/.hermes/sessions/`, Mercury: `~/.mercury/sessions/`, Minerva: `~/.minerva/sessions/`, Athena: `~/.athena/sessions/`, OpenClaw: `~/.openclaw/sessions/`, Nano: `~/.nano/sessions/` |
| Cross-device check | Mac Mini, Mac Studio, MacBook Pro — verify skill exists and is in sync |
| Skill file itself | Read full SKILL.md + linked references, templates, scripts |
| Registry entries | Check `~/.claude/registry_skills.md`, `~/.agents/registries/skills.md` for registration accuracy |

### Review Steps

1. **Load the skill** — Read SKILL.md + all linked files.
2. **Check Nexus telemetry** — Query events for skill invocation, errors, or failures.
3. **Mine sessions** — `session_search(query="<skill-name>")` across all agent homes; look for:
   - User corrections related to the skill
   - Errors or pitfalls encountered
   - Missing steps discovered during use
   - Suggestions for improvement
4. **Cross-device verify** — Check skill exists on Mac Mini, Mac Studio, MBP; compare versions.
5. **Cross-agent verify** — Check all agent homes have the skill registered and accessible.
6. **Identify improvements** — Collate findings into actionable patches.
7. **Apply patches** — Use `skill_manage(action='patch')` with specific old/new strings.
8. **Re-propagate** — Follow ecosystem-sync to push updates to all devices and registries.
9. **Log** — Write review summary to `~/.agents/knowledge/skill-reviews/YYYY-MM-DD-<skill-name>-review.md`

### Output

- Skill improvement report with specific changes made
- Before/after diff summary
- Propagation status across devices and agents

---

## Mode 3 — Experience

Capture a story, win, or lesson the user just shared and persist it properly.

### Capture Steps

1. **Listen** — Identify the narrative: what happened, what was the outcome, what was learned.
2. **Classify** — Tag as: `story` | `win` | `lesson` | `failure` | `correction` | `insight`
3. **Structure** — Format as:
   ```
   ## [Classification]: [Title]
   - **When**: [Date or relative time]
   - **Context**: [What was happening]
   - **What happened**: [The experience]
   - **Takeaway**: [The lesson or value]
   - **Tags**: [Relevant tags]
   ```
4. **Persist** — Store in multiple surfaces:
   - Nexus guide: `mcp_nexus_kb_nexus_guides_create` with tags
   - Agent memory: `memory(action='add')` with a concise declarative summary
   - Knowledge file: `~/.agents/knowledge/experiences/YYYY-MM-DD-<slug>.md`
5. **Cross-reference** — Link to relevant skills, plans, or Nexus entities if applicable.

### Output

- Confirmation of what was captured and where it was stored
- Links/references to the persisted artifacts

---

## Mode 4 — Historical Review

Mine recent conversations across the whole ecosystem for learnings that were not captured at the time.

### Scan Scope

| Agent | Session DB Path | Notes |
|-------|----------------|-------|
| Hermes | `~/.hermes/sessions/` | Primary sessions |
| Mercury | `~/.mercury/sessions/` | Adversarial review sessions |
| Minerva | `~/.minerva/sessions/` | Research sessions |
| Athena | `~/.athena/sessions/` | Analysis sessions |
| OpenClaw | `~/.openclaw/sessions/` | Gateway sessions |
| Nano | `~/.nano/sessions/` | Lightweight sessions |
| Claude Code | `~/.claude/sessions/` | Code sessions |
| Gemini | `~/.gemini/sessions/` | Gemini sessions |
| Codex | `~/.codex/sessions/` | Codex sessions |
| Kimi | `~/.kimi/sessions/` | Kimi sessions |

### Review Steps

1. **Time window** — Default: last 7 days. User can specify a range.
2. **Discovery queries** — Run `session_search` on the current machine plus check session DBs on other devices via SSH (Mac Mini → Mac Studio → MBP, or vice versa).
3. **Extract** — For each relevant session, look for:
   - Decisions made without documentation
   - Errors resolved without a lesson captured
   - User corrections or preferences stated
   - Architecture decisions or contract clarifications
   - Deploy/auth/rollback gotchas
   - Coordination insights
   - Performance observations
4. **Deduplicate** — Merge overlapping learnings from multiple agents' sessions.
5. **Prioritize** — Rank by: (a) recurrence across agents, (b) severity of impact, (c) durability.
6. **Capture** — For each missed learning:
   - Create Nexus guide or update existing one
   - Add to agent memory if it's a preference or rule
   - Patch relevant skills if the learning affects a procedure
   - Write to `~/.agents/knowledge/missed-learnings/YYYY-MM-DD-<slug>.md`
7. **Summary** — Produce a consolidated report.

### Output

- Number of sessions scanned per agent per device
- List of missed learnings extracted, categorized and prioritized
- Where each learning was persisted
- Skills patched (if any)

---

## Mode 5 — Foundation

Fill in missing foundational content: rules, guides, SOPs, knowledge that the ecosystem should have but doesn't.

### Gap Detection

1. **Rule gaps** — Check `~/.agents/rules/` for missing coverage of known ecosystem patterns.
2. **Guide gaps** — Query Nexus guides for common operational domains with no guide.
3. **Skill gaps** — Cross-reference session errors/pitfalls with existing skills; missing skill = gap.
4. **Knowledge gaps** — Check `~/.agents/memory/SHARED_FACTS.md` and Nexus knowledge graph for missing entities or relationships.
5. **Registry gaps** — Verify all skills are registered in both `~/.claude/registry_skills.md` and `~/.agents/registries/skills.md`.
6. **Cross-device gaps** — Check if foundational files exist on Mac Mini, Mac Studio, and MBP.

### Foundation Categories

| Category | Examples |
|----------|----------|
| Agent conventions | Naming, paths, communication protocol |
| Operational SOPs | Deploy flow, incident response, rollback |
| Architecture decisions | System topology, data flow, auth model |
| Tool-specific guides | CLI tools, API patterns, MCP servers |
| Team coordination | A2A protocol, War Room rules, heartbeat |
| Security | Credential management, access control, audit |

### Fill Steps

1. **Identify the gap** — Determine what's missing.
2. **Source the content** — Extract from conversations, existing docs, or best practices.
3. **Draft** — Write the foundational content in the correct format and location.
4. **Register** — If it's a skill, follow A+B rule. If a guide, use Nexus. If a rule, place in `~/.agents/rules/`.
5. **Propagate** — Ecosystem-sync to all devices and agent homes.
6. **Verify** — Check that the content is discoverable and loadable.

### Output

- List of gaps identified
- Content created for each gap (type, location, summary)
- Propagation and verification status

---

## Cross-Device Compatibility

This skill is compatible with all agents in the ecosystem:

- **Hermes** (`~/.hermes/skills/`)
- **Mercury** (`~/.mercury/skills/`)
- **Minerva** (`~/.minerva/skills/`)
- **Athena** (`~/.athena/skills/`)
- **OpenClaw** (`~/.openclaw/skills/`)
- **Nano** (`~/.nano/skills/`)
- **Claude Code** (`~/.claude/skills/`)
- **Gemini** (`~/.gemini/skills/`)
- **Codex** (`~/.codex/skills/`)
- **Kimi** (`~/.kimi/skills/`)
- **KiloCode** (`~/.kilocode/skills/`)

Canonical location: `~/.agents/skills/software-development/improve-system/`
Mirrored to all agent homes via ecosystem-sync or manual symlink.

## Cross-Device Targets

| Device | Method |
|--------|--------|
| Mac Mini (this machine) | Direct file write |
| Mac Studio | `scp -r` via Tailscale |
| MacBook Pro | `scp -r` via Tailscale |
| AI-Servers | `scp -r` via Tailscale |

## Pitfalls

- **Mercury skill-name collision**: On the Mac Mini, skills may exist in both `~/.mercury/skills/` and `~/.hermes-shared-skills/`. Use `~/.agents/skills/` (Tree A) as the canonical location to avoid ambiguity. If skill_view/skill_manage refuses, use absolute-path file editing instead.
- **Session DB access**: Other agents' session DBs may not be directly queryable via `session_search`. Use `terminal` to read SQLite files on other devices via SSH.
- **Nexus availability**: If Nexus is down, fall back to local file-based storage and sync later.
- **Large session scans**: For historical-review mode, limit to 7 days by default to avoid excessive I/O. User can override with a date range.
- **Cross-device SSH**: Always `mkdir -p` the remote parent directory before `scp -r`.
