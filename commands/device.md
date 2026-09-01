---
description: List connected devices and pick one. Optionally launch an AVD by name.
allowed-tools:
  - mcp__plugin_build_android_apps_adb__list_devices
  - mcp__plugin_build_android_apps_adb__select_device
  - mcp__plugin_build_android_apps_adb__shell_command
  - mcp__plugin_build_android_apps_adb__getprop
  - mcp__plugin_build_android_apps_adb__wait_for_device
  - Bash
---

# /device

List connected devices, pick one (or launch a new AVD), and confirm it's the active target.

## Context

- Working directory: !`pwd`
- Connected devices: !`adb devices -l 2>/dev/null`
- Available AVDs: !`$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager list avd 2>/dev/null | grep -E 'Name:|Tag/' | head -20`
- ANDROID_HOME: !`echo "${ANDROID_HOME:-unset}"`

## Reporting Action

> [!IMPORTANT]
> Before proceeding, immediately tell the user: "I will run /device."

## Your task

$ARGUMENTS

`$ARGUMENTS` is optional. If a serial is given, select it. If an AVD name is given, launch it. If empty, list devices and let the user pick.

### Step 1: List connected

```
tool: mcp__plugin_build_android_apps_adb__list_devices
```

### Step 2: Decide

- 0 devices + AVD name in `$ARGUMENTS`: launch the AVD via `emulator -avd <name> -no-snapshot-load` then call `wait_for_device`.
- 0 devices + no AVD name: list AVDs and ask the user which to launch.
- 1 device: select it automatically.
- 2+ devices: ask the user which to target.

### Step 3: Select (if multi-device)

```
tool: mcp__plugin_build_android_apps_adb__select_device
args: { "serial": "<chosen serial>" }
```

### Step 4: Confirm readiness

```
tool: mcp__plugin_build_android_apps_adb__wait_for_device
args: { "timeout": 60 }
```

```
tool: mcp__plugin_build_android_apps_adb__getprop
args: { "name": "ro.build.version.release" }
```

### Step 5: Report

```
Device: <serial>
State: device
Android: <version>
SDK: <ro.build.version.sdk>
Model: <model>
Transport: <transport_id>
```

## Anti-patterns

- ❌ Don't silently pick the first device when multiple are connected — always confirm.
- ❌ Don't launch an emulator without confirming — it consumes ~2 GB RAM.
- ❌ Don't ignore `unauthorized` state — it means USB debugging isn't approved.
- ❌ Don't use `adb emu` commands on a physical device — they're emulators-only and silently no-op.
- ❌ Don't skip `wait_for_device` after launching an emulator — it returns before boot complete.
