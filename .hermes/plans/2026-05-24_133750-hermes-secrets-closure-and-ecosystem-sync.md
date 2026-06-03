# Hermes Secrets Closure + Ecosystem-Sync Enhancement Plan

> **For Hermes:** This is a planning-only artifact. Review and execute only after Bernhard explicitly restarts work.

**Goal:** Close the current secrets/env cleanup against the new Nexus-only policy, then improve ecosystem-sync guidance and verification so the whole agent fleet follows the same secret-handling rules without drifting back to local `.env` sprawl.

**Architecture:** Use a staged cutover. First establish the live truth about where secrets still exist and whether Nexus bootstrap already covers runtime needs. Then close the migration safely by separating bootstrap/routing variables from durable secrets. Only after that, update ecosystem-sync guidance and verification so propagation workflows reinforce the new policy instead of reintroducing local secret copies.

**Tech Stack / Surfaces:**
- Hermes Python code: `hermes_cli/env_loader.py`
- Hermes tests: `tests/hermes_cli/test_env_loader.py`
- Workspace/runtime canon: `AGENTS.md`, `~/.hermes/workspace/FLEET_REFERENCE.md`
- Environment-policy skills/canon:
  - `~/.athena/skills/software-development/bernhard-agent-environment-conventions/SKILL.md`
  - `~/.athena/skills/software-development/bernhard-ecosystem-onboarding/SKILL.md`
  - `~/.hermes/skills/devops/ecosystem-sync-operations/SKILL.md`

---

## Current context and assumptions

- Bernhard’s current instruction overrides older upstream `.env` conventions: **all API keys, tokens, secrets, and the global `.env` must live only in Nexus**.
- The Hermes repo already has a Nexus bootstrap path in `hermes_cli/env_loader.py` via `_load_nexus_bootstrap_env()`.
- Existing tests already prove one important cutover invariant: Nexus-fetched values can override stale local dotenv secrets.
- `ecosystem-sync-operations` already encodes a hard rule that secrets must never ride ecosystem-sync, but the broader workflow still needs explicit closure/verification steps tied to the new policy.
- Work is currently paused; this document is for review/checking, not immediate execution.

---

## Proposed execution sequence

1. Audit the actual remaining local-secret surfaces.
2. Classify every local env variable as either:
   - non-secret bootstrap/routing config that may remain local temporarily, or
   - durable secret that must move to Nexus only.
3. Verify the Nexus bootstrap path covers live runtime needs before any secret deletion.
4. Remove or deprecate remaining local durable-secret storage only after verification.
5. Update ecosystem-sync guidance/tests/docs so secret drift does not re-enter through sync workflows.
6. Run a closure review before marking the plan complete.

---

## Step-by-step plan

### Task 1: Baseline the current secret-loading behavior

**Objective:** Confirm the current code path and tests already supporting Nexus bootstrap and local dotenv precedence.

**Files:**
- Read: `hermes_cli/env_loader.py`
- Read/Test: `tests/hermes_cli/test_env_loader.py`
- Read: `AGENTS.md`

**Steps:**
1. Re-read `hermes_cli/env_loader.py` and identify the exact order of operations:
   - local/user `.env` load
   - project `.env` load
   - Nexus bootstrap load
   - credential sanitization
2. Re-read `tests/hermes_cli/test_env_loader.py` and map which behaviors are already covered.
3. Produce a short matrix:
   - covered by tests
   - behavior exists but untested
   - desired by policy but not yet implemented

**Verification:**
- A written matrix exists with no guessed behavior.
- Every claim points back to code or test evidence.

---

### Task 2: Inventory local env / secret drift surfaces

**Objective:** Find where durable secrets may still exist outside Nexus.

**Files / Surfaces to inspect:**
- `~/.hermes/.env`
- repo/project `.env` files relevant to Hermes runtime
- profile-specific env/config surfaces if they participate in startup
- adjacent bot homes only if they are part of the same active bootstrap path

**Steps:**
1. Enumerate candidate env files and bootstrap/config surfaces.
2. For each surface, classify entries into:
   - bootstrap routing/config (`HERMES_NEXUS_BOOTSTRAP_URL`, integration IDs, profile selectors, non-secret base URLs)
   - secrets (`*_API_KEY`, tokens, passwords, service tokens, credential material)
3. Flag any place where the same durable secret appears in more than one local file.
4. Flag any place where local storage is still acting as the real source of truth instead of Nexus.

