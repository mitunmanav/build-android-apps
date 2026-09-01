"""state/state.py — minimal load/save/validate for state.json.

Phase 1 scope: schema validation on read/write + safe defaults when file
is missing. Mutations + plan algebra live in Phase 2 (state-manager +
plan-mutator).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SCHEMA_PATH = Path(__file__).parent / "schema.json"

DEFAULT_STATE: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "phase": "idle",
    "plan": [],
    "cursor": {"phase": "intake", "task_id": ""},
    "history": [],
}


def current_schema_version() -> int:
    """Return the schema version this module understands (always 1 for v1.0)."""
    return SCHEMA_VERSION


def load(path: Path) -> dict[str, Any]:
    """Load state.json from path. Returns DEFAULT_STATE if missing/corrupt.

    Never raises on missing file — first-run projects have no state yet.
    Raises ValueError on schema mismatch (caller decides whether to migrate).
    """
    if not path.exists():
        return dict(DEFAULT_STATE)
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
