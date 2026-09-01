"""Async subprocess wrapper for ./gradlew."""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path


def find_gradlew(cwd: str | Path) -> Path:
    """Locate the gradlew script in or above `cwd`.

    Raises FileNotFoundError if not found. Excludes the `gradlew.bat` shim
    on non-Windows platforms (and vice versa on Windows).
    """
    candidates = ("gradlew", "gradlew.bat" if os.name == "nt" else None)
    p = Path(cwd).resolve()
    for base in (p, *p.parents):
        for name in candidates:
            if not name:
                continue
            cand = base / name
            if cand.is_file():
                return cand
    raise FileNotFoundError(
        f"No gradlew script found at or above {p}. "
        "Run this tool from an Android project root or pass `cwd` pointing at one."
    )


@dataclass(frozen=True, slots=True)
class GradleResult:
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def raise_for_status(self) -> None:
        if not self.ok:
            raise GradleError(self.returncode, self.stderr.strip() or self.stdout.strip())


class GradleError(RuntimeError):
    def __init__(self, returncode: int, message: str) -> None:
        super().__init__(f"gradlew exited {returncode}: {message}")
        self.returncode = returncode
        self.message = message


async def run(
    *args: str,
    cwd: str | Path | None = None,
    timeout: float = 600.0,
    java_home: str | None = None,
) -> GradleResult:
    """Run a Gradle command asynchronously.

    `cwd` defaults to $PWD. `java_home` defaults to $JAVA_HOME.
    `timeout` defaults to 10 minutes (Gradle is slow).
    """
    cwd = Path(cwd).resolve() if cwd else Path.cwd()
    script = find_gradlew(cwd)
    env = os.environ.copy()
    if java_home:
        env["JAVA_HOME"] = java_home
    cmd = [str(script), *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise GradleError(-1, f"gradlew timeout after {timeout}s: {' '.join(cmd)}")
    return GradleResult(
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        returncode=proc.returncode if proc.returncode is not None else -1,
    )


_TASK_LINE = re.compile(r"^(?P<name>[a-zA-Z][\w:.-]*)\s+-\s+(?P<desc>.+?)\s*$")
_DASH_LINE = re.compile(r"^-+$")


def parse_tasks(stdout: str) -> list[dict[str, str]]:
    """Parse `./gradlew tasks --all` output into structured records.

    Returns a list of {"name": ..., "description": ..., "group": ...}.
    Skips header lines, blank lines, and section dividers.

    Parsing strategy: scan line by line. A line that ends with "tasks"
    AND is followed by a dashes divider is a group header. Anything matching
    the "<name> - <description>" pattern between dividers is a task in the
    most recent group.
    """
    lines = stdout.splitlines()
    tasks: list[dict[str, str]] = []
    current_group = ""
    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith(("BUILD ", "Starting a Gradle", "Daemon", "Welcome to", ">", "$", "Configure project")):
            continue
        if (
            line.endswith(" tasks")
            and i + 1 < len(lines)
            and _DASH_LINE.match(lines[i + 1].strip())
        ):
            current_group = line.strip()
            continue
        if " - " in line and not line.startswith(" "):
            m = _TASK_LINE.match(line)
            if m:
                tasks.append({
                    "name": m.group("name").strip(),
                    "description": m.group("desc").strip(),
                    "group": current_group,
                })
    return tasks
