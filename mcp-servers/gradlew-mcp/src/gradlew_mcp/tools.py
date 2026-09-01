"""Extra gradlew-mcp tools for Phase 4 slash commands."""

from __future__ import annotations

from typing import Any

from mcp.types import ToolAnnotations

from . import runner


def register(server) -> None:
    """Register all gradlew-mcp tools on the given MCPServer instance."""

    @server.tool(
        name="run_lint",
        title="Run Android lint",
        description=(
            "Run Android lint via `./gradlew lint` and parse the report. "
            "Returns a summary of issues grouped by severity. "
            "Pass `variant` to target a specific build variant (e.g. 'debug')."
        ),
        annotations=ToolAnnotations(
            title="Lint", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def run_lint(variant: str | None = None, cwd: str | None = None, timeout: float = 600.0) -> dict[str, Any]:
        cmd = [f"lint{variant.capitalize()}" if variant else "lint"]
        result = await runner.run(*cmd, cwd=cwd or ".", timeout=timeout)
        summary = _summarize_lint(result.stdout)
        return {
            "ok": result.ok,
            "task": cmd[0],
            "returncode": result.returncode,
            "summary": summary,
            "tail": "\n".join(result.stdout.splitlines()[-30:]),
        }

    @server.tool(
        name="run_tests",
        title="Run unit tests",
        description=(
            "Run unit tests via `./gradlew test`. Returns pass/fail counts plus "
            "the tail of test output. For instrumentation tests, use run_task directly "
            "with the connectedAndroidTest task."
        ),
        annotations=ToolAnnotations(
            title="Run Tests", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def run_tests(variant: str | None = None, cwd: str | None = None, timeout: float = 900.0) -> dict[str, Any]:
        cmd = [f"test{variant.capitalize()}UnitTest" if variant else "test"]
        result = await runner.run(*cmd, cwd=cwd or ".", timeout=timeout)
        return {
            "ok": result.ok,
            "task": cmd[0],
            "returncode": result.returncode,
            "stdout_lines": len(result.stdout.splitlines()),
            "stderr_lines": len(result.stderr.splitlines()),
            "tail": "\n".join(result.stdout.splitlines()[-50:]),
            "stderr_tail": "\n".join(result.stderr.splitlines()[-30:]),
        }

    @server.tool(
        name="clean",
        title="Clean Gradle build",
        description=(
            "Run `./gradlew clean`. Destructive: removes build/, .gradle/, all generated artifacts. "
            "Use this before a fresh build when build state is suspect."
        ),
        annotations=ToolAnnotations(
            title="Clean", read_only_hint=False, destructive_hint=True,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def clean(cwd: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
        result = await runner.run("clean", cwd=cwd or ".", timeout=timeout)
        return {
            "ok": result.ok,
            "returncode": result.returncode,
            "tail": "\n".join(result.stdout.splitlines()[-20:]),
        }

    @server.tool(
        name="parse_dependencies",
        title="Parse project dependencies",
        description=(
            "Run `./gradlew :app:dependencies` and return the parsed tree. "
            "Useful for finding duplicate class conflicts or outdated versions."
        ),
        annotations=ToolAnnotations(
            title="Dependencies", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def parse_dependencies(module: str = ":app", configuration: str = "releaseRuntimeClasspath", cwd: str | None = None, timeout: float = 300.0) -> dict[str, Any]:
        result = await runner.run(f"{module}:dependencies", "--configuration", configuration, cwd=cwd or ".", timeout=timeout)
        return {
            "ok": result.ok,
            "module": module,
            "configuration": configuration,
            "returncode": result.returncode,
            "tail": "\n".join(result.stdout.splitlines()[-100:]),
        }

    @server.tool(
        name="find_duplicate_classes",
        title="Find duplicate classes",
        description=(
            "Run `./gradlew :app:dependencies` and parse for duplicate class entries. "
            "Common cause of `Duplicate class` errors at build time."
        ),
        annotations=ToolAnnotations(
            title="Duplicate Classes", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def find_duplicate_classes(module: str = ":app", cwd: str | None = None, timeout: float = 300.0) -> dict[str, Any]:
        result = await runner.run(f"{module}:dependencies", cwd=cwd or ".", timeout=timeout)
        classes: dict[str, list[str]] = {}
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped or "---" in stripped:
                continue
            parts = stripped.split(":")
            if len(parts) >= 2 and "." in parts[0]:
                cls = parts[0].strip()
                classes.setdefault(cls, []).append(stripped)
        duplicates = {k: v for k, v in classes.items() if len(v) > 1}
        return {
            "ok": result.ok,
            "module": module,
            "duplicate_count": len(duplicates),
            "duplicates": dict(list(duplicates.items())[:50]),
        }


def _summarize_lint(stdout: str) -> dict[str, Any]:
    """Best-effort parse of `gradlew lint` output for an issue summary."""
    summary: dict[str, Any] = {"errors": 0, "warnings": 0, "issues_by_severity": {}}
    for line in stdout.splitlines():
        line = line.strip()
        if "errors and " in line and "warnings" in line:
            try:
                err_part = line.split("errors and")[0].strip().split()[-1]
                summary["errors"] = int(err_part)
                warn_part = line.split("warnings")[0].split()[-1]
                summary["warnings"] = int(warn_part)
            except (ValueError, IndexError):
                pass
        if line.endswith("errors") and line[0].isdigit():
            try:
                summary["errors"] = int(line.split()[0])
            except ValueError:
                pass
        if line.endswith("warnings") and line[0].isdigit() and "errors" not in line:
            try:
                summary["warnings"] = int(line.split()[0])
            except ValueError:
                pass
    return summary
