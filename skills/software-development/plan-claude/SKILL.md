---
name: plan-claude
description: >
  MANDATORY pre-work gate for all agents. Invokes Claude CLI with --model opus to generate
  a plan that passes the exitplanmode hook (23+ required sections, frontmatter, quality gates).
  Ensures plan is persisted to MBP first, Mac Studio second, Mac Mini third. Escalates on
  quota exhaustion. Do not start large-scale work without this skill completing.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [plan, claude, opus, mandatory, quality-gate, exitplanmode, pre-work, cross-agent]
    related_skills:
      - plan-quality-mode
      - writing-plans
      - plan
      - ecosystem-sync
trigger_keywords:
  - plan-claude
  - /plan-claude
  - plan with claude
  - plan with opus
  - claude plan
  - opus plan
  - mandatory plan
  - pre-work plan
---

# Plan-Claude — Mandatory Pre-Work Planning Gate

**IRON RULE**: No agent (Hermes, Mercury, Minerva, Athena, OpenClaw, Nano, or any future agent) may begin large-scale work without first completing a plan generated via this skill.

## When This Skill Fires

This skill is **mandatory** when ANY of these conditions are true:

1. The task involves 3+ files or 2+ hours of work
2. The task involves infrastructure changes (deploy, config, servers)
3. The task involves API changes, auth changes, or database schema changes
4. The task involves cross-agent coordination
5. The task involves security-sensitive operations
6. The user says "plan", "plan this", "/plan-claude", or any trigger keyword
7. A Symphony task is being picked up for IN_PROGRESS

This skill is **NOT required** for:
- Single-file edits with no blast radius
- Quick questions, lookups, or status checks
- Formatting or cosmetic changes
- Explicit user override: "skip planning" / "just do it"

## Step 1 — Detect Current Agent & Model

1. Identify the current agent (Hermes / Mercury / Minerva / Athena / OpenClaw / Nano / other).
2. Identify the current model (check environment or `HERMES_MODEL` / agent config).
3. If the current model IS Claude Sonnet or Claude Opus → the agent can plan directly using `plan-quality-mode` skill. Still execute Steps 3–7 for persistence and propagation.
4. If the current model is NOT Claude Sonnet or Opus → proceed to Step 2 to invoke Claude CLI.

## Step 2 — Invoke Claude CLI with Opus

### Command Template

```bash
claude --model opus
```

The alias `opus` resolves to the latest Claude Opus model automatically (currently `claude-opus-4-20250514`).

### Prompt to Feed Claude

Construct the prompt with these components:

```
You are generating a plan that MUST pass the exitplanmode quality gate hook.

## Task Description
<describe the task the user wants planned>

## Plan Quality Requirements
You MUST include ALL of the following sections in the plan:

### Required Frontmatter (BLOCKING if missing)
---
project: <project-name>
status: in_progress
difficulty: <1-100>
confidence: <1-100>
---

### Required Sections (23+ sections, ALL mandatory)
1. Context — Why this task exists
2. Implementation — Step-by-step chunks with exact file paths and commands
3. Strict Constraints — Anti-patterns, forbidden practices, what NOT to do
4. Environment & Configuration — Build targets, env vars, platform specifics
5. Data Flow & State Management — How data moves through the system
6. Edge Cases — Known edge cases and how to handle them
7. Testing Strategy — RED-GREEN-REFACTOR, test commands, coverage targets
8. Security — Auth, secrets, credential handling
9. Backwards Compatibility — Breaking changes, migration path
10. Verification — How to verify each step worked
11. Rollback — How to undo if something goes wrong
12. Files — All files that will be created/modified
13. Dependencies — External deps, versions, package changes
14. Regulatory Compliance — Any compliance requirements
15. Scope — In-scope and out-of-scope boundaries
16. Definition of Done — Acceptance criteria, MUST PASS items
17. Assumptions & Risks — Risk log with severity
18. Observability & Logging — Telemetry, monitoring
19. Discovered Issues — Open findings (ALL must be resolved [x] before plan exit)
20. Regression Testing — Regression test plan
21. Vision (conditional: required when >3 files) — Feature vision, BLUEPRINT.md alignment >=75%
22. Self-Verification — Verify steps the agent must run post-implementation
23. Documentation — Nexus docs, guide updates needed
24. Security Scan — Pre-commit secret scan step

### Quality Rules
- Context budget: max 300 lines, 25 files, 8 chunks, 40KB, 120k tokens
- Per-chunk limits: max 15 files, 25 steps, 100 lines
- NO unfilled brackets like [Provide...] — every section must have real content
- NO open checkboxes in Discovered Issues — all must be [x]
- Production deploys MUST mention canary/staging/QA
- Delegation Strategy mandatory when >15 files or >5 chunks

Generate the complete plan now.
```

