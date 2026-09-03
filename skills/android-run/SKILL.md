---
name: android-run
description: >
  Install a debug APK on a connected device or emulator, launch the main
  activity, and capture an initial screenshot. Use this skill after
  gradlew-mcp run_task assembleDebug produces a debug APK and the user wants to run, preview, or
  see the app on a device or emulator. Pairs with /preview slash command. Do
  not use for release-signed APKs (use android-publish-update for Play
  Store), for screenshot test fixtures (use /test + qa-user), or for any
  device-side debugging (use android-debug-fix).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [adb, install, launch, screenshot, device]
---

# Android Run

> [!NOTE]
> Install + launch + screenshot. One cycle. No fixes.

## Prerequisites

- A debug APK at `app/build/outputs/apk/debug/app-debug.apk`
- A connected device or running emulator (`adb devices` non-empty)
- ANDROID_HOME on PATH

## Workflow

### Step 1: Pick the device

```
tool: mcp__plugin_build_android_apps_adb__list_devices
args: {}
```

If multiple devices, call `adb.select_device` and ask the user. Wrong serial = wasted 30+ seconds.

### Step 2: Confirm the APK exists

```
tool: mcp__plugin_build_android_apps_gradlew__describe_project
args: { "cwd": "." }
```

The response includes `apk_path`. If the file is missing, run `assembleDebug` first via `gradlew-mcp.run_task`.

### Step 3: Install

```
tool: mcp__plugin_build_android_apps_adb__install_apk
args: { "serial": "<serial>", "path": "<apk_path>" }
```

If the package is already installed and signatures differ, the install fails. Ask the user before running `uninstall_app` + reinstall.

### Step 4: Launch

```
tool: mcp__plugin_build_android_apps_adb__start_activity
args: { "serial": "<serial>", "package": "<application_id>", "activity": ".MainActivity" }
```

If `start_activity` returns no output, the app is starting. Wait 2 seconds before screenshot.

### Step 5: Capture screenshot

```
tool: mcp__plugin_build_android_apps_adb__screencap
args: { "serial": "<serial>", "path": "/tmp/preview.png" }
```

### Step 6: Report

Print:
- Device serial + API level
- APK installed (version code + version name)
- Activity launched
- Screenshot saved at /tmp/preview.png

Then ask: "Looks right? Want me to fix anything I see, or run `/preview` to capture more screens?"

## Anti-patterns

- **DO NOT** reinstall over an existing install with mismatched signatures without confirming.
- **DO NOT** auto-launch when multiple devices are connected.
- **DO NOT** use `am force-stop` to clear state — that wipes everything. Use `pm clear` only on user request.

## Pairing

- `gradlew-mcp run_task assembleDebug` — produces the APK (no android-build skill; /build delegates to gradlew-mcp)
- `android-debug-fix` — handles crashes / unexpected behavior after launch
- `mcp__plugin_build_android_apps_adb__screencap` — the screenshot tool
- `/preview` slash command — pre-approved entry point

## References

- See [references/device-picker.md](references/device-picker.md) for the
  multi-device selection UX.
