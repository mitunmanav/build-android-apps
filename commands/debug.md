---
description: Attach the JDWP debugger, set up logcat streaming, and prepare for breakpoint debugging.
allowed-tools:
  - mcp__plugin_build_android_apps_adb__list_devices
  - mcp__plugin_build_android_apps_adb__select_device
  - mcp__plugin_build_android_apps_adb__shell_command
  - mcp__plugin_build_android_apps_adb__logcat_dump
  - mcp__plugin_build_android_apps_adb__getprop
  - mcp__plugin_build_android_apps_adb__start_activity
  - Read
  - Grep
---

# /debug

Set up a debug session: open JDWP socket, start logcat, ready the agent for breakpoint interaction.

## Context

- Working directory: !`pwd`
- Connected devices: !`adb devices -l 2>/dev/null | head -10`
- Recent crash logs: !`adb logcat -d -b crash 2>/dev/null | tail -20`

## Your task

$ARGUMENTS

`$ARGUMENTS` should be either the package name (e.g. `com.example`) or a description of what to debug.

### Step 1: Confirm device

Call `mcp__plugin_build_android_apps_adb__list_devices`. If empty, abort with: "Connect a device or start an emulator first."

### Step 2: Identify the package

If `$ARGUMENTS` is empty, search for the package from the current project:

```bash
grep -oE 'applicationId\s*=?\s*"[^"]+"' app/build.gradle.kts 2>/dev/null | head -1
```

Otherwise parse from `$ARGUMENTS`.

### Step 3: Set debug-app flag and re-launch (recommended for startup breakpoints)

Call `mcp__plugin_build_android_apps_adb__shell_command`:

```
tool: mcp__plugin_build_android_apps_adb__shell_command
args: { "command": "am set-debug-app -w <package>" }
```

Then find the launcher activity (read AndroidManifest.xml) and:

```
tool: mcp__plugin_build_android_apps_adb__start_activity
args: { "component": "<package>/<activity>" }
```

The app should now be paused at startup, waiting for a JDWP debugger.

### Step 4: Confirm JDWP port

```
tool: mcp__plugin_build_android_apps_adb__shell_command
args: { "command": "cat /proc/net/unix | grep -i jdwp" }
```

Expect a row like `00000000: 0000 0000 00000000 0000 0000 00000000 00000000 02 12345 1 @jdwp-control`. Note the PID (column 8).

### Step 5: Start logcat streaming

```
tool: mcp__plugin_build_android_apps_adb__logcat_dump
args: { "tag": "<package>", "level": "V", "max_lines": 200 }
```

### Step 6: Summarize for the agent

Print to the user:

- Package: `<package>`
- Device: `<serial>`
- PID: `<pid>`
- Debugger attached: NO (waiting for the agent to connect)
- Logcat tail (last 10 lines)

Then say: "App is paused at startup. Set breakpoints in your IDE, then attach. I'll watch logcat."

## Anti-patterns

- ❌ Don't `am force-stop` while a debugger is attached — you'll lose the JDWP session.
- ❌ Don't `pm clear` mid-debug — you wipe state. Ask first.
- ❌ Don't attempt to attach to a release-signed APK — it refuses. Build debug variant.
- ❌ Don't skip the `set-debug-app -w` step if breakpoints at startup are needed.
- ❌ Don't `adb logcat -c` while debugging.