### Handling the Claude CLI Session

1. Start the Claude CLI session interactively: `claude --model opus` in a PTY.
2. Paste the constructed prompt.
3. Wait for Claude to produce the plan.
4. Extract the full plan text from the session output.
5. If Claude asks clarifying questions, relay them to the user and feed answers back.

## Step 3 — Model Availability & Quota Check

### If `--model opus` fails:

1. **Model not found / name error**: The model alias may have changed. Look up the current syntax:
   ```bash
   # Check available models
   claude --help 2>&1 | grep -i model
   ```
   If `opus` alias doesn't work, try the full model ID. Search online for the latest Claude Opus model identifier:
   ```
   https://docs.anthropic.com/en/docs/about-claude/models
   ```
   The pattern is typically `claude-opus-4-YYYYMMDD` or similar. Use the latest dated variant.

2. **Rate limit / overloaded**: Wait 30 seconds and retry once. If still failing, fall back to `sonnet`:
   ```bash
   claude --model sonnet
   ```
   Note the fallback in the plan frontmatter.

3. **Quota exhausted / subscription empty**:
   - **ESCALATE IMMEDIATELY** to the user.
   - Do NOT proceed with the work.
   - Message: *"Claude Opus quota is exhausted. Cannot generate plan. Please check your Claude Max/Pro subscription status and try again."*
   - Log the escalation to `~/.agents/knowledge/plan-claude-escalations/YYYY-MM-DD-<slug>.md`

## Step 4 — Validate Plan Against Quality Gate

Before persisting, verify the plan passes the quality gate:

1. **Frontmatter check**: `project`, `status`, `difficulty`, `confidence` all present and valid.
2. **Section completeness**: All 23+ required sections present with real content (no `[Provide...]` stubs).
3. **Discovered Issues**: All checkboxes resolved `[x]` (no open `- [ ]`).
4. **Context budget**: Under 300 lines, 25 files, 8 chunks, 40KB.
5. **Per-chunk limits**: Each chunk under 15 files, 25 steps, 100 lines.
6. **Deploy gates**: Production deploys mention canary/staging.

If validation fails, feed the errors back to Claude for correction. Repeat up to 2 times. If still failing after 2 retries, persist the plan with a warning and flag for manual review.

## Step 5 — Persist Plan with Redundancy Chain

### File Naming Convention

```
~/.claude/plans/<agent>/<YYYY-MM-DD>_<HHMMSS>-<slug>.md
```

Where:
- `<agent>` = the agent generating the plan (hermes, mercury, minerva, athena, openclaw, nano)
- `<slug>` = kebab-case description of the task (max 60 chars)
- Example: `~/.claude/plans/mercury/2026-06-03_142500-gpu-gateway-v2-hardening.md`

### Redundancy Chain (write in order, stop at first success)

| Priority | Device | Hostname / IP | Path |
|----------|--------|---------------|------|
| **1 (primary)** | MacBook Pro | `bernie-macbookpro-m4` | `~/.claude/plans/<agent>/` |
| **2 (fallback)** | Mac Studio | `100.122.177.88` | `~/.claude/plans/<agent>/` |
| **3 (local)** | Mac Mini (this machine) | localhost | `~/.claude/plans/<agent>/` |

### Write Procedure

```bash
PLAN_FILE="<YYYY-MM-DD>_<HHMMSS>-<slug>.md"
PLAN_DIR="~/.claude/plans/<agent>"
PLAN_CONTENT="<the plan text>"

# Try MBP first
ssh bernie-macbookpro-m4 "mkdir -p ${PLAN_DIR}" 2>/dev/null && \
  echo "${PLAN_CONTENT}" | ssh bernie-macbookpro-m4 "cat > ${PLAN_DIR}/${PLAN_FILE}" 2>/dev/null

if [ $? -eq 0 ]; then
  echo "Plan persisted to MBP (primary)"
else
  # Fallback to Mac Studio
  ssh 100.122.177.88 "mkdir -p ${PLAN_DIR}" 2>/dev/null && \
    echo "${PLAN_CONTENT}" | ssh 100.122.177.88 "cat > ${PLAN_DIR}/${PLAN_FILE}" 2>/dev/null

  if [ $? -eq 0 ]; then
    echo "Plan persisted to Mac Studio (fallback)"
  else
    # Last resort: local Mac Mini
    mkdir -p "${PLAN_DIR}" && \
      echo "${PLAN_CONTENT}" > "${PLAN_DIR}/${PLAN_FILE}"
    echo "Plan persisted locally on Mac Mini (last resort)"
  fi
fi
```

