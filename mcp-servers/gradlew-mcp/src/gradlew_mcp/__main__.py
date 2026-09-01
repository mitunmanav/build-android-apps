"""gradlew-mcp: MCP server exposing gradlew to AI agents.

Phase 2b+2c slices: list_tasks, run_task, run_lint, run_tests, clean,
parse_dependencies, find_duplicate_classes.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import runner, tools as _tools, tools_phase5 as _tools_phase5

log = logging.getLogger("gradlew_mcp")

mcp = MCPServer(
    name="gradlew-mcp",
    version="0.1.0",
    instructions=(
        "Use these tools to drive a Gradle build. Always call list_tasks first to discover "
        "available tasks. run_task is long-running (Gradle can take minutes); pass a high "
        "timeout for production builds. Set `cwd` to your Android project root."
    ),
)


@mcp.tool(
    name="list_tasks",
    title="List Gradle Tasks",
    description=(
        "List all available Gradle tasks in the project (`./gradlew tasks --all`). "
        "Returns a structured list of {name, description, group}. "
        "Set `cwd` to the Android project root (defaults to $PWD). "
        "Use this before run_task to discover task names."
    ),
    annotations=ToolAnnotations(
        title="List Gradle Tasks",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
async def list_tasks(cwd: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
    try:
        result = await runner.run("tasks", "--all", cwd=cwd or ".", timeout=timeout)
    except FileNotFoundError as e:
        return {"tasks": [], "error": str(e)}
    return {
        "tasks": runner.parse_tasks(result.stdout),
        "ok": result.ok,
        "returncode": result.returncode,
    }


@mcp.tool(
    name="run_task",
    title="Run Gradle Task",
    description=(
        "Run a Gradle task (e.g. `assembleDebug`, `test`, `lint`). "
        "Returns stdout/stderr/returncode plus a 'tail' (last 50 lines) for streaming UX. "
        "Long-running: pass `timeout` in seconds (default 600 = 10 min). "
        "Note: this slice runs synchronously. Task-based progress notifications arrive in a later slice."
    ),
    annotations=ToolAnnotations(
        title="Run Gradle Task",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def run_task(
    task: str,
    args: list[str] | None = None,
    cwd: str | None = None,
    timeout: float = 600.0,
) -> dict[str, Any]:
    cmd = [task, *(args or [])]
    try:
        result = await runner.run(*cmd, cwd=cwd or ".", timeout=timeout)
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e), "task": task}
    stdout_lines = result.stdout.splitlines()
    return {
        "ok": result.ok,
        "task": task,
        "returncode": result.returncode,
        "stdout_lines": len(stdout_lines),
        "stderr_lines": len(result.stderr.splitlines()),
        "tail": "\n".join(stdout_lines[-50:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
    }


def main() -> None:
    _tools.register(mcp)
    _tools_phase5.register(mcp)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.info("gradlew-mcp stopped")


if __name__ == "__main__":
    main()
