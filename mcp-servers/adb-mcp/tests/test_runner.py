"""Tests for the async adb subprocess wrapper (runner.py).

We never invoke a real adb process. We monkey-patch `runner.find_adb`
to return a script that echoes its argv and exit code, so we can
verify command construction, stdout/stderr capture, and timeout behavior.
"""

from __future__ import annotations

import asyncio
import os
import stat
from pathlib import Path

import pytest

from adb_mcp import runner


@pytest.fixture
def fake_adb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fake `adb` binary in tmp_path and patch find_adb to return it."""
    bin_path = tmp_path / "adb"
    bin_path.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "# Echo argv lines as 'arg=<value>' for easy assertions.\n"
        "for i, a in enumerate(sys.argv[1:]):\n"
        "    sys.stdout.write(f'arg{i}={a}\\n')\n"
        "# Exit non-zero if ARGV contains 'fail' so we can test error paths.\n"
        "if 'fail' in sys.argv:\n"
        "    sys.stderr.write('intentional failure\\n')\n"
        "    sys.exit(7)\n"
    )
    bin_path.chmod(bin_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    monkeypatch.setattr(runner, "find_adb", lambda: str(bin_path))
    return bin_path


async def test_run_captures_stdout(fake_adb: Path) -> None:
    result = await runner.run("devices", "-l")
    assert result.ok
    assert result.returncode == 0
    assert "arg0=devices" in result.stdout
    assert "arg1=-l" in result.stdout


async def test_run_passes_device_serial(fake_adb: Path) -> None:
    result = await runner.run("shell", "echo hi", device="emulator-5554")
    assert result.ok
    assert "arg0=-s" in result.stdout
    assert "arg1=emulator-5554" in result.stdout
    assert "arg2=shell" in result.stdout


async def test_run_returns_nonzero(fake_adb: Path) -> None:
    result = await runner.run("fail")
    assert not result.ok
    assert result.returncode == 7
    assert "intentional failure" in result.stderr


async def test_run_raises_on_nonzero(fake_adb: Path) -> None:
    result = await runner.run("fail")
    assert not result.ok
    with pytest.raises(runner.AdbError) as ei:
        result.raise_for_status()
    assert ei.value.returncode == 7
    assert "intentional failure" in str(ei.value)


async def test_run_timeout_raises(fake_adb: Path) -> None:
    bin_path = fake_adb
    bin_path.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, time\n"
        "time.sleep(5)\n"
    )
    bin_path.chmod(bin_path.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(runner.AdbError) as ei:
        await runner.run("devices", timeout=0.2)
    assert "timeout" in str(ei.value).lower()


def test_parse_devices_basic() -> None:
    sample = (
        "List of devices attached\n"
        "emulator-5554   device product:sdk_gphone64_x86_64 model:Android_SDK_built_for_x86_64 device:emu64xa transport_id:1\n"
        "0123456789ABCDEF    unauthorized\n"
    )
    devices = runner.parse_devices(sample)
    assert len(devices) == 2
    assert devices[0].serial == "emulator-5554"
    assert devices[0].state == "device"
    assert devices[0].model == "Android_SDK_built_for_x86_64"
    assert devices[0].product == "sdk_gphone64_x86_64"
    assert devices[1].serial == "0123456789ABCDEF"
    assert devices[1].state == "unauthorized"


def test_parse_devices_empty() -> None:
    assert runner.parse_devices("List of devices attached\n\n") == []


def test_find_adb_prefers_android_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    adb_in_sdk = tmp_path / "platform-tools" / "adb"
    adb_in_sdk.parent.mkdir(parents=True)
    adb_in_sdk.write_text("#!/bin/sh\n")
    adb_in_sdk.chmod(0o755)
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path))
    assert runner.find_adb() == str(adb_in_sdk)


def test_find_adb_falls_back_to_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    adb = tmp_path / "adb"
    adb.write_text("#!/bin/sh\n")
    adb.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ.get('PATH', '')}")
    assert runner.find_adb() == str(adb)


def test_find_adb_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        runner.find_adb()