**Verification:**
- A concrete inventory exists with path + classification for each surface.
- No raw secret values are copied into notes or chat.

**Risk note:**
- Do not delete anything during inventory. This is read-only classification.

---

### Task 3: Define the cutover contract

**Objective:** Write down the exact line between what may remain local and what must move to Nexus.

**Files likely to update:**
- `hermes_cli/env_loader.py` (only if current behavior conflicts with contract)
- docs/skills touched later in the plan

**Contract to enforce:**
- Allowed locally, if needed for bootstrap:
  - Nexus base URL
  - integration ID / manifest selector
  - non-secret runtime routing/config values
- Not allowed as durable local state:
  - API keys
  - tokens
  - passwords
  - service secrets
  - the global `.env` as a long-lived secret store

**Steps:**
1. Compare the desired contract against current loader behavior.
2. Identify whether the loader needs:
   - stricter docs only,
   - stricter tests,
   - or code changes to prevent fallback drift.
3. Decide the safest transition mode:
   - temporary compatibility with local secrets during cutover, or
   - hard failure once bootstrap is confirmed live.

**Verification:**
- One explicit contract statement exists that Hermes can review against code/tests.
- Any transition behavior is labeled temporary vs final-state.

---

### Task 4: Close test gaps before changing runtime behavior

**Objective:** Ensure the migration is guarded by tests before tightening behavior.

**Files likely to modify:**
- `tests/hermes_cli/test_env_loader.py`
- possibly new test helpers under `tests/hermes_cli/`

**Likely missing test targets:**
- bootstrap variables remain local while durable secrets come from Nexus
- Nexus bootstrap missing/partial payload behavior
- multiple local env sources exist but Nexus still wins for durable secrets
- future regression: local secret fallback accidentally becomes authoritative again

**Steps:**
1. Add failing tests for any missing contract-critical behavior.
2. Run only the env-loader test target first.
3. If behavior is wrong, patch implementation minimally.
4. Re-run targeted tests until green.

**Verification command:**
```bash
pytest tests/hermes_cli/test_env_loader.py -v
```

**Expected result:**
- All env-loader tests pass.
- New tests clearly encode the Nexus-only policy for durable secrets.

---

### Task 5: Tighten the runtime implementation if needed

**Objective:** Make the loader enforce the cutover contract without causing an avoidable startup outage.

**Files likely to modify:**
- `hermes_cli/env_loader.py`

**Possible implementation directions:**
- Keep bootstrap/routing variables local but let Nexus override secret-bearing keys.
- Add a clearer separation between bootstrap config and secret payloads.
- Add warnings/telemetry when durable secrets are still being loaded from local `.env` during transition.
- Avoid broad local fallback that silently normalizes secret drift.

**Steps:**
1. Patch only the minimum logic required by the tests and contract.
2. Preserve staged-cutover safety: do not strand startup if live bootstrap is not yet verified.
3. Re-run targeted tests.
4. If feasible, run a slightly broader Hermes CLI test slice touching import/startup env behavior.

**Verification commands:**
```bash
pytest tests/hermes_cli/test_env_loader.py -v
pytest tests/hermes_cli -k env -v
```

**Expected result:**
- The loader behavior matches the written contract.
- No regressions in nearby env/startup tests.

---

### Task 6: Produce a secrets-plan closure checklist

**Objective:** Convert the audit + implementation state into an explicit closure list Bernhard/Hermes can approve.

**Deliverable should answer:**
- What secret surfaces still exist locally?
- Which are transitional bootstrap-only?
- Which still need migration into Nexus?
- What evidence proves runtime can start from Nexus bootstrap?
- What exact deletions/cleanups remain after verification?

**Checklist items should include:**
- inventory completed
- bootstrap path verified live
- duplicate durable secret copies removed
- no ecosystem-sync category transports secrets
- docs/skills updated to reflect final rule
- closure codebase review completed before marking done

**Verification:**
- A reviewer can tell, in one screen, whether the plan is truly closable.

---

### Task 7: Enhance ecosystem-sync guidance to reinforce the new policy

**Objective:** Make ecosystem-sync docs/verification explicitly support Nexus-only secret management.

**Files likely to inspect/update:**
- `~/.hermes/skills/devops/ecosystem-sync-operations/SKILL.md`
- canonical ecosystem-sync implementation/docs if they live under `~/.claude/skills/ecosystem-sync/` (verify canonical source before editing)
- any propagated/local copies only after canonical source is confirmed

