---
description: Pull and analyze an Android crash report (tombstone, ANR trace, or logcat crash buffer).
allowed-tools:
  - mcp__plugin_build_android_app_plugin_adb__list_devices
  - mcp__plugin_build_android_app_plugin_adb__select_device
  - mcp__plugin_build_android_app_plugin_adb__logcat_dump
  - mcp__plugin_build_android_app_plugin_adb__shell_command
  - mcp__plugin_build_android_app_plugin_adb__pull_file
  - mcp__plugin_build_android_app_plugin_adb__push_file
  - mcp__plugin_build_android_app_plugin_adb__unzip
  - Read
  - Grep
---

# /crash

Analyze a crash: pull the crash report, read the offending stack frames, localize to your source.

## Context

- Working directory: !`pwd`
- Recent crash logs on default device: !`adb logcat -d -b crash 2>/dev/null | tail -10`

## Your task

$ARGUMENTS

`$ARGUMENTS` is optional. If empty, analyze the most recent crash on the connected device. If a path to a crash report file is given, analyze that file directly.

### Step 1: Identify the crash source

#### Case A: User provided a file path

Skip to Step 3 with the file path.

#### Case B: Crash on a connected device

```
tool: mcp__plugin_build_android_app_plugin_adb__logcat_dump
args: { "tag": "AndroidRuntime", "level": "E", "max_lines": 100 }
```

Look for `FATAL EXCEPTION`. Note the package name and exception type.

#### Case C: ANR

```
tool: mcp__plugin_build_android_app_plugin_adb__shell_command
args: { "command": "ls /data/anr/" }
tool: mcp__plugin_build_android_app_plugin_adb__pull_file
args: { "remote_path": "/data/anr/traces.txt", "local_path": "./anr_traces.txt" }
```

Read `./anr_traces.txt` and find the offending thread (usually `main`).

#### Case D: Tombstone (native crash)

```
tool: mcp__plugin_build_android_app_plugin_adb__shell_command
args: { "command": "ls /data/tombstones/" }
tool: mcp__plugin_build_android_app_plugin_adb__pull_file
args: { "remote_path": "/data/tombstones/tombstone_0X", "local_path": "./tombstone_0X" }
```

The tombstone format includes a register dump and a backtrace. For symbol resolution, you may need an `addr2line` step (out of scope here).

### Step 2: Pull the report (Case B)

If the user wants the crash saved:

```
tool: mcp__plugin_build_android_app_plugin_adb__shell_command
args: { "command": "logcat -b crash -d -f /sdcard/crash.txt" }
tool: mcp__plugin_build_android_app_plugin_adb__pull_file
args: { "remote_path": "/sdcard/crash.txt", "local_path": "./crash.txt" }
```

### Step 3: Read + localize

Read the crash file with the Read tool. Identify:

1. Exception type (`java.lang.NullPointerException`, etc.)
2. The first frame in the user's source code (skip framework frames)
3. The exact file + line

Search for the offending class:

```bash
grep -rn "class <ClassName>" app/src/main/
```

Read the surrounding context (10 lines above and below).

### Step 4: Report

Format:

```
Crash type: <exception>
Package: <package>
Thread: <thread>
File: <path>:<line>
Symbol: <fully.qualified.Class.method>
Cause: <one-line interpretation from the surrounding code>
Hypothesis: <what likely went wrong>
Next: <concrete fix or "ask the user for repro steps">
```

## Anti-patterns

- ❌ Don't trust the first frame in the stack — it's often a framework method. The user's code is deeper.
- ❌ Don't `pm clear` to "fix" the crash — that's hiding the symptom. Fix the cause.
- ❌ Don't pull tombstones via `cat` on a non-root device — they'll be unreadable. Always use `adb pull`.
- ❌ Don't ship a fix without reproducing locally. Build, install, repeat the steps that triggered the crash.
- ❌ Don't ignore "caused by" chains — NPEs often hide a deeper IllegalStateException.
