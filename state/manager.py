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

from .state import load, save, validate, SCHEMA_VERSION


HISTORY_LIMIT = 50


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class StateError(Exception):
    pass


class StateManager:
    def __init__(self, path: Path):
        self.path = path
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
        return "\n".join(lines)

    def continue_loop(self) -> dict:
        nxt = self.next_pending()
        if not nxt:
            return {"action": "noop", "reason": "no pending tasks"}
        out = self.mark_in_progress(nxt["id"])
        return {"action": "in_progress", "task": out}

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