**Required guidance to preserve or strengthen:**
- secrets never ride ecosystem-sync
- `env`/secret categories stay excluded from `--full`
- verification distinguishes `source changed`, `local copy changed`, and `propagation completed`
- post-sync verification uses direct remote evidence, not just the tool banner

**Steps:**
1. Identify the canonical source for ecosystem-sync docs/implementation.
2. Compare canonical source vs propagated/local copies for drift.
3. Patch the canonical source first.
4. Ensure wording explicitly covers the new Bernhard rule: the global `.env` belongs in Nexus and is not to be redistributed across agent homes.
5. Add/adjust verification guidance so operators can prove that no secret categories were reintroduced.

**Verification:**
- The canonical ecosystem-sync source contains the updated rule.
- Any propagated copies are checked separately and not confused with source-of-truth edits.

---

### Task 8: Validate sync behavior without transporting secrets

**Objective:** Confirm ecosystem-sync workflows still function while keeping secrets out of band.

**Files / Surfaces:**
- canonical ecosystem-sync tool/config source
- representative remote targets named by the sync workflow

**Steps:**
1. Run a dry-run of the relevant ecosystem-sync mode.
2. Confirm `env` / secret categories are excluded.
3. Verify bot-home or config propagation still includes the intended non-secret files.
4. If sync claims success, directly verify representative targets.

**Verification standard:**
- exact dry-run/real commands used
- which targets were checked
- which file paths were verified remotely
- explicit statement that no secret category was transported

**Note:**
- Only execute this task after Bernhard re-enables work.

---

### Task 9: Run plan-closure review before declaring done

**Objective:** Satisfy the workspace rule that plan closure requires a codebase review for bugs, anomalies, and duplicate/unclean code.

**Files / Surfaces:**
- changed Python files
- changed tests
- changed skills/docs

**Steps:**
1. Review diffs for duplicated logic, inconsistent policy wording, or partial propagation.
2. Check for mismatches between code behavior, tests, and docs.
3. Verify no stale local-secret guidance remains in touched files.
4. Only then move the plan from active to closed.

**Verification:**
- Closure note includes explicit review findings, even if the finding is “no additional issues found”.

---

## Likely files to change

**Code / tests**
- `hermes_cli/env_loader.py`
- `tests/hermes_cli/test_env_loader.py`

**Docs / skills / policy surfaces**
- `~/.hermes/skills/devops/ecosystem-sync-operations/SKILL.md`
- canonical ecosystem-sync implementation/docs under `~/.claude/skills/ecosystem-sync/` if that is confirmed as source of truth
- possibly repo/workspace policy docs if they still describe local `.env` as a durable secret store

**Possibly inspect-only unless drift is confirmed**
- `AGENTS.md`
- `~/.hermes/workspace/FLEET_REFERENCE.md`
- `~/.athena/skills/software-development/bernhard-agent-environment-conventions/SKILL.md`

---

## Tests / validation

**Primary test target**
```bash
pytest tests/hermes_cli/test_env_loader.py -v
```

**Secondary targeted validation**
```bash
pytest tests/hermes_cli -k env -v
```

**Operational verification**
- direct inspection of runtime env-loading logic
- direct check of local env surfaces without exposing secret values
- ecosystem-sync dry-run evidence showing no secret categories are included
- direct remote verification on representative targets if sync-related changes are made

---

## Risks and tradeoffs

- **Outage risk:** deleting local secrets before live bootstrap is proven can break startup.
- **Drift risk:** patching propagated ecosystem-sync copies instead of the canonical source creates false completion.
- **Policy ambiguity risk:** if some local variables are both bootstrap inputs and secrets, they need explicit classification before enforcement.
- **Verification risk:** a sync success banner is not enough; direct target checks are required.

---

## Open questions for review

1. Should Hermes eventually hard-fail when durable local secrets are present after bootstrap is proven, or only warn?
2. What is the canonical ecosystem-sync source to edit first in this environment: `~/.claude/skills/ecosystem-sync/...` or another managed source?
3. Which local variables, if any, are temporarily allowed to remain outside Nexus for bootstrap continuity?

---

## Definition of done

This plan is complete only when all of the following are true:
- durable secrets are no longer treated as local source-of-truth
- Nexus bootstrap is verified as the live secret authority
- env-loader tests encode the new contract
- ecosystem-sync guidance and verification explicitly preserve the Nexus-only rule
- representative sync validation proves no secret transport
- closure review is performed before marking the work done
