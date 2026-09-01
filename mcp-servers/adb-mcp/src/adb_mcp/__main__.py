"""adb-mcp: MCP server exposing adb to AI agents.

Phase 2a+2c slices: list_devices, select_device, install_apk, shell_command,
start_activity, stop_app, uninstall_app, clear_app_data, logcat_dump, logcat_clear,
screencap, pull_file, push_file, getprop, setprop, wait_for_device, dump_layout, unzip.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import runner, tools as _tools

log = logging.getLogger("adb_mcp")

mcp = MCPServer(
    name="adb-mcp",
    version="0.1.0",
    instructions=(
        "Use these tools to drive an Android device via adb. "
        "Always call list_devices first to confirm what's connected; "
        "if more than one device is connected, call select_device before install or shell."
    ),
)


@mcp.tool(
    name="list_devices",
    title="List ADB Devices",
    description=(
        "List all devices and emulators visible to `adb devices -l`. "
        "Returns an empty list if nothing is connected. Use this before any device-specific operation."
    ),
    annotations=ToolAnnotations(
        title="List ADB Devices",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
async def list_devices() -> dict[str, Any]:
    try:
        result = await runner.run("devices", "-l")
    except FileNotFoundError as e:
        return {"devices": [], "error": str(e)}
    devices = runner.parse_devices(result.stdout)
    return {"devices": [d.to_dict() for d in devices]}


@mcp.tool(
    name="select_device",
    title="Select Device from List",
    description=(
        "Pick a device serial from a list of devices. "
        "If `serial` is provided and matches a connected device, returns it. "
        "If only one device is connected, returns it automatically. "
        "If zero or multiple devices are connected and `serial` is not provided, "
        "returns the full list so the caller can disambiguate."
    ),
    annotations=ToolAnnotations(
        title="Select Device",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
async def select_device(serial: str | None = None) -> dict[str, Any]:
    result = await runner.run("devices", "-l")
    devices = runner.parse_devices(result.stdout)
    if not devices:
        return {"devices": [], "selected": None, "message": "No devices connected."}
    if serial:
        for d in devices:
            if d.serial == serial:
                return {"devices": [d.to_dict() for d in devices], "selected": d.to_dict()}
        return {
            "devices": [d.to_dict() for d in devices],
            "selected": None,
            "message": f"Serial '{serial}' not in connected devices.",
        }
    if len(devices) == 1:
        return {"devices": [d.to_dict() for d in devices], "selected": devices[0].to_dict()}
    return {
        "devices": [d.to_dict() for d in devices],
        "selected": None,
        "message": "Multiple devices connected. Call select_device with `serial` set.",
    }


@mcp.tool(
    name="install_apk",
    title="Install APK",
    description=(
        "Install an APK file on a connected device using `adb install -r` (replace existing install). "
        "Returns success/failure plus the install output. Set `device` to target a specific serial; "
        "otherwise the lone connected device is used."
    ),
    annotations=ToolAnnotations(
        title="Install APK",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    ),
)
async def install_apk(apk_path: str, device: str | None = None) -> dict[str, Any]:
    path = Path(apk_path).expanduser()
    if not path.is_file():
        return {"ok": False, "error": f"APK not found at {path}"}
    try:
        result = await runner.run("install", "-r", str(path), device=device)
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": result.ok,
        "returncode": result.returncode,
        "output": (result.stdout.strip() or result.stderr.strip()),
        "device": device,
        "apk_path": str(path),
    }


def main() -> None:
    _tools.register(mcp)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.info("adb-mcp stopped")


if __name__ == "__main__":
    main()
