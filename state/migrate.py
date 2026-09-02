"""state/migrate.py — version-aware migration for state.json.

Supported upgrades: v0 (no schema_version) → v1 (field add) and
v1 → v2 (adds constraints/orchestration/ledger/agents; existing data kept).

CLI:
    python -m state.migrate validate <path>
    python -m state.migrate migrate <in> <out>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .state import SCHEMA_VERSION, DEFAULT_ORCHESTRATION


def _v1_to_v2(state: dict) -> None:
    """v1 → v2: add the orchestration-loop sections. Existing data is kept."""
    state["constraints"] = list(state.get("constraints", []))
    orch = dict(DEFAULT_ORCHESTRATION)
    orch["metrics"] = dict(DEFAULT_ORCHESTRATION["metrics"])
    # preserve any already-present v2 fields (idempotent migration)
    for k, v in state.get("orchestration", {}).items():
        if k == "metrics" and isinstance(v, dict):
            merged = dict(orch["metrics"])
            merged.update(v)
            orch["metrics"] = merged
        else:
            orch[k] = v
    state["orchestration"] = orch
    state["ledger"] = list(state.get("ledger", []))
    state["agents"] = list(state.get("agents", []))
    state["schema_version"] = 2


def migrate(state: dict) -> dict:
    """Migrate any state.json to current schema version. Returns the
    migrated state (mutates in place AND returns for convenience).
    Raises ValueError on unknown source version.
    """
    if not isinstance(state, dict):
        raise ValueError(f"state must be a dict, got {type(state).__name__}")

    v = state.get("schema_version")
    if v is None:
        # v0 → v1: just add the field
        state["schema_version"] = 1
        v = 1

    if v == 1 and SCHEMA_VERSION >= 2:
        _v1_to_v2(state)
        v = 2

    if v == SCHEMA_VERSION:
        return state

    raise ValueError(
        f"unsupported schema_version: {v}. This plugin (v1.0.0) only "
        f"understands up to v{SCHEMA_VERSION}. Run a newer plugin or "
        f"manually edit state.json."
    )


def _cmd_validate(path: Path) -> int:
    state = json.loads(path.read_text(encoding="utf-8"))
    migrate(state)
    if state.get("schema_version") != SCHEMA_VERSION:
        print(f"FAIL: still at v{state.get('schema_version')}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def _cmd_migrate(inp: Path, out: Path) -> int:
    state = json.loads(inp.read_text(encoding="utf-8"))
    migrate(state)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "validate":
        return _cmd_validate(Path(argv[1]))
    if cmd == "migrate":
        return _cmd_migrate(Path(argv[1]), Path(argv[2]))
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
