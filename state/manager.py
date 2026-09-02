"""state/manager.py — full plan algebra with ring-buffer history + undo.

Public API:
    StateManager(path) — load/save state.json
        .add_task(title, phase, deps=None, files_touched=None, added_by='user')
        .remove_task(task_id, hard=False)        # soft = mark skipped
        .change_task(task_id, **fields)
        .mark_in_progress(task_id)
        .mark_done(task_id)
        .mark_skipped(task_id)
        .undo_last() -> dict | None              # returns the undone entry
        .next_pending() -> dict | None           # next task to work on
        .summary() -> str                        # one-line human summary
        .where() -> str                          # multi-line "where am I"
        .continue_loop() -> dict                 # move cursor to next pending

Mutations push a history entry with a `before` snapshot (state pre-mutation)
for undo. history is a ring buffer capped at 50.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .state import load, save, validate, SCHEMA_VERSION, LEDGER_LIMIT, AGENT_LOG_LIMIT, DEFAULT_ORCHESTRATION
from .migrate import migrate as migrate_state


HISTORY_LIMIT = 50


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class StateError(Exception):
    pass


class StateManager:
    def __init__(self, path: Path):
        self.path = path
        try:
            self._state = load(path)
        except ValueError as e:
            if "schema_version" not in str(e) or not path.exists():
                raise
            # transparent v1 → v2 upgrade on first touch
            raw = json.loads(path.read_text(encoding="utf-8"))
            migrate_state(raw)
            save(path, raw)
            self._state = load(path)
        if not self._state["history"]:
            self._state["history"] = []

    # ---- core IO -----------------------------------------------------

    def flush(self) -> None:
        save(self.path, self._state)

    def state(self) -> dict:
        return self._state

    # ---- history (with snapshots) -----------------------------------

    def _push_history(self, action: str, summary: str, before: dict) -> None:
        hist = self._state.setdefault("history", [])
        hist.append({"at": _now(), "action": action, "summary": summary, "before": before})
        if len(hist) > HISTORY_LIMIT:
            # ring buffer: drop oldest (which loses its before snapshot — undo of older items is then no-op)
            del hist[0 : len(hist) - HISTORY_LIMIT]

    def _drop_last_history(self) -> None:
        hist = self._state.get("history", [])
        if hist:
            hist.pop()

    # ---- plan algebra ------------------------------------------------

    def add_task(
        self,
        title: str,
        phase: str,
        deps: list[str] | None = None,
        files_touched: list[str] | None = None,
        added_by: str = "user",
        task_id: str | None = None,
    ) -> dict:
        if not title or not phase:
            raise StateError("title and phase are required")
        if phase not in {"intake", "plan", "scaffold", "build", "test", "publish", "update"}:
            raise StateError(f"unknown phase: {phase}")
        tid = task_id or uuid.uuid4().hex[:8]
        if any(t["id"] == tid for t in self._state["plan"]):
            raise StateError(f"task id {tid!r} already exists")
        before = json.loads(json.dumps(self._state))
        item = {
            "id": tid,
            "title": title,
            "status": "pending",
            "phase": phase,
            "deps": list(deps or []),
            "files_touched": list(files_touched or []),
            "added_by": added_by,
            "added_at": _now(),
        }
        self._state["plan"].append(item)
        self._push_history("add_task", f"+ {title}", before)
        return item

    def remove_task(self, task_id: str, hard: bool = False) -> dict:
        idx = self._find(task_id)
        if idx is None:
            raise StateError(f"task id {task_id!r} not found")
        item = self._state["plan"][idx]
        before = json.loads(json.dumps(self._state))
        if hard:
            del self._state["plan"][idx]
            self._push_history("remove_task", f"- {item['title']} (hard)", before)
        else:
            self._state["plan"][idx] = {**item, "status": "skipped"}
            self._push_history("skip_task", f"- {item['title']} (skipped)", before)
            item = self._state["plan"][idx]
        return item

    def change_task(self, task_id: str, **fields: Any) -> dict:
        idx = self._find(task_id)
        if idx is None:
            raise StateError(f"task id {task_id!r} not found")
        item = self._state["plan"][idx]
        allowed = {"title", "phase", "deps", "files_touched"}
        bad = set(fields) - allowed
        if bad:
            raise StateError(f"cannot change fields: {bad}")
        fields = {k: v for k, v in fields.items() if v is not None}
        if "phase" in fields and fields["phase"] not in {"intake", "plan", "scaffold", "build", "test", "publish", "update"}:
            raise StateError(f"unknown phase: {fields['phase']}")
        before = json.loads(json.dumps(self._state))
        new = {**item, **fields}
        self._state["plan"][idx] = new
        self._push_history("change_task", f"~ {item['title']}", before)
        return self._state["plan"][idx]

    def mark_in_progress(self, task_id: str) -> dict:
        return self._transition(task_id, "in_progress")

    def mark_done(self, task_id: str) -> dict:
        out = self._transition(task_id, "done")
        if out:
            self._state["cursor"] = {"phase": out["phase"], "task_id": out["id"]}
            self._state["phase"] = out["phase"]
        return out

    def mark_skipped(self, task_id: str) -> dict:
        return self._transition(task_id, "skipped")

    def _transition(self, task_id: str, new_status: str) -> dict:
        idx = self._find(task_id)
        if idx is None:
            raise StateError(f"task id {task_id!r} not found")
        item = self._state["plan"][idx]
        if item["status"] == "done" and new_status != "done":
            raise StateError(f"task {task_id!r} is done; cannot revert")
        if new_status not in {"in_progress", "done", "skipped"}:
            raise StateError(f"invalid transition target: {new_status}")
        if item["status"] == new_status:
            return item  # idempotent
        before = json.loads(json.dumps(self._state))
        self._state["plan"][idx] = {**item, "status": new_status}
        self._push_history("status_change", f"  {item['title']} → {new_status}", before)
        return self._state["plan"][idx]

    # ---- queries -----------------------------------------------------

    def _find(self, task_id: str) -> int | None:
        for i, t in enumerate(self._state["plan"]):
            if t["id"] == task_id:
                return i
        return None

    def get_task(self, task_id: str) -> dict | None:
        idx = self._find(task_id)
        return self._state["plan"][idx] if idx is not None else None

    def next_pending(self) -> dict | None:
        """Kahn's-algorithm-lite: next pending task whose deps are all done."""
        plan = self._state["plan"]
        done_ids = {t["id"] for t in plan if t["status"] == "done"}
        for t in plan:
            if t["status"] != "pending":
                continue
            if all(dep in done_ids for dep in t.get("deps", [])):
                return t
        return None

    def summary(self) -> str:
        plan = self._state["plan"]
        total = len(plan)
        done = sum(1 for t in plan if t["status"] == "done")
        pending = sum(1 for t in plan if t["status"] == "pending")
        in_prog = sum(1 for t in plan if t["status"] == "in_progress")
        skipped = sum(1 for t in plan if t["status"] == "skipped")
        cur = self._state.get("cursor", {})
        cur_title = next(
            (t["title"] for t in plan if t["id"] == cur.get("task_id")),
            "(none)",
        )
        return (
            f"phase={self._state['phase']} cursor.task={cur_title!r} "
            f"[done={done} in_progress={in_prog} pending={pending} skipped={skipped} total={total}]"
        )

    def where(self) -> str:
        plan = self._state["plan"]
        cur = self._state.get("cursor", {})
        lines = [
            f"phase: {self._state['phase']}",
            f"cursor.task_id: {cur.get('task_id','')}",
            f"plan: {len(plan)} item(s)",
        ]
        for t in plan:
            mark = {"pending": "·", "in_progress": "▶", "done": "✓", "skipped": "✗"}[t["status"]]
            deps = f" (deps: {', '.join(t.get('deps', []))})" if t.get("deps") else ""
            lines.append(f"  {mark} [{t['id']}] {t['title']} @ {t['phase']}{deps}")
        next_p = self.next_pending()
        if next_p:
            lines.append(f"\nnext pending: [{next_p['id']}] {next_p['title']} @ {next_p['phase']}")
        else:
            lines.append("\nno pending tasks")
        orch = self._state.get("orchestration", {})
        if orch:
            lines.append(
                f"loop: mode={orch.get('mode', 'guided')} status={orch.get('status', 'idle')} "
                f"fix_round={orch.get('fix_round', 0)} staleness={orch.get('staleness', 0)}"
            )
        ledger = self._state.get("ledger", [])
        if ledger:
            lines.append("recent loop activity:")
            for entry in ledger[-5:]:
                lines.append(f"  · {entry.get('line', '')}")
        cons = self._state.get("constraints", [])
        if cons:
            lines.append(f"constraints: {len(cons)} locked from spec")
        return "\n".join(lines)

    def continue_loop(self) -> dict:
        nxt = self.next_pending()
        if not nxt:
            return {"action": "noop", "reason": "no pending tasks"}
        out = self.mark_in_progress(nxt["id"])
        return {"action": "in_progress", "task": out}

    # ---- orchestration loop (v2) --------------------------------------

    def _orch(self) -> dict:
        orch = self._state.setdefault("orchestration", dict(DEFAULT_ORCHESTRATION))
        orch.setdefault("metrics", dict(DEFAULT_ORCHESTRATION["metrics"]))
        return orch

    def set_mode(self, mode: str) -> dict:
        if mode not in ("guided", "autopilot"):
            raise StateError("mode must be 'guided' or 'autopilot'")
        before = json.loads(json.dumps(self._state))
        self._orch()["mode"] = mode
        self._push_history("set_mode", f"mode → {mode}", before)
        return self._orch()

    def set_status(self, status: str) -> dict:
        if status not in ("idle", "running", "stopped", "awaiting_user"):
            raise StateError("status must be idle|running|stopped|awaiting_user")
        before = json.loads(json.dumps(self._state))
        self._orch()["status"] = status
        self._push_history("loop_status", f"loop → {status}", before)
        return self._orch()

    def set_constraints(self, constraints: list[str]) -> list[str]:
        if not all(isinstance(c, str) for c in constraints):
            raise StateError("constraints must be strings")
        before = json.loads(json.dumps(self._state))
        self._state["constraints"] = list(constraints)
        self._push_history("set_constraints", f"{len(constraints)} constraint(s)", before)
        return self._state["constraints"]

    def append_ledger(self, task_id: str, line: str) -> dict:
        if not line:
            raise StateError("ledger line must be non-empty")
        before = json.loads(json.dumps(self._state))
        entry = {"at": _now(), "task_id": task_id, "line": line}
        ledger = self._state.setdefault("ledger", [])
        ledger.append(entry)
        if len(ledger) > LEDGER_LIMIT:
            del ledger[0 : len(ledger) - LEDGER_LIMIT]
        # any ledger append counts as forward progress
        self._orch()["staleness"] = 0
        return entry

    def log_agent(self, name: str, task_id: str, model: str, status: str) -> dict:
        before = json.loads(json.dumps(self._state))
        entry = {"at": _now(), "name": name, "task_id": task_id, "model": model, "status": status}
        agents = self._state.setdefault("agents", [])
        agents.append(entry)
        if len(agents) > AGENT_LOG_LIMIT:
            del agents[0 : len(agents) - AGENT_LOG_LIMIT]
        return entry

    def bump_staleness(self) -> int:
        """Call once per loop step that produced NO state advance.
        Orchestrator stops (cap 3) when this returns >= 3."""
        orch = self._orch()
        orch["staleness"] = int(orch.get("staleness", 0)) + 1
        return orch["staleness"]

    def reset_staleness(self) -> int:
        self._orch()["staleness"] = 0
        return 0

    def start_task(self, task_id: str) -> dict:
        """Mark in_progress + record loop focus (idempotent per task)."""
        out = self.mark_in_progress(task_id)
        orch = self._orch()
        if orch.get("current_task_id") != task_id:
            orch["current_task_id"] = task_id
            orch["fix_round"] = 0
        return out

    def record_fix_round(self, task_id: str) -> int:
        """Increment fix_round for the current task; returns new round (1-based)."""
        orch = self._orch()
        if orch.get("current_task_id") != task_id:
            orch["current_task_id"] = task_id
            orch["fix_round"] = 0
        orch["fix_round"] = int(orch.get("fix_round", 0)) + 1
        orch["metrics"]["fix_rounds_total"] = int(orch["metrics"].get("fix_rounds_total", 0)) + 1
        return orch["fix_round"]

    def record_task_done(self, task_id: str, first_pass: bool = True, ui_evidence: bool | None = None) -> dict:
        """Metrics + completion bookkeeping. Call AFTER mark_done."""
        orch = self._orch()
        m = orch["metrics"]
        m["tasks_done"] = int(m.get("tasks_done", 0)) + 1
        if first_pass:
            m["first_pass"] = int(m.get("first_pass", 0)) + 1
        if ui_evidence is not None:
            m["ui_tasks_total"] = int(m.get("ui_tasks_total", 0)) + 1
            if ui_evidence:
                m["ui_tasks_with_evidence"] = int(m.get("ui_tasks_with_evidence", 0)) + 1
        orch["fix_round"] = 0
        orch["current_task_id"] = ""
        orch["staleness"] = 0
        self._state["cursor"] = {"phase": self._state["phase"], "task_id": ""}
        return orch

    def record_staleness_stop(self) -> None:
        orch = self._orch()
        orch["status"] = "stopped"
        orch["metrics"]["staleness_stops"] = int(orch["metrics"].get("staleness_stops", 0)) + 1

    # ---- undo --------------------------------------------------------

    def undo_last(self) -> dict | None:
        hist = self._state.get("history", [])
        if not hist:
            return None
        # Skip past undo markers to find the most recent real mutation
        idx = None
        for i in range(len(hist) - 1, -1, -1):
            if hist[i].get("before") is not None:
                idx = i
                break
        if idx is None:
            return {"action": "noop", "reason": "no undoable mutations in history"}
        entry = hist[idx]
        before = entry["before"]
        marker = {k: v for k, v in entry.items() if k != "before"}
        marker["undone"] = True
        marker["undone_at"] = _now()
        # Restore pre-mutation state — its history lacks the entry at idx
        hist.pop(idx)
        hist.append(marker)
        self._state = json.loads(json.dumps(before))
        self._state["schema_version"] = SCHEMA_VERSION
        self._state["history"] = hist
        return {"action": "undone", "entry": marker}
