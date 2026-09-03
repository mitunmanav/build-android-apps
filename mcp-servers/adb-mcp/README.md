# adb-mcp

MCP server wrapping the Android Debug Bridge (`adb`) for AI agents.

## What it does

Exposes `adb` as typed MCP tools so an AI agent can:

- List and select connected devices
- Install/uninstall APKs
- Capture screenshots, pull/push files
- Stream logcat (subscribable resource)
- Drive the Android shell (with safety guards)
- Run `am`, `pm`, `dumpsys`, `screencap`, etc.

## Install

```bash
# From the plugin root
pip install -e ./mcp-servers/adb-mcp

# Or from this directory
pip install -e .
```

## Run standalone (for debugging)

```bash
adb-mcp
# or
python -m adb_mcp
```

The server speaks MCP over stdio. Pair it with any MCP host (Codex, Claude Code, .agents).

## Tools provided (18 total)

| Tool | Annotations | Purpose |
|---|---|---|
| `list_devices` | read-only, idempotent | `adb devices -l` |
| `select_device` | read-only, idempotent | Pick from multi-device (returns selection) |
| `install_apk` | destructive | `adb install -r <apk>` |
| `shell_command`, `start_activity`, `stop_app`, `uninstall_app`, `clear_app_data` | mixed | Drive app + shell |
| `logcat_dump`, `logcat_clear`, `screencap`, `pull_file`, `push_file` | mixed | Logs, screenshots, files |
| `getprop`, `setprop`, `wait_for_device`, `dump_layout`, `unzip` | mixed | Props, boot, UI tree, zips |

See `../../SPEC.md §9` for the full tool list.

## Configuration

Reads from environment:

- `ANDROID_HOME` — preferred; uses `${ANDROID_HOME}/platform-tools/adb` if set
- `PATH` — falls back to `adb` on `PATH`

## License

Apache-2.0.
