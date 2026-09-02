---
name: android-emulator-browser
description: 'Launch, control, and inspect an Android emulator or connected device
  from the AI assistant. Capture screenshots, drive the UI by tapping/swiping, dump
  the view hierarchy, and inspect element bounds. Use this skill when the user wants
  to "see what''s on screen", "drive the app", "show me the UI", or verify a visual
  change on a real device or AVD. Do not use for unit-test runs, profiler traces,
  or anything that needs the host machine''s GPU. Pairs with the `adb` MCP server
  and the `/device` and `/run` slash commands.

  '
license: Apache-2.0
compatibility: 'Requires ANDROID_HOME on PATH (adb), an Android emulator (AVD) created
  via avdmanager or a USB-connected device with USB debugging enabled.

  '
allowed-tools: mcp__plugin_build_android_apps_adb__list_devices mcp__plugin_build_android_apps_adb__select_device
  mcp__plugin_build_android_apps_adb__shell_command mcp__plugin_build_android_apps_adb__start_activity
  mcp__plugin_build_android_apps_adb__screencap
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: android, emulator, avd, screencap, uiautomator, view-hierarchy, adb
  platform: android
  version: 0.1.0
---


# Android Emulator Browser

## Prerequisites

- `adb` on `PATH`
- At least one emulator (AVD) running OR a USB-connected device with debugging enabled
- An Android app to inspect (the app does not need to be running — you can launch it)

## Workflow

### Step 1: Confirm what's connected

Call `adb.list_devices`. If empty, offer to start an emulator:

```bash
$ANDROID_HOME/emulator/emulator -avd <avd-name> -no-snapshot-load
```

Or use `avdmanager list avd` to enumerate available AVDs first.

If multiple devices are connected, call `adb.select_device` to pick one before any device-specific action.

### Step 2: Get the current view hierarchy

Use UIAutomator's dump to inspect what's on screen:

```bash
adb shell uiautomator dump /sdcard/window_dump.xml
adb pull /sdcard/window_dump.xml ./window_dump.xml
```

The XML contains one node per visible element with `bounds`, `text`, `content-desc`, and `class` attributes. Use this to:

- Confirm what the user is reporting
- Compute tap coordinates: bounds="[x1,y1][x2,y2]" → tap at ((x1+x2)/2, (y1+y2)/2)
- Verify a screen shows expected content after a code change

### Step 3: Drive the UI

For taps, swipes, and text input, use `adb shell input`:

```bash
# Tap
adb shell input tap 540 1200

# Swipe
adb shell input swipe 100 1000 100 200 300   # x1 y1 x2 y2 duration_ms

# Type text (spaces need %s, special chars need escaping)
adb shell input text "hello%sworld"

# Hardware back / home / recents
adb shell input keyevent 4     # KEYCODE_BACK
adb shell input keyevent 3     # KEYCODE_HOME
adb shell input keyevent 187   # KEYCODE_RECENT_APPS
```

For content-description or text-based targeting (more reliable than coordinates), prefer `adb shell uiautomator2` if installed — but coordinate input works without any extra tooling.

### Step 4: Capture a screenshot

```bash
adb shell screencap -p /sdcard/screen.png
adb pull /sdcard/screen.png ./screen.png
```

Use the screenshot to verify visual state. View the file with the file-reading tool.

### Step 5: Verify or report

After driving the UI, re-dump the hierarchy or take a fresh screenshot to confirm the expected state. Report what you observed to the user with concrete details (text content, element bounds, timestamp) — never claim something happened without evidence.

## Anti-patterns

- Do NOT use `adb emu` commands on physical devices — they only work on emulators and silently no-op elsewhere.
- Do NOT assume coordinates are stable across screen sizes — always derive from `uiautomator dump` bounds, not hardcoded numbers.
- Do NOT chain `input tap` and `input text` without a small sleep — fast devices can drop inputs. `adb shell` with a single shell that chains commands is more reliable than separate invocations.
- Do NOT leave a screencap on the device — always pull and clean up with `adb shell rm /sdcard/screen.png`.
- Do NOT use the emulator's "rotate" UI control to test rotation — set `adb shell settings put system accelerometer_rotation 0` and `adb shell settings put system user_rotation 1` to force rotation reliably.

## Pairing

- `material3-expressive` — when verifying a Compose UI change, also check for Material 3 Expressive compliance.
- `compose-performance-audit` — if you notice jank while driving the UI, switch skills to investigate.
- `adb.screencap` (in MCP) — for a typed alternative to the shell command above.
- `/device` slash command — picks the target device with confirmation.
