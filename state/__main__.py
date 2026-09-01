"""state/__main__.py — CLI for state operations.

Subcommands:
    load <path>                        print state.json (or DEFAULT_STATE if missing)
    save <path> <json>                 write state.json (validates first)
    validate <path>                    exit 0 if valid, 1 otherwise
    migrate <in> <out>                 upgrade to current schema version
    add <path> --title T --phase P [--deps d1,d2] [--files f1,f2]
                                        add plan item
    remove <path> --task ID [--hard]   remove (or skip) plan item
    change <path> --task ID [--title T] [--phase P] [--deps d1,d2] [--files f1,f2]
                                        change plan item
    done <path> --task ID              mark task done + advance cursor
    start <path> --task ID             mark task in_progress
    skip <path> --task ID              mark task skipped
    undo <path>                        undo last mutation
    where <path>                       multi-line "where am I"
    continue <path>                    advance to next pending task
    summary <path>                     one-line summary
    route <path> [--affected id1,id2] show ordered phases to run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .state import SCHEMA_VERSION, load, save
from .migrate import migrate, _cmd_migrate
from .manager import StateManager, StateError
from .router import explain, route_after, route_full, detect_cycle


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="state", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_path_arg(s, help_text):
        s.add_argument("path", help=help_text)

    s = sub.add_parser("load", help="load and print state.json")
    add_path_arg(s, "path to state.json")
    s.add_argument("--default", action="store_true", help="print DEFAULT_STATE on missing file")

    s = sub.add_parser("save", help="write state.json (validates first)")
    add_path_arg(s, "path to state.json")
    s.add_argument("state_json", help="JSON string of new state")

    s = sub.add_parser("validate", help="validate state.json")
    add_path_arg(s, "path to state.json")

    s = sub.add_parser("migrate", help="migrate to current schema")
    s.add_argument("inp", help="input state.json")
    s.add_argument("out", help="output state.json")

    # mutation subcommands
    s = sub.add_parser("add", help="add plan item")
    add_path_arg(s, "path to state.json")
    s.add_argument("--title", required=True)
    s.add_argument("--phase", required=True)
    s.add_argument("--deps", default="", help="comma-separated task ids")
    s.add_argument("--files", default="", help="comma-separated file paths")
    s.add_argument("--by", default="user", choices=["user", "agent"])
    s.add_argument("--id", default=None)

    s = sub.add_parser("remove", help="remove or skip plan item")
    add_path_arg(s, "path to state.json")
    s.add_argument("--task", required=True)
    s.add_argument("--hard", action="store_true", help="delete vs mark skipped")

    s = sub.add_parser("change", help="change plan item fields")
    add_path_arg(s, "path to state.json")
    s.add_argument("--task", required=True)
    s.add_argument("--title", default=None)
    s.add_argument("--phase", default=None)
    s.add_argument("--deps", default=None, help="comma-separated (replaces)")
    s.add_argument("--files", default=None, help="comma-separated (replaces)")

    s = sub.add_parser("done", help="mark task done + advance cursor")
    add_path_arg(s, "path to state.json")
    s.add_argument("--task", required=True)

    s = sub.add_parser("start", help="mark task in_progress")
    add_path_arg(s, "path to state.json")
    s.add_argument("--task", required=True)

    s = sub.add_parser("skip", help="mark task skipped")
    add_path_arg(s, "path to state.json")
    s.add_argument("--task", required=True)

    s = sub.add_parser("undo", help="undo last mutation")
    add_path_arg(s, "path to state.json")

    for name in ("where", "continue", "summary"):
        s = sub.add_parser(name, help=f"{name} command")
        add_path_arg(s, "path to state.json")

    s = sub.add_parser("route", help="show ordered phases (Kahn's algo)")
    add_path_arg(s, "path to state.json")
    s.add_argument("--affected", default="", help="comma-separated task ids (delta-aware)")

    s = sub.add_parser("check-cycle", help="detect cycle in plan deps")
    add_path_arg(s, "path to state.json")

    return p


def _csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    path = Path(getattr(args, "path", None) or (Path.cwd() / ".build-android" / "state.json"))

    try:
        if args.cmd == "load":
            if args.default or path.exists():
                print(json.dumps(load(path), indent=2, ensure_ascii=False))
            else:
                print(f"no state.json at {path}", file=sys.stderr)
                return 1
            return 0

        if args.cmd == "save":
            state = json.loads(args.state_json)
            save(path, state)
            print(f"OK -> {path}")
            return 0

        if args.cmd == "validate":
            state = load(path)
            print(f"OK schema_version={state.get('schema_version','?')}")
            return 0

        if args.cmd == "migrate":
            return _cmd_migrate(Path(args.inp), Path(args.out))

        # mutation ops require a real file
        mgr = StateManager(path)

        if args.cmd == "add":
            item = mgr.add_task(
                title=args.title,
                phase=args.phase,
                deps=_csv(args.deps),
                files_touched=_csv(args.files),
                added_by=args.by,
                task_id=args.id,
            )
            mgr.flush()
            print(json.dumps(item, indent=2))
            return 0

        if args.cmd == "remove":
            item = mgr.remove_task(args.task, hard=args.hard)
            mgr.flush()
            print(json.dumps(item, indent=2))
            return 0

        if args.cmd == "change":
            fields = {
                "title": args.title,
                "phase": args.phase,
                "deps": _csv(args.deps) if args.deps is not None else None,
                "files_touched": _csv(args.files) if args.files is not None else None,
            }
            item = mgr.change_task(args.task, **fields)
            mgr.flush()
            print(json.dumps(item, indent=2))
            return 0

        if args.cmd == "done":
            item = mgr.mark_done(args.task)
            mgr.flush()
            print(json.dumps(item, indent=2))
            return 0

        if args.cmd == "start":
            item = mgr.mark_in_progress(args.task)
            mgr.flush()
            print(json.dumps(item, indent=2))
            return 0

        if args.cmd == "skip":
            item = mgr.mark_skipped(args.task)
            mgr.flush()
            print(json.dumps(item, indent=2))
            return 0

        if args.cmd == "undo":
            result = mgr.undo_last()
            mgr.flush()
            print(json.dumps(result, indent=2) if result else "nothing to undo")
            return 0

        if args.cmd == "where":
            print(mgr.where())
            return 0

        if args.cmd == "continue":
            result = mgr.continue_loop()
            mgr.flush()
            print(json.dumps(result, indent=2))
            return 0

        if args.cmd == "summary":
            print(mgr.summary())
            return 0

        if args.cmd == "route":
            state = mgr.state()
            if args.affected:
                affected = [x.strip() for x in args.affected.split(",") if x.strip()]
                tasks = route_after(state, affected)
                print(f"delta-aware route ({len(tasks)} tasks after {affected}):")
            else:
                tasks = route_full(state)
                print(explain(state))
                return 0
            for i, t in enumerate(tasks, 1):
                deps = f" (deps: {', '.join(t.get('deps', []))})" if t.get("deps") else ""
                print(f"  {i}. [{t['id']}] {t['title']} @ {t['phase']}{deps}")
            return 0

        if args.cmd == "check-cycle":
            state = mgr.state()
            cyc = detect_cycle(state["plan"])
            if cyc:
                print("CYCLE:", " -> ".join(cyc))
                return 1
            print("OK no cycles")
            return 0

        parser.print_help()
        return 2

    except StateError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