### Post-Write: Sync to All Devices

After successful write to the primary target, attempt to copy the plan to the other devices in the chain for full redundancy:

```bash
# If MBP was primary, also copy to Mac Studio and local
scp bernie-macbookpro-m4:${PLAN_DIR}/${PLAN_FILE} /tmp/${PLAN_FILE} 2>/dev/null
ssh 100.122.177.88 "mkdir -p ${PLAN_DIR}" && scp /tmp/${PLAN_FILE} 100.122.177.88:${PLAN_DIR}/ 2>/dev/null
mkdir -p ${PLAN_DIR} && cp /tmp/${PLAN_FILE} ${PLAN_DIR}/
```

## Step 6 — Log & Notify

1. Log the plan creation to Nexus:
   ```
   mcp_nexus_kb_nexus_events_log(
     event_type="plan.created",
     aggregate_type="plan",
     aggregate_id="<plan-slug>",
     payload={
       "agent": "<agent-name>",
       "model": "opus",
       "difficulty": <score>,
       "confidence": <score>,
       "primary_device": "<device-where-stored>",
       "redundancy_status": "<full|partial|local-only>"
     }
   )
   ```

2. Emit a Symphony task comment if the work is tracked.

3. Report to the user:
   - Plan filename and location
   - Device redundancy status
   - Whether validation passed or has warnings

## Step 7 — Gate: No Work Without Completed Plan

After this skill completes:
- The plan file MUST exist on at least one device
- The plan MUST have passed validation (or have explicit warnings noted)
- The agent MAY NOW proceed with execution, following the plan's implementation steps
- If the agent deviates from the plan, it must document why in the plan file

## Complete Flow Diagram

```
User request → Is it large-scale work?
  ├─ No → Proceed normally (no plan needed)
  └─ Yes → Is current model Sonnet/Opus?
       ├─ Yes → Generate plan directly → Validate → Persist → Done
       └─ No → Invoke `claude --model opus`
            ├─ Success → Generate plan → Validate → Persist → Done
            ├─ Model not found → Lookup syntax → Retry
            ├─ Rate limited → Wait + retry OR fallback to sonnet
            └─ Quota exhausted → ESCALATE to user (hard stop)
```

## Cross-Agent Applicability

| Agent | Skill Home | Notes |
|-------|-----------|-------|
| Hermes | `~/.hermes/skills/` | Team lead — most frequent user |
| Mercury | `~/.mercury/skills/` | Adversarial review — plans required before review |
| Minerva | `~/.minerva/skills/` | Research — plans for multi-research efforts |
| Athena | `~/.athena/skills/` | Analysis — plans for complex analysis |
| OpenClaw | `~/.openclaw/skills/` | Gateway — plans for infra changes |
| Nano | `~/.nano/skills/` | Lightweight — plans optional (skip for trivial) |
| Future agents | TBD | Add to this table when provisioned |

## Model Reference

| Date | Alias | Full Model ID | Notes |
|------|-------|---------------|-------|
| 2025-05 | `opus` | `claude-opus-4-20250514` | Latest as of skill creation |
| 2025-05 | `sonnet` | `claude-sonnet-4-20250514` | Fallback when Opus unavailable |

**When a new Opus model is released**: The `opus` alias automatically resolves to the latest. If the alias breaks, search `https://docs.anthropic.com/en/docs/about-claude/models` for the latest model ID.

## Pitfalls

- **Claude CLI must be interactive**: Per ecosystem rule, Claude must be used via interactive CLI only — never `claude -p`, Anthropic SDK, or direct API calls. Use PTY mode (`pty=true`) for the terminal session.
- **Quota is subscription-governed**: Claude Max/Pro subscriptions have usage limits. If Opus is unavailable, the error will indicate rate limiting or quota exhaustion. Do NOT fall back to API-key-based execution.
- **Plan path scoping**: The `plan_path_scoping_validator.py` hook enforces that plans go to `~/.claude/plans/<agent>/`, not the root `plans/` directory. Always include the agent subdirectory.
- **Discovered Issues gate**: The quality gate BLOCKS plan exit if any `- [ ]` checkboxes remain in Discovered Issues. All must be `[x]`.
- **Cross-device SSH**: Always `mkdir -p` the remote directory before writing. Network may be intermittent on Tailscale.
- **Mercury skill-name collision**: On Mac Mini, skills may exist in both `~/.mercury/skills/` and `~/.hermes-shared-skills/`. Use `~/.agents/skills/` as canonical.
- **Large plans**: If the task is very large (>300 lines), split into sub-plans with a master plan linking them. The quality gate blocks oversized plans.
