---
description: Build (if needed), install the APK, and launch the app on a connected device.
allowed-tools:
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_gradlew__list_tasks
  - mcp__plugin_build_android_apps_adb__list_devices
  - mcp__plugin_build_android_apps_adb__select_device
  - mcp__plugin_build_android_apps_adb__install_apk
  - mcp__plugin_build_android_apps_adb__start_activity
  - mcp__plugin_build_android_apps_adb__wait_for_device
  - mcp__plugin_build_android_apps_adb__logcat_dump
  - Read
  - Bash
---

# /run

Build, install, and launch the app on a connected device.

## Context

- Working directory: !`pwd`
- Connected devices: !`adb devices -l 2>/dev/null | head -10`
- Recent changes: !`git log --oneline -3 2>/dev/null`

## Your task

$ARGUMENTS

`$ARGUMENTS` is optional. If empty: build debug, install, launch the launcher activity. If provided, treat as a variant override (e.g. "release") or package name override (e.g. "com.example/.MainActivity").

### Step 1: Pick a device

Call `mcp__plugin_build_android_apps_adb__list_devices`. If empty, ask the user to start an emulator or connect a device. If multiple, call `mcp__plugin_build_android_apps_adb__select_device` with the chosen serial.

### Step 2: Wait for device

Call `mcp__plugin_build_android_apps_adb__wait_for_device` to ensure boot complete.

### Step 3: Build (skip if no Kotlin/Java sources changed since last build)

Call `mcp__plugin_build_android_apps_gradlew__run_task`:

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "assembleDebug", "timeout": 600 }
```

Use `assembleRelease` if `$ARGUMENTS` says release. The MCP server returns the APK path; capture it.

### Step 4: Install

Call `mcp__plugin_build_android_apps_adb__install_apk`:

```
tool: mcp__plugin_build_android_apps_adb__install_apk
args: { "apk_path": "<returned apk path>", "device": "<serial>" }
```

### Step 5: Launch

Read `AndroidManifest.xml` to find the launcher activity:

```bash
grep -A1 "LAUNCHER" app/src/main/AndroidManifest.xml
```

Then call:

```
tool: mcp__plugin_build_android_apps_adb__start_activity
args: { "component": "<package>/<activity>", "device": "<serial>" }
```

If `$ARGUMENTS` provides a custom activity or deeplink action, use that instead.

### Step 6: Confirm launch

Use `mcp__plugin_build_android_apps_adb__logcat_dump` to confirm the app's process started. Report the PID + first 5 lines of logcat.

## Anti-patterns

- ❌ Don't `adb install -r` then `adb shell am start` without waiting for the install to complete — the activity start races.
- ❌ Don't assume the device is ready just because `adb devices` shows it — call `wait_for_device`.
- ❌ Don't auto-install over a release-signed APK — confirm with the user first.
- ❌ Don't guess the launcher activity — read AndroidManifest.xml.
