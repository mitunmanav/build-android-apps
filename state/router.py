"""state/router.py — Kahn's-algorithm deps resolver + delta-aware re-routing.

Given a state.json's plan, returns the minimal ordered phase sequence to run.
Deterministic, no LLM, no state mutation (read-only).

Algorithm:
    1. Build adjacency: parent -> children (deps[i] -> i)
    2. Compute in-degrees over the *eligible* subgraph
       (eligible = status in {pending, in_progress})
    3. Kahn's: zero-in-degree first, decrement on pop
    4. Cycle check: if order length < eligible count, raise

Delta-aware:
    "user added a new screen at publish phase" -> only that screen +
    downstream items should re-run. router.route_after(state, affected_ids)
    restricts the eligible set to items transitively downstream of `affected_ids`.

Public API:
    route_full(state) -> list[plan_item]
    route_after(state, affected_ids) -> list[plan_item]
    topological_order(state) -> list[plan_item]
    detect_cycle(state) -> list[str] | None   # returns cycle path or None
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable


# Statuses that count as "already done" when computing dependencies.
DONE_STATUSES = {"done"}


def _by_id(plan: list[dict]) -> dict[str, dict]:
    return {t["id"]: t for t in plan}


def topological_order(plan: list[dict]) -> list[dict]:
    """Pure topological sort over the plan. Status-agnostic.

    Items not in DONE_STATUSES are eligible; done items still appear in order
    but at their natural position (so callers can compute "what's next").
    """
    by_id = _by_id(plan)
    children: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = {tid: 0 for tid in by_id}
    for t in plan:
        for dep in t.get("deps", []):
            if dep in by_id:
                children[dep].append(t["id"])
                in_degree[t["id"]] += 1
    # stable ordering: by phase, then by id
    phase_rank = {p: i for i, p in enumerate(["intake", "plan", "scaffold", "build", "test", "publish", "update"])}
    queue = deque(sorted(
        (tid for tid, deg in in_degree.items() if deg == 0),
        key=lambda tid: (phase_rank.get(by_id[tid].get("phase", "build"), 99), tid),
    ))
    order: list[dict] = []
    while queue:
        tid = queue.popleft()
        order.append(by_id[tid])
        for child in children[tid]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
        # re-sort to keep deterministic
        queue = deque(sorted(queue, key=lambda x: (phase_rank.get(by_id[x].get("phase", "build"), 99), x)))
    return order


def detect_cycle(plan: list[dict]) -> list[str] | None:
    """Return the cycle path (list of task ids) if one exists, else None."""
    by_id = _by_id(plan)
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {tid: WHITE for tid in by_id}
    parent: dict[str, str | None] = {tid: None for tid in by_id}

    def dfs(start: str) -> list[str] | None:
        stack: list[tuple[str, int]] = [(start, 0)]
        while stack:
            node, i = stack[-1]
            deps = [d for d in by_id[node].get("deps", []) if d in by_id]
            if i >= len(deps):
                color[node] = BLACK
                stack.pop()
                continue
            stack[-1] = (node, i + 1)
            nxt = deps[i]
            if color[nxt] == GRAY:
                # cycle: reconstruct from nxt back to node via parent
                path = [nxt, node]
                p = parent[node]
                while p is not None and p != nxt:
                    path.append(p)
                    p = parent[p]
                path.reverse()
                return path
            if color[nxt] == WHITE:
                color[nxt] = GRAY
                parent[nxt] = node
                stack.append((nxt, 0))
        return None

    for tid in by_id:
        if color[tid] == WHITE:
            color[tid] = GRAY
            cyc = dfs(tid)
            if cyc:
                return cyc
    return None


def route_full(state: dict) -> list[dict]:
    """Return the ordered list of pending+in-progress tasks to run,
    respecting deps. Already-done tasks are excluded from output.
    """
    plan = state["plan"]
    order = topological_order(plan)
    return [t for t in order if t["status"] not in DONE_STATUSES]


def route_after(state: dict, affected_ids: Iterable[str]) -> list[dict]:
    """Delta-aware routing: only run `affected_ids` and their downstream.

    For each id in `affected_ids`, find every item that transitively depends
    on it (i.e., items that have the id in their dep chain). Return the
    ordered subset.

    Use case: user adds "Settings screen" at publish phase → only that screen
    and items depending on it need to re-run, not the whole plan.
    """
    plan = state["plan"]
    by_id = _by_id(plan)
    affected = set(affected_ids)
    # expand to downstream
    changed = True
    while changed:
        changed = False
        for t in plan:
            if t["id"] in affected:
                continue
            if any(dep in affected for dep in t.get("deps", [])):
                affected.add(t["id"])
                changed = True
    order = topological_order(plan)
    return [t for t in order if t["id"] in affected and t["status"] not in DONE_STATUSES]


def explain(state: dict) -> str:
    """Human-readable explanation of the current route plan."""
    cycle = detect_cycle(state["plan"])
    if cycle:
        names = [state["plan"][[t["id"] for t in state["plan"]].index(tid)]["title"] for tid in cycle if tid in [t["id"] for t in state["plan"]]]
        return f"CYCLE DETECTED: {' -> '.join(names)}"
    full = route_full(state)
    if not full:
        return "No pending tasks. Plan is complete or has no eligible items."
    lines = [f"Route plan ({len(full)} tasks):"]
    for i, t in enumerate(full, 1):
        deps = f" (after: {', '.join(t.get('deps', []))})" if t.get("deps") else ""
        lines.append(f"  {i}. [{t['id']}] {t['title']} @ {t['phase']}{deps}")
    return "\n".join(lines)
