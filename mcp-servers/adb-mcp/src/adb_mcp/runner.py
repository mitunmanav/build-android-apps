"""Async subprocess wrapper for adb."""

from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


def find_adb() -> str:
    """Locate the adb binary.

    Prefers `${ANDROID_HOME}/platform-tools/adb`; falls back to PATH.
    Raises FileNotFoundError if neither resolves.
    """
    android_home = os.environ.get("ANDROID_HOME")
    if android_home:
        candidate = Path(android_home) / "platform-tools" / "adb"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    on_path = shutil.which("adb")
    if on_path:
        return on_path
    raise FileNotFoundError(
        "adb not found. Set ANDROID_HOME or add `adb` to PATH. "
        "Install via Android SDK or `brew install android-platform-tools`."
    )


@dataclass(frozen=True, slots=True)
class AdbResult:
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def raise_for_status(self) -> None:
        if not self.ok:
            raise AdbError(self.returncode, self.stderr.strip() or self.stdout.strip())

    def lines(self) -> list[str]:
        return [line for line in self.stdout.splitlines() if line.strip()]


class AdbError(RuntimeError):
    def __init__(self, returncode: int, message: str) -> None:
        super().__init__(f"adb exited {returncode}: {message}")
        self.returncode = returncode
        self.message = message


def build_cmd(*args: str, device: str | None = None) -> list[str]:
    """Build an adb command, prepending `-s <device>` if a serial is given."""
    cmd = [find_adb()]
    if device:
        cmd += ["-s", device]
    cmd += list(args)
    return cmd


async def run(*args: str, device: str | None = None, timeout: float = 30.0) -> AdbResult:
    """Run an adb command asynchronously with a timeout (seconds).

    Returns AdbResult; caller decides whether to raise on non-zero exit.
    """
    cmd = build_cmd(*args, device=device)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise AdbError(-1, f"adb timeout after {timeout}s: {' '.join(cmd)}")
    return AdbResult(
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        returncode=proc.returncode if proc.returncode is not None else -1,
    )


@dataclass(frozen=True, slots=True)
class Device:
    serial: str
    state: str
    model: str | None
    product: str | None
    transport: str | None

    def to_dict(self) -> dict:
        return {
            "serial": self.serial,
            "state": self.state,
            "model": self.model,
            "product": self.product,
            "transport": self.transport,
        }


def parse_devices(stdout: str) -> list[Device]:
    """Parse `adb devices -l` output into Device objects."""
    devices: list[Device] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        attrs: dict[str, str] = {}
        for token in parts[2:]:
            if ":" in token:
                k, v = token.split(":", 1)
                attrs[k] = v
        devices.append(
            Device(
                serial=serial,
                state=state,
                model=attrs.get("model"),
                product=attrs.get("product"),
                transport=attrs.get("transport_id"),
            )
        )
    return devices
