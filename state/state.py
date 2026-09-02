"""state/state.py — minimal load/save/validate for state.json.

Phase 1 scope: schema validation on read/write + safe defaults when file
is missing. Mutations + plan algebra live in Phase 2 (state-manager +
plan-mutator).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
SCHEMA_PATH = Path(__file__).parent / "schema.json"

LEDGER_LIMIT = 200
AGENT_LOG_LIMIT = 100

DEFAULT_ORCHESTRATION: dict[str, Any] = {
    "mode": "guided",  # guided = 1 human gate (spec); autopilot = none mid-run
    "status": "idle",  # idle|running|stopped|awaiting_user
    "fix_round": 0,
    "staleness": 0,  # consecutive loop steps with no state advance (cap: 3 → stop)
    "current_task_id": "",
    "metrics": {
        "tasks_done": 0,
        "first_pass": 0,
        "fix_rounds_total": 0,
        "staleness_stops": 0,
        "ui_tasks_with_evidence": 0,
        "ui_tasks_total": 0,
    },
}

DEFAULT_STATE: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "phase": "idle",
    "plan": [],
    "cursor": {"phase": "intake", "task_id": ""},
    "constraints": [],  # spec's global constraints, verbatim, one line each
    "orchestration": dict(DEFAULT_ORCHESTRATION, metrics=dict(DEFAULT_ORCHESTRATION["metrics"])),
    "ledger": [],  # append-only loop record: Task N: ... / Ruling: ... lines
    "agents": [],  # dispatch log: {at, name, task_id, model, status}
    "history": [],
}


def current_schema_version() -> int:
    """Return the schema version this module understands."""
    return SCHEMA_VERSION


def load(path: Path) -> dict[str, Any]:
    """Load state.json from path. Returns DEFAULT_STATE if missing/corrupt.

    Never raises on missing file — first-run projects have no state yet.
    Raises ValueError on schema mismatch (caller decides whether to migrate).
    """
    if not path.exists():
        # deep copy: DEFAULT_STATE holds nested dicts (orchestration.metrics)
        # that must never be shared across StateManager instances
        return json.loads(json.dumps(DEFAULT_STATE))
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"state.json at {path} is not valid JSON: {e}") from e
    if not isinstance(raw, dict):
        raise ValueError(f"state.json at {path} must be a JSON object, got {type(raw).__name__}")
    validate(raw)
    return raw


def save(path: Path, state: dict[str, Any]) -> None:
    """Validate and write state.json atomically. Path is created if missing."""
    validate(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def validate(state: dict[str, Any]) -> None:
    """Lightweight structural validation. Full JSON-schema check is
    optional (requires `jsonschema` package; we keep it dependency-free
    by default so this module works on a fresh `/setup` install).
    """
    required = ("schema_version", "phase", "plan", "cursor", "history")
    missing = [k for k in required if k not in state]
    if missing:
        raise ValueError(f"state.json missing required fields: {missing}")

    if state["schema_version"] != SCHEMA_VERSION:
        raise ValueError(
            f"state.json schema_version={state['schema_version']}; "
            f"expected {SCHEMA_VERSION}. Run `python -m state.migrate {state['schema_version']} {SCHEMA_VERSION}`."
        )

    phase = state["phase"]
    allowed = {"intake", "plan", "scaffold", "build", "test", "publish", "update", "idle"}
    if phase not in allowed:
        raise ValueError(f"state.json phase={phase!r} not in {allowed}")

    if not isinstance(state["plan"], list):
        raise ValueError("state.json plan must be an array")
    for i, item in enumerate(state["plan"]):
        if not isinstance(item, dict):
            raise ValueError(f"plan[{i}] must be an object")
        for k in ("id", "title", "status", "phase"):
            if k not in item:
                raise ValueError(f"plan[{i}] missing field {k!r}")

    if not isinstance(state["cursor"], dict):
        raise ValueError("state.json cursor must be an object")

    if not isinstance(state["history"], list):
        raise ValueError("state.json history must be an array")
    if len(state["history"]) > 50:
        raise ValueError("state.json history exceeds 50 entries (ring buffer overflow)")
    for i, item in enumerate(state["history"]):
        if not isinstance(item, dict):
            raise ValueError(f"history[{i}] must be an object")
        for k in ("at", "action", "summary"):
            if k not in item:
                raise ValueError(f"history[{i}] missing field {k!r}")

    # ---- v2 sections (orchestration loop) ----------------------------
    if state["schema_version"] >= 2:
        for k in ("constraints", "orchestration", "ledger", "agents"):
            if k not in state:
                raise ValueError(f"state.json (v2) missing required field {k!r}")
        if not isinstance(state["constraints"], list) or not all(
            isinstance(c, str) for c in state["constraints"]
        ):
            raise ValueError("state.json constraints must be an array of strings")
        orch = state["orchestration"]
        if not isinstance(orch, dict):
            raise ValueError("state.json orchestration must be an object")
        if orch.get("mode") not in ("guided", "autopilot"):
            raise ValueError("orchestration.mode must be 'guided' or 'autopilot'")
        if orch.get("status") not in ("idle", "running", "stopped", "awaiting_user"):
            raise ValueError("orchestration.status must be idle|running|stopped|awaiting_user")
        if not isinstance(orch.get("metrics", {}), dict):
            raise ValueError("orchestration.metrics must be an object")
        for name, arr, cap in (
            ("ledger", state["ledger"], LEDGER_LIMIT),
            ("agents", state["agents"], AGENT_LOG_LIMIT),
        ):
            if not isinstance(arr, list):
                raise ValueError(f"state.json {name} must be an array")
            if len(arr) > cap:
                raise ValueError(f"state.json {name} exceeds {cap} entries (ring buffer overflow)")
            for i, item in enumerate(arr):
                if not isinstance(item, dict):
                    raise ValueError(f"{name}[{i}] must be an object")
