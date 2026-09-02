"""tests/test_state_v2.py — state.json v2 (orchestration loop sections).

Covers: v1→v2 transparent migration, loop API, metrics, staleness cap,
ledger/agents ring buffers, validation rejections.
Run: python3 -m pytest tests/ -q
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from state.manager import StateManager, StateError
from state.migrate import migrate
from state.state import DEFAULT_STATE, load, save, validate


# ---------------------------------------------------------------- helpers

def tmp_state_path(tmp_path: Path) -> Path:
    return tmp_path / "state.json"


def v1_state() -> dict:
    return {
        "schema_version": 1,
        "phase": "build",
        "plan": [
            {"id": "t1", "title": "Login screen", "status": "done", "phase": "build"},
            {"id": "t2", "title": "Streak logic", "status": "pending", "phase": "build", "deps": ["t1"]},
        ],
        "cursor": {"phase": "build", "task_id": "t1"},
        "history": [],
    }


# ---------------------------------------------------------------- migration

def test_v1_to_v2_migration_keeps_data():
    state = v1_state()
    migrate(state)
    assert state["schema_version"] == 2
    assert state["plan"][0]["title"] == "Login screen"
    assert state["cursor"]["task_id"] == "t1"
    for k in ("constraints", "orchestration", "ledger", "agents"):
        assert k in state
    validate(state)


def test_migration_is_idempotent():
    state = v1_state()
    migrate(state)
    orch_before = json.dumps(state["orchestration"])
    migrate(state)
    assert json.dumps(state["orchestration"]) == orch_before


def test_manager_auto_migrates_v1_file(tmp_path):
    p = tmp_state_path(tmp_path)
    p.write_text(json.dumps(v1_state()), encoding="utf-8")
    m = StateManager(p)
    assert m.state()["schema_version"] == 2
    assert m.state()["plan"][1]["status"] == "pending"


def test_v0_promotes_to_v2():
    state = {k: v for k, v in v1_state().items() if k != "schema_version"}
    migrate(state)
    assert state["schema_version"] == 2


def test_v3_rejected():
    state = v1_state()
    state["schema_version"] = 3
    with pytest.raises(ValueError, match="unsupported schema_version"):
        migrate(state)


# ---------------------------------------------------------------- defaults

def test_default_state_is_valid_v2():
    validate(dict(DEFAULT_STATE))


def test_manager_on_missing_file_gives_v2_defaults(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    orch = m.state()["orchestration"]
    assert orch["mode"] == "guided"
    assert orch["status"] == "idle"
    assert orch["metrics"]["tasks_done"] == 0
    assert m.state()["constraints"] == []
    assert m.state()["ledger"] == []
    assert m.state()["agents"] == []


# ---------------------------------------------------------------- loop API

def test_mode_and_status_transitions(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    m.set_mode("autopilot")
    m.set_status("running")
    assert m.state()["orchestration"]["mode"] == "autopilot"
    assert m.state()["orchestration"]["status"] == "running"
    with pytest.raises(StateError):
        m.set_mode("yolo")
    with pytest.raises(StateError):
        m.set_status("vibing")


def test_constraints_roundtrip(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    m.set_constraints(["min SDK 26", "Kotlin 2.0.21"])
    m.flush()
    m2 = StateManager(tmp_state_path(tmp_path))
    assert m2.state()["constraints"] == ["min SDK 26", "Kotlin 2.0.21"]
    with pytest.raises(StateError):
        m.set_constraints([1, 2])  # type: ignore[arg-type]


def test_ledger_append_resets_staleness(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    for _ in range(3):
        m.bump_staleness()
    m.append_ledger("t1", "Task 1: fix round 1/5 (0 addressed, 2 open)")
    assert m.state()["orchestration"]["staleness"] == 0


def test_ledger_ring_buffer_cap(tmp_path):
    from state.state import LEDGER_LIMIT
    m = StateManager(tmp_state_path(tmp_path))
    for i in range(LEDGER_LIMIT + 20):
        m.append_ledger("t1", f"Ruling: entry {i} — test — nothing")
    assert len(m.state()["ledger"]) == LEDGER_LIMIT
    assert f"entry {LEDGER_LIMIT + 19}" in m.state()["ledger"][-1]["line"]


def test_agent_log_ring_buffer_cap(tmp_path):
    from state.state import AGENT_LOG_LIMIT
    m = StateManager(tmp_state_path(tmp_path))
    for i in range(AGENT_LOG_LIMIT + 5):
        m.log_agent("implementer", "t1", "haiku", "DONE")
    assert len(m.state()["agents"]) == AGENT_LOG_LIMIT


def test_fix_round_and_task_done(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    task = m.add_task("Streak logic", "build")
    m.start_task(task["id"])
    assert m.record_fix_round(task["id"]) == 1
    assert m.record_fix_round(task["id"]) == 2
    m.mark_done(task["id"])
    m.record_task_done(task["id"], first_pass=False, ui_evidence=True)
    orch = m.state()["orchestration"]
    assert orch["metrics"]["fix_rounds_total"] == 2
    assert orch["metrics"]["tasks_done"] == 1
    assert orch["metrics"]["first_pass"] == 0
    assert orch["metrics"]["ui_tasks_total"] == 1
    assert orch["metrics"]["ui_tasks_with_evidence"] == 1
    assert orch["current_task_id"] == ""
    assert orch["fix_round"] == 0


def test_staleness_cap_records_stop(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    for _ in range(3):
        m.bump_staleness()
    m.record_staleness_stop()
    m.flush()
    m2 = StateManager(tmp_state_path(tmp_path))
    orch = m2.state()["orchestration"]
    assert orch["staleness"] == 3
    assert orch["status"] == "stopped"
    assert orch["metrics"]["staleness_stops"] == 1


def test_where_renders_loop_state(tmp_path):
    m = StateManager(tmp_state_path(tmp_path))
    task = m.add_task("Streak logic", "build")
    m.start_task(task["id"])
    m.append_ledger(task["id"], "Task 1: fix round 1/5 (0 addressed, 1 open)")
    m.set_constraints(["min SDK 26"])
    out = m.where()
    assert "loop: mode=guided" in out
    assert "recent loop activity" in out
    assert "Task 1: fix round 1/5" in out
    assert "constraints: 1" in out


def test_v1_state_still_validates_under_v1_rules():
    """A v1 document that has NOT been migrated must still be rejected by the
    v2 validator (forced upgrade path), not silently accepted."""
    state = v1_state()
    with pytest.raises(ValueError, match="schema_version"):
        validate(state)
