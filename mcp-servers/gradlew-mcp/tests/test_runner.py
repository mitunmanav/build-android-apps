"""Tests for the async gradlew subprocess wrapper (runner.py).

We never invoke a real gradlew. We create a fake `gradlew` shell script in tmp_path
and patch `runner.find_gradlew` to return it. This lets us verify command construction,
argument passing, environment propagation, and timeout behavior.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from gradlew_mcp import runner


@pytest.fixture
def fake_gradle_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fake gradlew script + Android project skeleton, patch find_gradlew."""
    project = tmp_path / "proj"
    project.mkdir()
    script = project / "gradlew"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "for i, a in enumerate(sys.argv[1:]):\n"
        "    sys.stdout.write(f'arg{i}={a}\\n')\n"
        "sys.stdout.write(f'JAVA_HOME={os.environ.get(\"JAVA_HOME\", \"unset\")}\\n')\n"
        "sys.stdout.write(f'CWD={os.getcwd()}\\n')\n"
        "if 'fail' in sys.argv:\n"
        "    sys.stderr.write('gradle failed\\n')\n"
        "    sys.exit(13)\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    monkeypatch.setattr(runner, "find_gradlew", lambda cwd=None: script)
    return project


async def test_run_basic(fake_gradle_project: Path) -> None:
    result = await runner.run("tasks", "--all", cwd=str(fake_gradle_project))
    assert result.ok
    assert result.returncode == 0
    assert "arg0=tasks" in result.stdout
    assert "arg1=--all" in result.stdout


async def test_run_passes_cwd(fake_gradle_project: Path) -> None:
    result = await runner.run("assembleDebug", cwd=str(fake_gradle_project))
    assert f"CWD={fake_gradle_project}" in result.stdout


async def test_run_propagates_java_home(fake_gradle_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JAVA_HOME", "/opt/jdk17")
    result = await runner.run("assembleDebug", cwd=str(fake_gradle_project))
    assert "JAVA_HOME=/opt/jdk17" in result.stdout


async def test_run_java_home_override(fake_gradle_project: Path) -> None:
    result = await runner.run(
        "assembleDebug", cwd=str(fake_gradle_project), java_home="/opt/jdk21"
    )
    assert "JAVA_HOME=/opt/jdk21" in result.stdout


async def test_run_returns_nonzero(fake_gradle_project: Path) -> None:
    result = await runner.run("fail", cwd=str(fake_gradle_project))
    assert not result.ok
    assert result.returncode == 13
    assert "gradle failed" in result.stderr


async def test_run_timeout_raises(fake_gradle_project: Path) -> None:
    script = fake_gradle_project / "gradlew"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import time\n"
        "time.sleep(5)\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(runner.GradleError) as ei:
        await runner.run("tasks", cwd=str(fake_gradle_project), timeout=0.2)
    assert "timeout" in str(ei.value).lower()


def test_find_gradlew_walks_up(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (tmp_path / "gradlew").write_text("#!/bin/sh\n")
    (tmp_path / "gradlew").chmod(0o755)
    assert runner.find_gradlew(nested) == tmp_path / "gradlew"


def test_find_gradlew_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        runner.find_gradlew(tmp_path)


def test_parse_tasks_extracts_names_and_groups() -> None:
    sample = """
> Task :tasks

------------------------------------------------------------
Tasks runnable from root project 'myapp'
------------------------------------------------------------

Application tasks
-----------------
assemble - Assembles the outputs of this project.
build - Assembles and tests this project.
clean - Deletes the build directory.

Build tasks
-----------
assembleDebug - Assembles main output for debug variant.
assembleRelease - Assembles main output for release variant.

Documentation tasks
-------------------
javadoc - Generates Javadoc API documentation.
"""
    tasks = runner.parse_tasks(sample)
    names = {t["name"] for t in tasks}
    assert "assemble" in names
    assert "build" in names
    assert "assembleDebug" in names
    assert "javadoc" in names
    by_name = {t["name"]: t for t in tasks}
    assert by_name["assemble"]["description"] == "Assembles the outputs of this project."
    assert by_name["assembleDebug"]["group"] == "Build tasks"


def test_parse_tasks_ignores_banner() -> None:
    sample = """
BUILD SUCCESSFUL in 2s
1 actionable task: 1 executed

> Task :tasks
"""
    assert runner.parse_tasks(sample) == []
