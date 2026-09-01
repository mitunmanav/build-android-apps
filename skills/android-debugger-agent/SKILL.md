---
name: android-debugger-agent
description: 'Drive an interactive Android debug session: connect to a device via
  adb, attach the JDWP debugger, set breakpoints by line number, step through code,
  inspect variables, and triage stack traces from logcat or a crash report. Use this
  skill when the user asks to "debug this", "attach a debugger", "why is this happening",
  "trace through the call", or after a crash/ANR to localize the failing call site.
  Do not use this skill for build errors (use compose-performance-audit or run `/build`),
  for UI design questions, or for release-signed APK signing issues. Pairs with the
  `adb` MCP server and the `/debug`, `/crash`, `/log` slash commands.

  '
license: Apache-2.0
compatibility: 'Requires ANDROID_HOME on PATH (adb), an Android device or emulator
  connected via adb, and an app with `android:debuggable="true"` (the default for
  debug build type). Pairs with the `adb` MCP server shipped by this plugin.

  '
allowed-tools: mcp__plugin_build_android_apps_adb__list_devices mcp__plugin_build_android_apps_adb__select_device
  mcp__plugin_build_android_apps_adb__shell_command mcp__plugin_build_android_apps_adb__logcat_dump
  mcp__plugin_build_android_apps_adb__pull_file
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords:
  - android
  - kotlin
  - jetpack-compose
  - debugger
  - jdwp
  - adb
  - logcat
  - crash
  - anr
  platform: android
  version: 0.1.0
---


# Android Debugger Agent

## Prerequisites

- `adb` on `PATH` (the `SessionStart` hook warns if missing)
- At least one connected device or running emulator (`adb devices -l`)
- A debuggable build of the target app (do not attempt to attach to a release-signed APK)
- Optionally: a crash report or ANR trace under `${ANDROID_HOME}/.../tombstones/` or pulled from the device

## Workflow

### Step 1: Confirm device + app

1. Call `adb.list_devices`. If multiple devices appear, call `adb.select_device` to pick one (or ask the user).
2. Confirm the target package is installed: `adb.shell_command {"command": "pm list packages | grep <package>"}`.
3. Get the process PID: `adb.shell_command {"command": "pidof <package>"}`. If empty, the app is not running — start it.

### Step 2: Open the JDWP socket

The Android debug bridge exposes a JDWP socket per app process. To make the JVM pause until a debugger attaches (recommended for breakpoints on app startup), set the debug-app flag and re-launch:

```bash
adb shell am set-debug-app -w <package>
adb shell am start -n <package>/<launch-activity>
```

For mid-run attach (app already running), skip the `set-debug-app` step.

### Step 3: Capture the failure (if debugging a bug)

- **Crash**: `adb logcat_dump` with `args = {"since": "boot"}`, filter for `AndroidRuntime` and the package tag.
- **ANR**: `adb pull_file "/data/anr/traces.txt" ./traces.txt` then read the file.
- **Tombstone**: `adb pull_file "/data/tombstones/tombstone_0X" ./tombstone_0X` then read with `objdump -d` or addr2line.
- For each, also call `adb logcat_filter {"tag": "<package>", "level": "WARN"}` for recent warning context.

### Step 4: Localize the failing call site

If the user gave a stack trace, locate the user's source files using `grep -rn "<symbol>" app/src/main/kotlin`. Quote the exact line and read surrounding context. Do not guess — every claim must cite a file path and line number.

If only a symptom, ask the user for reproduction steps before guessing.

### Step 5: Propose a fix and verify

1. Read the offending file (Read tool). Show the user the snippet before editing.
2. Edit (Edit tool) with the smallest possible change.
3. Run `/build` to rebuild and reinstall.
4. Re-run the failing flow.
5. If the symptom persists, re-capture logcat and re-localize.

## Anti-patterns

- Do NOT modify files without first reading them and showing the user the snippet.
- Do NOT `adb logcat -c` while debugging — you'll lose the very lines you need. Use filter instead.
- Do NOT attach a debugger to a release-signed APK — Android refuses. Build a debug variant instead.
- Do NOT rely on `am force-stop` followed by `am start` to clear state — use `pm clear <package>` only when the user confirms.
- Do NOT skip the device-picker step when multiple devices are connected — wrong serial wastes 30+ seconds per command.

## Pairing

- `material3-expressive` and `compose-ui-patterns` — if the bug is in a Compose recomposition, switch skills before editing.
- `adb.logcat_dump` (subscribable resource) — for long sessions, subscribe to live logcat instead of polling.
- `/debug` slash command — pre-approved tool set for the full debug workflow.
- `/crash` slash command — when starting from a crash report rather than a live symptom.
