"""Extra adb-mcp tools.

Adds: shell_command, start_activity, logcat_dump, logcat_clear, screencap,
pull_file, push_file, getprop, setprop, wait_for_device, uninstall_app,
clear_app_data, stop_app, unzip.
"""

from __future__ import annotations

import asyncio
import base64
import re
from pathlib import Path
from typing import Any

from mcp.types import ToolAnnotations

from . import runner

_ANSI_RE = re.compile(rb"\x1b\[[0-9;]*m")


def register(server) -> None:
    """Register all adb-mcp tools on the given MCPServer instance."""

    @server.tool(
        name="shell_command",
        title="Run adb shell command",
        description=(
            "Run an `adb shell <command>` on a connected device. "
            "Returns stdout, stderr, returncode. "
            "Use for dumpsys, getprop, pm, am, ls, cat — anything you'd run interactively."
        ),
        annotations=ToolAnnotations(
            title="adb shell", read_only_hint=False, destructive_hint=False,
            idempotent_hint=False, open_world_hint=True,
        ),
    )
    async def shell_command(command: str, device: str | None = None, timeout: float = 30.0) -> dict[str, Any]:
        result = await runner.run("shell", command, device=device, timeout=timeout)
        return {
            "ok": result.ok,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    @server.tool(
        name="start_activity",
        title="Start an Android Activity",
        description=(
            "Launch an activity via `am start`. Pass either `component` (e.g. "
            "`com.example/.MainActivity`) or `action` + optional `data` URI. "
            "Use this to bring the app to the foreground or open a deeplink."
        ),
        annotations=ToolAnnotations(
            title="Start Activity", read_only_hint=False, destructive_hint=False,
            idempotent_hint=False, open_world_hint=True,
        ),
    )
    async def start_activity(
        component: str | None = None,
        action: str | None = None,
        data: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any]:
        cmd = ["am", "start"]
        if action:
            cmd += ["-a", action]
        if data:
            cmd += ["-d", data]
        if component:
            cmd.append(component)
        result = await runner.run(*cmd, device=device)
        return {
            "ok": result.ok,
            "returncode": result.returncode,
            "output": (result.stdout.strip() or result.stderr.strip()),
        }

    @server.tool(
        name="stop_app",
        title="Force-stop an app",
        description="Force-stop an app via `am force-stop <package>`. Idempotent.",
        annotations=ToolAnnotations(
            title="Stop App", read_only_hint=False, destructive_hint=True,
            idempotent_hint=True, open_world_hint=True,
        ),
    )
    async def stop_app(package: str, device: str | None = None) -> dict[str, Any]:
        result = await runner.run("shell", "am", "force-stop", package, device=device)
        return {"ok": result.ok, "returncode": result.returncode, "package": package}

    @server.tool(
        name="uninstall_app",
        title="Uninstall an app",
        description="Uninstall an app via `adb uninstall <package>`. Destructive: removes app + data.",
        annotations=ToolAnnotations(
            title="Uninstall App", read_only_hint=False, destructive_hint=True,
            idempotent_hint=False, open_world_hint=True,
        ),
    )
    async def uninstall_app(package: str, device: str | None = None) -> dict[str, Any]:
        result = await runner.run("uninstall", package, device=device)
        return {"ok": result.ok, "package": package, "output": (result.stdout.strip() or result.stderr.strip())}

    @server.tool(
        name="clear_app_data",
        title="Clear app data",
        description="Clear an app's data via `pm clear <package>`. Destructive: wipes all app state.",
        annotations=ToolAnnotations(
            title="Clear App Data", read_only_hint=False, destructive_hint=True,
            idempotent_hint=True, open_world_hint=True,
        ),
    )
    async def clear_app_data(package: str, device: str | None = None) -> dict[str, Any]:
        result = await runner.run("shell", "pm", "clear", package, device=device)
        return {"ok": result.ok, "package": package, "output": result.stdout.strip()}

    @server.tool(
        name="logcat_dump",
        title="Dump logcat",
        description=(
            "Dump current logcat via `adb logcat -d`. Filter by `tag` (substring match) "
            "and `level` (V/D/I/W/E). Use `since` to scope to recent lines (e.g. 'boot', '1h'). "
            "For long sessions, prefer the logcat_filter resource (subscribable)."
        ),
        annotations=ToolAnnotations(
            title="Logcat Dump", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def logcat_dump(
        tag: str | None = None,
        level: str | None = None,
        since: str | None = None,
        max_lines: int = 500,
        device: str | None = None,
    ) -> dict[str, Any]:
        cmd = ["logcat", "-d"]
        if since:
            cmd += ["-T", since]
        if tag and level:
            cmd += [f"{tag}:{level}"]
        elif level:
            cmd += [f"*:{level}"]
        elif tag:
            cmd += [f"{tag}:V"]
        result = await runner.run(*cmd, device=device, timeout=60.0)
        lines = result.stdout.splitlines()
        tail = lines[-max_lines:]
        return {
            "ok": result.ok,
            "lines": len(lines),
            "tail": tail,
            "truncated": len(lines) > max_lines,
        }

    @server.tool(
        name="logcat_clear",
        title="Clear logcat buffer",
        description="Clear the logcat ring buffer via `adb logcat -c`. Destructive.",
        annotations=ToolAnnotations(
            title="Clear Logcat", read_only_hint=False, destructive_hint=True,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def logcat_clear(device: str | None = None) -> dict[str, Any]:
        result = await runner.run("logcat", "-c", device=device)
        return {"ok": result.ok, "returncode": result.returncode}

    @server.tool(
        name="screencap",
        title="Capture device screenshot",
        description=(
            "Capture the device screen as PNG. Returns base64-encoded PNG data and dimensions. "
            "Use the result directly or save via shell_command with base64 decode."
        ),
        annotations=ToolAnnotations(
            title="Screenshot", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def screencap(device: str | None = None) -> dict[str, Any]:
        cmd = ["exec-out", "screencap", "-p"]
        proc = await asyncio.create_subprocess_exec(
            runner.find_adb(), *(["-s", device] if device else []), *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
        if proc.returncode != 0:
            return {"ok": False, "error": stderr.decode("utf-8", errors="replace")}
        return {
            "ok": True,
            "encoding": "base64",
            "data": base64.b64encode(stdout).decode("ascii"),
            "size_bytes": len(stdout),
        }

    @server.tool(
        name="pull_file",
        title="Pull file from device",
        description="Pull a file from the device via `adb pull <remote> <local>`.",
        annotations=ToolAnnotations(
            title="Pull File", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def pull_file(remote_path: str, local_path: str, device: str | None = None) -> dict[str, Any]:
        Path(local_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        result = await runner.run("pull", remote_path, local_path, device=device)
        return {
            "ok": result.ok,
            "remote_path": remote_path,
            "local_path": local_path,
            "output": (result.stdout.strip() or result.stderr.strip()),
        }

    @server.tool(
        name="push_file",
        title="Push file to device",
        description="Push a file from the host to the device via `adb push <local> <remote>`.",
        annotations=ToolAnnotations(
            title="Push File", read_only_hint=False, destructive_hint=True,
            idempotent_hint=False, open_world_hint=False,
        ),
    )
    async def push_file(local_path: str, remote_path: str, device: str | None = None) -> dict[str, Any]:
        if not Path(local_path).expanduser().is_file():
            return {"ok": False, "error": f"local file not found: {local_path}"}
        result = await runner.run("push", local_path, remote_path, device=device)
        return {
            "ok": result.ok,
            "local_path": local_path,
            "remote_path": remote_path,
            "output": (result.stdout.strip() or result.stderr.strip()),
        }

    @server.tool(
        name="getprop",
        title="Read system property",
        description="Read an Android system property via `getprop <name>`. Returns the value or empty string.",
        annotations=ToolAnnotations(
            title="getprop", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def getprop(name: str, device: str | None = None) -> dict[str, Any]:
        result = await runner.run("shell", "getprop", name, device=device)
        return {"name": name, "value": result.stdout.strip(), "ok": result.ok}

    @server.tool(
        name="setprop",
        title="Set system property",
        description="Set an Android system property via `setprop <name> <value>`. Requires root or sysapp signature.",
        annotations=ToolAnnotations(
            title="setprop", read_only_hint=False, destructive_hint=True,
            idempotent_hint=False, open_world_hint=False,
        ),
    )
    async def setprop(name: str, value: str, device: str | None = None) -> dict[str, Any]:
        result = await runner.run("shell", "setprop", name, value, device=device)
        return {"ok": result.ok, "name": name, "value": value}

    @server.tool(
        name="wait_for_device",
        title="Wait for device",
        description=(
            "Block until the device is ready (boot complete + adb authorized). "
            "Returns when the device responds to `getprop sys.boot_completed`."
        ),
        annotations=ToolAnnotations(
            title="Wait for Device", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def wait_for_device(timeout: float = 120.0, device: str | None = None) -> dict[str, Any]:
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            result = await runner.run("shell", "getprop", "sys.boot_completed", device=device)
            if result.ok and result.stdout.strip() == "1":
                return {"ready": True, "waited_sec": timeout - (deadline - asyncio.get_event_loop().time())}
            await asyncio.sleep(1.0)
        return {"ready": False, "error": f"device not ready after {timeout}s"}

    @server.tool(
        name="unzip",
        title="Extract zip on host",
        description=(
            "Helper: extract a zip file on the host (used to unpack a pulled crash report bundle). "
            "Returns the list of extracted paths."
        ),
        annotations=ToolAnnotations(
            title="Unzip", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def unzip(zip_path: str, dest: str | None = None) -> dict[str, Any]:
        zp = Path(zip_path).expanduser()
        if not zp.is_file():
            return {"ok": False, "error": f"zip not found: {zp}"}
        dest_p = Path(dest).expanduser() if dest else zp.parent / (zp.stem + "_extracted")
        dest_p.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            "unzip", "-o", str(zp), "-d", str(dest_p),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        files = sorted(p.relative_to(dest_p).as_posix() for p in dest_p.rglob("*") if p.is_file())
        return {
            "ok": proc.returncode == 0,
            "dest": str(dest_p),
            "files": files,
            "stderr": stderr.decode("utf-8", errors="replace") if proc.returncode != 0 else "",
        }
