# MCP Servers Reference

Two Python MCP servers ship with this plugin: `adb-mcp` and `gradlew-mcp`. Both communicate over **stdio** (per Codex + Claude Code + agentskills.io open-standard recommendation).

## adb-mcp

17 tools for driving an Android device via the Android Debug Bridge.

### Tool index

| Tool | Annotations | Purpose |
|---|---|---|
| `list_devices` | RO, idempotent | `adb devices -l` |
| `select_device` | RO, idempotent | Pick a device (or auto-pick the lone connected one) |
| `install_apk` | destructive | `adb install -r <apk>` |
| `shell_command` | non-idempotent | `adb shell <command>` — for dumpsys, getprop, pm, am |
| `start_activity` | non-idempotent | Launch an activity via `am start` |
| `stop_app` | destructive, idempotent | `am force-stop <package>` |
| `uninstall_app` | destructive | `adb uninstall <package>` |
| `clear_app_data` | destructive, idempotent | `pm clear <package>` |
| `logcat_dump` | RO, idempotent | Filtered logcat dump |
| `logcat_clear` | destructive, idempotent | `logcat -c` |
| `screencap` | RO, idempotent | PNG screenshot, base64-encoded |
| `pull_file` | RO | `adb pull` |
| `push_file` | destructive | `adb push` |
| `getprop` | RO | Read a system property |
| `setprop` | destructive | Set a system property |
| `wait_for_device` | RO, idempotent | Block until boot complete |
| `unzip` | RO | Extract a zip on the host |

### Install

```bash
pip install -e ./mcp-servers/adb-mcp
adb-mcp   # or: python -m adb_mcp
```

### Smoke test

```bash
python3 -c "
import asyncio, json, sys
async def go():
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'adb_mcp',
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    msg = json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize',
                      'params':{'protocolVersion':'2024-11-05','capabilities':{},
                                'clientInfo':{'name':'smoke','version':'0.1'}}}).encode()
    proc.stdin.write(msg + b'\n'); await proc.stdin.drain()
    print(await proc.stdout.readline())
asyncio.run(go())
"
```

## gradlew-mcp

7 tools wrapping `./gradlew` for build automation.

### Tool index

| Tool | Annotations | Purpose |
|---|---|---|
| `list_tasks` | RO, idempotent | Parse `./gradlew tasks --all` |
| `run_task` | non-idempotent | Run a Gradle task (long-running) |
| `run_lint` | RO | `./gradlew lint` with summary |
| `run_tests` | RO | `./gradlew test` with summary |
| `clean` | destructive, idempotent | `./gradlew clean` |
| `parse_dependencies` | RO | `./gradlew :app:dependencies` |
| `find_duplicate_classes` | RO | Find class duplicates in the dep tree |

### Install

```bash
pip install -e ./mcp-servers/gradlew-mcp
gradlew-mcp   # or: python -m gradlew_mcp
```

## Transport

Both servers use **stdio** transport — no HTTP, no SSE, no WebSocket. The host launches the server as a subprocess and exchanges newline-delimited JSON-RPC 2.0 messages over the child's stdin/stdout.

## Resource + prompt surface

Both servers can additionally expose:

- **Resources** (subscribable): `adb://logcat/{device}/{buffer}` for live logcat streaming; `gradle://project/info` for project metadata
- **Prompts**: `diagnose-app-crash` (adb-mcp), `explain-error` (gradlew-mcp)

These are added in v0.2. See [SPEC.md §9](../SPEC.md) for the full list.

## Testing

```bash
cd mcp-servers/adb-mcp && pytest
cd mcp-servers/gradlew-mcp && pytest
```

10 tests per server, mocking the subprocess calls so no real adb/gradle required.
