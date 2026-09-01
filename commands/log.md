---
description: Filter and stream logcat by tag, level, or regex. Supports one-shot dump or live subscription.
allowed-tools:
  - mcp__plugin_build_android_apps_adb__list_devices
  - mcp__plugin_build_android_apps_adb__select_device
  - mcp__plugin_build_android_apps_adb__logcat_dump
  - mcp__plugin_build_android_apps_adb__logcat_clear
  - mcp__plugin_build_android_apps_adb__shell_command
  - Read
---

# /log

Filter and inspect logcat output.

## Context

- Working directory: !`pwd`
- Connected devices: !`adb devices -l 2>/dev/null | head -10`

## Your task

$ARGUMENTS

`$ARGUMENTS` is a filter spec. Examples:

- `tag:MyClass` — match tag substring
- `level:W` — minimum level (V/D/I/W/E)
- `since:1h` — only lines from the last hour
- `regex:NullPointer|Crash` — regex against message text
- (empty) — last 100 lines, level I and above

If multiple filters are provided, AND them together. If only a level is given, filter all tags at that level.

### Step 1: Pick a device

Call `mcp__plugin_build_android_apps_adb__list_devices`. If empty, abort.

### Step 2: Clear (optional, only if user says "clear" or "fresh")

```
tool: mcp__plugin_build_android_apps_adb__logcat_clear
```

Confirm before clearing: clearing logcat is destructive.

### Step 3: Dump

```
tool: mcp__plugin_build_android_apps_adb__logcat_dump
args: { "tag": "<tag>", "level": "<level>", "since": "<since>", "max_lines": 200 }
```

For regex matching, fall back to:

```
tool: mcp__plugin_build_android_apps_adb__shell_command
args: { "command": "logcat -d | grep -E '<regex>' | tail -200" }
```

### Step 4: Format + show

Present the lines in a numbered, severity-tagged list. Highlight any `E` or `FATAL` lines in red. Suggest next steps if patterns emerge (e.g. "10 NullPointerException in 5s — likely a stale state" → recommend `/debug`).

## Anti-patterns

- ❌ Don't `logcat -c` while a debug session is active.
- ❌ Don't dump without a level filter on a busy device — 10,000 lines of `D` will drown the signal.
- ❌ Don't pipe through external `grep -v` chains; use the structured MCP dump.
- ❌ Don't tail-pipe to file without the user knowing; large log captures are storage-heavy.
- ❌ Don't include timestamps if the user just wants the latest; show the most recent first.
