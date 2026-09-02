# MCP Servers Reference

Five Python MCP servers ship with this plugin, all over **stdio** (per Codex + Claude Code + agentskills.io spec). Config: `.mcp.json`.

## adb-mcp

18 tools for driving an Android device via the Android Debug Bridge.

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
| `dump_layout` | RO, idempotent | `uiautomator dump` view hierarchy for UI debugging |
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
| `describe_project` | RO | JSON targets + APK/AAB paths (matches `android describe`) |
| `manage_sdk` | destructive | `sdkmanager` install/upgrade wrapper |
| `run_help` / `run_build_dry` | RO | Lightweight verification (`help` / `build --dry-run`) |

### Install

```bash
pip install -e ./mcp-servers/gradlew-mcp
gradlew-mcp   # or: python -m gradlew_mcp
```

## play-store-mcp

9 tools for Google Play Developer API: `auth`, `upload_aab`, `upload_listing`, `upload_screenshot`, `get_review_status`, `list_rejections`, `submit_for_review`, `rollout_staged`, `get_stats`.

## keystore-mcp

5 tools for upload keystore: `generate`, `verify`, `rotate`, `backup`, `fingerprint` (via `keytool`).

## asset-mcp

4 tools for launcher icons/feature graphics/screenshots: `generate_icon` (5 densities + adaptive), `generate_feature_graphic`, `generate_screenshot`, `compose_marketing` (requires `Pillow`).

## Transport

All 5 servers use **stdio** transport — no HTTP, no SSE, no WebSocket. The host launches each server as a subprocess and exchanges newline-delimited JSON-RPC 2.0 messages over stdin/stdout.

## Resource + prompt surface

Servers may additionally expose:

- **Resources** (subscribable): `adb://logcat/{device}/{buffer}`, `gradle://project/info`, `gradle://build/{id}/report`
- **Prompts**: `diagnose-app-crash` (adb-mcp), `explain-error` (gradlew-mcp)

See [SPEC.md §9](../SPEC.md) for the full tool tables.

## Testing

```bash
cd mcp-servers/adb-mcp && pytest
cd mcp-servers/gradlew-mcp && pytest
# keystore-mcp / play-store-mcp / asset-mcp — smoke via stdio (see scripts/smoke.sh)
```

10 tests per server (adb/gradlew), mocking subprocess so no real adb/gradle required.
