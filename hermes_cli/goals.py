"""Persistent session goals — the Ralph loop for Hermes.

A goal is a free-form user objective that stays active across turns. After
each turn completes, a small judge call asks an auxiliary model "is this
goal satisfied by the assistant's last response?". If not, Hermes feeds a
continuation prompt back into the same session and keeps working until the
goal is done, turn budget is exhausted, the user pauses/clears it, or the
user sends a new message (which takes priority and pauses the goal loop).

State is persisted in SessionDB's ``state_meta`` table keyed by
``goal:<session_id>`` so ``/resume`` picks it up.

Design notes / invariants:

- The continuation prompt is just a normal user message appended to the
  session via ``run_conversation``. No system-prompt mutation, no toolset
  swap — prompt caching stays intact.
- Judge failures are fail-OPEN: ``continue``. A broken judge must not wedge
  progress; the turn budget is the backstop.
- When a real user message arrives mid-loop it preempts the continuation
  prompt and also pauses the goal loop for that turn (we still re-judge
  after, so if the user's message happens to complete the goal the judge
  will say ``done``).
- This module has zero hard dependency on ``cli.HermesCLI`` or the gateway
  runner — both wire the same ``GoalManager`` in.

Nothing in this module touches the agent's system prompt or toolset.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Constants & defaults
# ──────────────────────────────────────────────────────────────────────

DEFAULT_MAX_TURNS = 20
DEFAULT_JUDGE_TIMEOUT = 30.0
# Cap how much of the last response + recent messages we send to the judge.
_JUDGE_RESPONSE_SNIPPET_CHARS = 4000
# After this many consecutive judge *parse* failures (empty output / non-JSON),
# the loop auto-pauses and points the user at the goal_judge config. API /
# transport errors do NOT count toward this — those are transient. This guards
# against small models (e.g. deepseek-v4-flash) that cannot follow the strict
# JSON reply contract; without it the loop runs until the turn budget is
# exhausted with every reply shaped like `judge returned empty response` or
# `judge reply was not JSON`.
DEFAULT_MAX_CONSECUTIVE_PARSE_FAILURES = 3

# ── Phase 1: CI Override constants ────────────────────────────────────────
CI_MAX_RETRIES = 5
CI_TIME_LIMIT_SECONDS = 3600  # 1 hour


# ── Phase 1: Goal metadata directory helpers ──────────────────────────────

def _get_goals_base_dir() -> str:
    """Return ~/.hermes/goals/"""
    try:
        from hermes_constants import get_hermes_home
        return str(get_hermes_home() / "goals")
    except Exception:
        import os
        return os.path.expanduser("~/.hermes/goals")


def _ensure_goal_dir(goal_id: str) -> "Path":
    """Create and return the metadata directory for a goal."""
    import pathlib
    d = pathlib.Path(_get_goals_base_dir()) / goal_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def init_goal_metadata(goal_id: str, goal_text: str) -> dict:
    """Create the goal metadata directory with all required files.

    Returns dict of file paths.
    """
    import pathlib
    from datetime import datetime

    ts = datetime.now().isoformat()
    d = _ensure_goal_dir(goal_id)

    files = {}

    # goal.md — the original goal text
    f = d / "goal.md"
    f.write_text(f"# Goal\n\n{goal_text}\n")
    files["goal"] = str(f)

    # phases.md — execution phases
    f = d / "phases.md"
    f.write_text(f"## Phases\n\n0. Planning\n")
    files["phases"] = str(f)

    # signals.md — completion signals from skills/hooks
    f = d / "signals.md"
    f.write_text(f"## Signals\n\n- [{ts}] goal_created: true\n")
    files["signals"] = str(f)

    # context.md — execution context for judge
    f = d / "context.md"
    f.write_text("## Context\n\n")
    files["context"] = str(f)

    # plan.md — the generated plan
    f = d / "plan.md"
    f.write_text("## Plan\n\n_Pending_ — plan not yet generated.\n")
    files["plan"] = str(f)

    # events.log — lifecycle events
    f = d / "events.log"
    f.write_text(f"[{ts}] goal_created\n")
    files["events"] = str(f)

    return files


# ── Phase 1: Signal-writing helpers ────────────────────────────────────────

def write_signal(goal_id: str, signal_type: str, value: str, metadata: dict = None):
    """Append a signal to ~/.hermes/goals/<goal_id>/signals.md"""
    try:
        import pathlib
        from datetime import datetime

        goal_dir = pathlib.Path(_get_goals_base_dir()) / goal_id
        if not goal_dir.exists():
            return

        ts = datetime.now().isoformat()
        entry = f"- [{ts}] {signal_type}: {value}"
        if metadata:
            import json as _json
            entry += f" | {_json.dumps(metadata)}"

        signals_file = goal_dir / "signals.md"
        with open(signals_file, "a") as fh:
            fh.write(entry + "\n")

        events_file = goal_dir / "events.log"
        with open(events_file, "a") as fh:
            fh.write(f"[{ts}] signal:{signal_type}={value}\n")
    except Exception:
        pass  # fail silent — signals are best-effort


def write_context(goal_id: str, phase: int, action: str, result: str):
    """Append to context.md so the judge sees execution history."""
    try:
        import pathlib
        from datetime import datetime

        goal_dir = pathlib.Path(_get_goals_base_dir()) / goal_id
        if not goal_dir.exists():
            return

        ts = datetime.now().isoformat()
        entry = f"\n## Phase {phase}: {action}\n[{ts}] {result}\n"

        ctx_file = goal_dir / "context.md"
        with open(ctx_file, "a") as fh:
            fh.write(entry)
    except Exception:
        pass


def read_signals(goal_id: str) -> str:
    """Read signals.md for the judge."""
    try:
        import pathlib
        f = pathlib.Path(_get_goals_base_dir()) / goal_id / "signals.md"
        if f.exists():
            return f.read_text()
    except Exception:
        pass
    return "(no signals yet)"


def read_context(goal_id: str) -> str:
    """Read context.md for the judge."""
    try:
        import pathlib
        f = pathlib.Path(_get_goals_base_dir()) / goal_id / "context.md"
        if f.exists():
            return f.read_text()
    except Exception:
        pass
    return "(no context yet)"


# ── Phase 1: CI Override ───────────────────────────────────────────────────

def check_council_approval(goal_id: str) -> bool:
    """Check if council has approved via signals.md."""
    signals = read_signals(goal_id)
    return "council_approved: true" in signals or "pr_approved: true" in signals


def check_ci_override(state: "GoalState") -> tuple:
    """Returns (can_override, reason) for CI failure override.

    Policy: CI fails → retry up to 5 times → after 1hr wall → council approval overrides.
    """
    if state.ci_retries < CI_MAX_RETRIES:
        return False, f"CI retriable ({state.ci_retries}/{CI_MAX_RETRIES})"

    elapsed = time.time() - state.ci_first_failure_at
    if elapsed < CI_TIME_LIMIT_SECONDS:
        remaining = CI_TIME_LIMIT_SECONDS - elapsed
        return False, f"CI time limit not reached ({int(elapsed)}s elapsed, {int(remaining)}s remaining)"

    if check_council_approval(state.metadata_dir.split("/")[-1] if state.metadata_dir else ""):
        return True, "CI failed after retries + time limit; council approved"

    return False, "CI failed but no council approval"


# ── Phase 1: WBS helpers ───────────────────────────────────────────────────

WBS_LEVELS = {
    1: "Goal",
    2: "Phase",
    3: "Work Package",
    4: "Task",
    5: "Sub-task",
}

DEP_TYPES = {
    "SS": "Start-to-Start",
    "SF": "Start-to-Finish",
    "FS": "Finish-to-Start",
    "FF": "Finish-to-Finish",
}


def wbs_number(parent: str, index: int, level: int) -> str:
    """Generate WBS number e.g. 1.1.1.1"""
    if level == 1:
        return str(index)
    return f"{parent}.{index}"


def advance_phase(state: "GoalState") -> "GoalState":
    """Advance to the next phase and log it."""
    if state.phase < state.max_phases:
        state.phase += 1
        write_signal(
            state.metadata_dir.split("/")[-1] if state.metadata_dir else "",
            "phase_advanced",
            f"phase_{state.phase}",
            {"max_phases": state.max_phases}
        )
    return state


CONTINUATION_PROMPT_TEMPLATE = (
    "[Continuing toward your standing goal]\n"
    "Goal: {goal}\n\n"
    "Continue working toward this goal. Take the next concrete step. "
    "If you believe the goal is complete, state so explicitly and stop. "
    "If you are blocked and need input from the user, say so clearly and stop."
)


JUDGE_SYSTEM_PROMPT = (
    "You are a strict judge evaluating whether an autonomous agent has "
    "achieved a user's stated goal. You receive the goal text and the "
    "agent's most recent response. Your only job is to decide whether "
    "the goal is fully satisfied based on that response.\n\n"
    "A goal is DONE only when:\n"
    "- The response explicitly confirms the goal was completed, OR\n"
    "- The response clearly shows the final deliverable was produced, OR\n"
    "- The response explains the goal is unachievable / blocked / needs "
    "user input (treat this as DONE with reason describing the block).\n\n"
    "Otherwise the goal is NOT done — CONTINUE.\n\n"
    "Reply ONLY with a single JSON object on one line:\n"
    '{\"done\": <true|false>, \"reason\": \"<one-sentence rationale>\"}'
)


JUDGE_USER_PROMPT_TEMPLATE = (
    "Goal:\n{goal}\n\n"
    "Agent's most recent response:\n{response}\n\n"
    "Is the goal satisfied?"
)


# ──────────────────────────────────────────────────────────────────────
# Dataclass
# ──────────────────────────────────────────────────────────────────────


@dataclass
class GoalState:
    """Serializable goal state stored per session."""

    goal: str
    status: str = "active"          # active | paused | done | cleared
    turns_used: int = 0
    max_turns: int = DEFAULT_MAX_TURNS
    created_at: float = 0.0
    last_turn_at: float = 0.0
    last_verdict: Optional[str] = None        # "done" | "continue" | "skipped"
    last_reason: Optional[str] = None
    paused_reason: Optional[str] = None       # why we auto-paused (budget, etc.)
    consecutive_parse_failures: int = 0       # judge-output parse failures in a row

    # ── Phase 1 enhancements ──────────────────────────────────────────────
    # Goal-family fields (all optional for backward compat)
    goal_type: str = "base"                    # base | plan | execute
    metadata_dir: str = ""                     # ~/.hermes/goals/<goal_id>/
    symphony_task_id: str = ""                  # Nexus task ID
    wbs_level: int = 1                          # WBS level (1=goal, 2=phase, 3=work pkg, 4=task)
    parent_task_id: str = ""                   # parent Symphony task for sub-tasks
    ci_override_allowed: bool = True          # council override on CI failure
    ci_retries: int = 0                        # current retry count
    ci_first_failure_at: float = 0.0          # timestamp of first CI failure
    signals_path: str = ""                      # path to signals.md
    context_path: str = ""                      # path to context.md
    plan_path: str = ""                         # path to plan.md
    phase: int = 0                              # current execution phase (0=planning)
    max_phases: int = 0
    agent_pool: list = field(default_factory=list)
    model_pool: list = field(default_factory=list)
    created_subtasks: list = field(default_factory=list)

    def __post_init__(self):
        if self.agent_pool is None:
            self.agent_pool = []
        if self.model_pool is None:
            self.model_pool = []
        if self.created_subtasks is None:
            self.created_subtasks = []

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "GoalState":
        data = json.loads(raw)
        return cls(
            goal=data.get("goal", ""),
            status=data.get("status", "active"),
            turns_used=int(data.get("turns_used", 0) or 0),
            max_turns=int(data.get("max_turns", DEFAULT_MAX_TURNS) or DEFAULT_MAX_TURNS),
            created_at=float(data.get("created_at", 0.0) or 0.0),
            last_turn_at=float(data.get("last_turn_at", 0.0) or 0.0),
            last_verdict=data.get("last_verdict"),
            last_reason=data.get("last_reason"),
            paused_reason=data.get("paused_reason"),
            consecutive_parse_failures=int(data.get("consecutive_parse_failures", 0) or 0),
            # Phase 1 fields
            goal_type=data.get("goal_type", "base"),
            metadata_dir=data.get("metadata_dir", ""),
            symphony_task_id=data.get("symphony_task_id", ""),
            wbs_level=int(data.get("wbs_level", 1) or 1),
            parent_task_id=data.get("parent_task_id", ""),
            ci_override_allowed=bool(data.get("ci_override_allowed", True)),
            ci_retries=int(data.get("ci_retries", 0) or 0),
            ci_first_failure_at=float(data.get("ci_first_failure_at", 0.0) or 0.0),
            signals_path=data.get("signals_path", ""),
            context_path=data.get("context_path", ""),
            plan_path=data.get("plan_path", ""),
            phase=int(data.get("phase", 0) or 0),
            max_phases=int(data.get("max_phases", 0) or 0),
            agent_pool=data.get("agent_pool") or [],
            model_pool=data.get("model_pool") or [],
            created_subtasks=data.get("created_subtasks") or [],
        )


# ──────────────────────────────────────────────────────────────────────
# Persistence (SessionDB state_meta)
# ──────────────────────────────────────────────────────────────────────


def _meta_key(session_id: str) -> str:
    return f"goal:{session_id}"


_DB_CACHE: Dict[str, Any] = {}


def _get_session_db() -> Optional[Any]:
    """Return a SessionDB instance for the current HERMES_HOME.

    SessionDB has no built-in singleton, but opening a new connection per
    /goal call would thrash the file. We cache one instance per
    ``hermes_home`` path so profile switches still pick up the right DB.
    Defensive against import/instantiation failures so tests and
    non-standard launchers can still use the GoalManager.
    """
    try:
        from hermes_constants import get_hermes_home
        from hermes_state import SessionDB

        home = str(get_hermes_home())
    except Exception as exc:  # pragma: no cover
        logger.debug("GoalManager: SessionDB bootstrap failed (%s)", exc)
        return None

    cached = _DB_CACHE.get(home)
    if cached is not None:
        return cached
    try:
        db = SessionDB()
    except Exception as exc:  # pragma: no cover
        logger.debug("GoalManager: SessionDB() raised (%s)", exc)
        return None
    _DB_CACHE[home] = db
    return db


def load_goal(session_id: str) -> Optional[GoalState]:
    """Load the goal for a session, or None if none exists."""
    if not session_id:
        return None
    db = _get_session_db()
    if db is None:
        return None
    try:
        raw = db.get_meta(_meta_key(session_id))
    except Exception as exc:
        logger.debug("GoalManager: get_meta failed: %s", exc)
        return None
    if not raw:
        return None
    try:
        return GoalState.from_json(raw)
    except Exception as exc:
        logger.warning("GoalManager: could not parse stored goal for %s: %s", session_id, exc)
        return None


def save_goal(session_id: str, state: GoalState) -> None:
    """Persist a goal to SessionDB. No-op if DB unavailable."""
    if not session_id:
        return
    db = _get_session_db()
    if db is None:
        return
    try:
        db.set_meta(_meta_key(session_id), state.to_json())
    except Exception as exc:
        logger.debug("GoalManager: set_meta failed: %s", exc)


def clear_goal(session_id: str) -> None:
    """Mark a goal cleared in the DB (preserved for audit, status=cleared)."""
    state = load_goal(session_id)
    if state is None:
        return
    state.status = "cleared"
    save_goal(session_id, state)


# ──────────────────────────────────────────────────────────────────────
# Judge
# ──────────────────────────────────────────────────────────────────────


def _truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "… [truncated]"


_JSON_OBJECT_RE = re.compile(r"\{.*?\}", re.DOTALL)


def _parse_judge_response(raw: str) -> Tuple[bool, str, bool]:
    """Parse the judge's reply. Fail-open to ``(False, "<reason>", parse_failed)``.

    Returns ``(done, reason, parse_failed)``. ``parse_failed`` is True when the
    judge returned output that couldn't be interpreted as the expected JSON
    verdict (empty body, prose, malformed JSON). Callers use that flag to
    auto-pause after N consecutive parse failures so a weak judge model
    doesn't silently burn the turn budget.
    """
    if not raw:
        return False, "judge returned empty response", True

    text = raw.strip()

    # Strip markdown code fences the model may wrap JSON in.
    if text.startswith("```"):
        text = text.strip("`")
        # Peel off leading json/JSON/etc tag
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1:]

    # First try: parse the whole blob.
    data: Optional[Dict[str, Any]] = None
    try:
        data = json.loads(text)
    except Exception:
        # Second try: pull the first JSON object out.
        match = _JSON_OBJECT_RE.search(text)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                data = None

    if not isinstance(data, dict):
        return False, f"judge reply was not JSON: {_truncate(raw, 200)!r}", True

    done_val = data.get("done")
    if isinstance(done_val, str):
        done = done_val.strip().lower() in {"true", "yes", "1", "done"}
    else:
        done = bool(done_val)
    reason = str(data.get("reason") or "").strip()
    if not reason:
        reason = "no reason provided"
    return done, reason, False


def judge_goal(
    goal: str,
    last_response: str,
    *,
    goal_id: str = "",
    timeout: float = DEFAULT_JUDGE_TIMEOUT,
) -> Tuple[str, str, bool]:
    """Ask the auxiliary model whether the goal is satisfied.

    Returns ``(verdict, reason, parse_failed)`` where verdict is ``"done"``,
    ``"continue"``, or ``"skipped"`` (when the judge couldn't be reached).

    ``parse_failed`` is True only when the judge call succeeded but its output
    was unusable (empty or non-JSON). API/transport errors return False — they
    are transient and should fail-open silently. Callers use this flag to
    auto-pause after N consecutive parse failures (see
    ``DEFAULT_MAX_CONSECUTIVE_PARSE_FAILURES``).

    This is deliberately fail-open: any error returns ``("continue", "...", False)``
    so a broken judge doesn't wedge progress — the turn budget and the
    consecutive-parse-failures auto-pause are the backstops.

    Phase 1 enhancement: if goal_id is provided, reads signals.md + context.md
    from ~/.hermes/goals/<goal_id>/ and enriches the judge prompt with observable
    completion signals (CI results, council approvals, phase status).
    """
    if not goal.strip():
        return "skipped", "empty goal", False
    if not last_response.strip():
        # No substantive reply this turn — almost certainly not done yet.
        return "continue", "empty response (nothing to evaluate)", False

    try:
        from agent.auxiliary_client import get_auxiliary_extra_body, get_text_auxiliary_client
    except Exception as exc:
        logger.debug("goal judge: auxiliary client import failed: %s", exc)
        return "continue", "auxiliary client unavailable", False

    try:
        client, model = get_text_auxiliary_client("goal_judge")
    except Exception as exc:
        logger.debug("goal judge: get_text_auxiliary_client failed: %s", exc)
        return "continue", "auxiliary client unavailable", False

    if client is None or not model:
        return "continue", "no auxiliary client configured", False

    # ── Phase 1: enrich judge prompt with signals ──────────────────────
    enriched_response = last_response

    if goal_id:
        try:
            signals_text = read_signals(goal_id)
            context_text = read_context(goal_id)
            if signals_text and signals_text != "(no signals yet)":
                enriched_response += "\n\n--- Observable Signals ---\n" + signals_text
            if context_text and context_text != "(no context yet)":
                enriched_response += "\n\n--- Execution Context ---\n" + context_text
        except Exception:
            pass  # fail silent — judge continues with text only

    prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        goal=_truncate(goal, 2000),
        response=_truncate(enriched_response, _JUDGE_RESPONSE_SNIPPET_CHARS),
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=200,
            timeout=timeout,
            extra_body=get_auxiliary_extra_body() or None,
        )
    except Exception as exc:
        logger.info("goal judge: API call failed (%s) — falling through to continue", exc)
        return "continue", f"judge error: {type(exc).__name__}", False

    try:
        raw = resp.choices[0].message.content or ""
    except Exception:
        raw = ""

    done, reason, parse_failed = _parse_judge_response(raw)
    verdict = "done" if done else "continue"
    logger.info("goal judge: verdict=%s reason=%s", verdict, _truncate(reason, 120))
    return verdict, reason, parse_failed


# ──────────────────────────────────────────────────────────────────────
# GoalManager — the orchestration surface CLI + gateway talk to
# ──────────────────────────────────────────────────────────────────────


class GoalManager:
    """Per-session goal state + continuation decisions.

    The CLI and gateway each hold one ``GoalManager`` per live session.

    Methods:

    - ``set(goal)`` — start a new standing goal.
    - ``clear()`` — remove the active goal.
    - ``pause()`` / ``resume()`` — explicit user controls.
    - ``status()`` — printable one-liner.
    - ``evaluate_after_turn(last_response)`` — call the judge, update state,
      and return a decision dict the caller uses to drive the next turn.
    - ``next_continuation_prompt()`` — the canonical user-role message to
      feed back into ``run_conversation``.
    """

    def __init__(self, session_id: str, *, default_max_turns: int = DEFAULT_MAX_TURNS):
        self.session_id = session_id
        self.default_max_turns = int(default_max_turns or DEFAULT_MAX_TURNS)
        self._state: Optional[GoalState] = load_goal(session_id)

    # --- introspection ------------------------------------------------

    @property
    def state(self) -> Optional[GoalState]:
        return self._state

    def is_active(self) -> bool:
        return self._state is not None and self._state.status == "active"

    def has_goal(self) -> bool:
        return self._state is not None and self._state.status in {"active", "paused"}

    def status_line(self) -> str:
        s = self._state
        if s is None or s.status in {"cleared",}:
            return "No active goal. Set one with /goal <text>."
        turns = f"{s.turns_used}/{s.max_turns} turns"
        if s.status == "active":
            return f"⊙ Goal (active, {turns}): {s.goal}"
        if s.status == "paused":
            extra = f" — {s.paused_reason}" if s.paused_reason else ""
            return f"⏸ Goal (paused, {turns}{extra}): {s.goal}"
        if s.status == "done":
            return f"✓ Goal done ({turns}): {s.goal}"
        return f"Goal ({s.status}, {turns}): {s.goal}"

    # --- mutation -----------------------------------------------------

    def set(self, goal: str, *, max_turns: Optional[int] = None, goal_type: str = "base") -> GoalState:
        goal = (goal or "").strip()
        if not goal:
            raise ValueError("goal text is empty")

        # Generate a goal_id for the metadata directory
        import hashlib
        import time as _time
        goal_id = hashlib.sha256(f"{goal[:100]}{_time.time()}".encode()).hexdigest()[:12]

        # Initialize metadata directory with all required files
        meta_files = init_goal_metadata(goal_id, goal)

        state = GoalState(
            goal=goal,
            status="active",
            turns_used=0,
            max_turns=int(max_turns) if max_turns else self.default_max_turns,
            created_at=_time.time(),
            last_turn_at=0.0,
            # Phase 1 fields
            goal_type=goal_type,
            metadata_dir=meta_files["signals"].replace("/signals.md", ""),
            signals_path=meta_files["signals"],
            context_path=meta_files["context"],
            plan_path=meta_files["plan"],
        )
        self._state = state
        save_goal(self.session_id, state)
        return state

    def pause(self, reason: str = "user-paused") -> Optional[GoalState]:
        if not self._state:
            return None
        self._state.status = "paused"
        self._state.paused_reason = reason
        save_goal(self.session_id, self._state)
        return self._state

    def resume(self, *, reset_budget: bool = True) -> Optional[GoalState]:
        if not self._state:
            return None
        self._state.status = "active"
        self._state.paused_reason = None
        if reset_budget:
            self._state.turns_used = 0
        save_goal(self.session_id, self._state)
        return self._state

    def clear(self) -> None:
        if self._state is None:
            return
        self._state.status = "cleared"
        save_goal(self.session_id, self._state)
        self._state = None

    def mark_done(self, reason: str) -> None:
        if not self._state:
            return
        self._state.status = "done"
        self._state.last_verdict = "done"
        self._state.last_reason = reason
        save_goal(self.session_id, self._state)

    # --- the main entry point called after every turn -----------------

    def evaluate_after_turn(
        self,
        last_response: str,
        *,
        user_initiated: bool = True,
    ) -> Dict[str, Any]:
        """Run the judge and update state. Return a decision dict.

        ``user_initiated`` distinguishes a real user prompt (True) from a
        continuation prompt we fed ourselves (False). Both increment
        ``turns_used`` because both consume model budget.

        Decision keys:
          - ``status``: current goal status after update
          - ``should_continue``: bool — caller should fire another turn
          - ``continuation_prompt``: str or None
          - ``verdict``: "done" | "continue" | "skipped" | "inactive"
          - ``reason``: str
          - ``message``: user-visible one-liner to print/send
        """
        state = self._state
        if state is None or state.status != "active":
            return {
                "status": state.status if state else None,
                "should_continue": False,
                "continuation_prompt": None,
                "verdict": "inactive",
                "reason": "no active goal",
                "message": "",
            }

        # Count the turn that just finished.
        state.turns_used += 1
        state.last_turn_at = time.time()

        verdict, reason, parse_failed = judge_goal(
            state.goal, last_response,
            goal_id=state.metadata_dir.split("/")[-1] if state.metadata_dir else "",
        )
        state.last_verdict = verdict
        state.last_reason = reason

        # Track consecutive judge parse failures. Reset on any usable reply,
        # including API / transport errors (parse_failed=False) so a flaky
        # network doesn't trip the auto-pause meant for bad judge models.
        if parse_failed:
            state.consecutive_parse_failures += 1
        else:
            state.consecutive_parse_failures = 0

        if verdict == "done":
            state.status = "done"
            save_goal(self.session_id, state)
            return {
                "status": "done",
                "should_continue": False,
                "continuation_prompt": None,
                "verdict": "done",
                "reason": reason,
                "message": f"✓ Goal achieved: {reason}",
            }

        # Auto-pause when the judge model can't produce the expected JSON
        # verdict N turns in a row. Points the user at the goal_judge config
        # so they can route this side task to a model that follows the
        # contract (e.g. google/gemini-3-flash-preview). Without this guard,
        # weak judge models burn the entire turn budget returning prose or
        # empty strings.
        if state.consecutive_parse_failures >= DEFAULT_MAX_CONSECUTIVE_PARSE_FAILURES:
            state.status = "paused"
            state.paused_reason = (
                f"judge model returned unparseable output {state.consecutive_parse_failures} turns in a row"
            )
            save_goal(self.session_id, state)
            return {
                "status": "paused",
                "should_continue": False,
                "continuation_prompt": None,
                "verdict": "continue",
                "reason": reason,
                "message": (
                    f"⏸ Goal paused — the judge model ({state.consecutive_parse_failures} turns) "
                    "isn't returning the required JSON verdict. Route the judge to a stricter "
                    "model in ~/.hermes/config.yaml:\n"
                    "  auxiliary:\n"
                    "    goal_judge:\n"
                    "      provider: openrouter\n"
                    "      model: google/gemini-3-flash-preview\n"
                    "Then /goal resume to continue."
                ),
            }

        if state.turns_used >= state.max_turns:
            state.status = "paused"
            state.paused_reason = f"turn budget exhausted ({state.turns_used}/{state.max_turns})"
            save_goal(self.session_id, state)
            return {
                "status": "paused",
                "should_continue": False,
                "continuation_prompt": None,
                "verdict": "continue",
                "reason": reason,
                "message": (
                    f"⏸ Goal paused — {state.turns_used}/{state.max_turns} turns used. "
                    "Use /goal resume to keep going, or /goal clear to stop."
                ),
            }

        save_goal(self.session_id, state)
        return {
            "status": "active",
            "should_continue": True,
            "continuation_prompt": self.next_continuation_prompt(),
            "verdict": "continue",
            "reason": reason,
            "message": (
                f"↻ Continuing toward goal ({state.turns_used}/{state.max_turns}): {reason}"
            ),
        }

    def next_continuation_prompt(self) -> Optional[str]:
        if not self._state or self._state.status != "active":
            return None
        return CONTINUATION_PROMPT_TEMPLATE.format(goal=self._state.goal)


__all__ = [
    "GoalState",
    "GoalManager",
    "CONTINUATION_PROMPT_TEMPLATE",
    "DEFAULT_MAX_TURNS",
    "CI_MAX_RETRIES",
    "CI_TIME_LIMIT_SECONDS",
    "WBS_LEVELS",
    "DEP_TYPES",
    "load_goal",
    "save_goal",
    "clear_goal",
    "judge_goal",
    "init_goal_metadata",
    "write_signal",
    "write_context",
    "read_signals",
    "read_context",
    "check_ci_override",
    "wbs_number",
    "advance_phase",
]
