---
description: Build the Android app via Gradle (assembles the default debug variant).
allowed-tools:
  - mcp__plugin_build_android_app_plugin_gradlew__list_tasks
  - mcp__plugin_build_android_app_plugin_gradlew__run_task
  - mcp__plugin_build_android_app_plugin_gradlew__parse_dependencies
  - mcp__plugin_build_android_app_plugin_adb__list_devices
  - Read
  - Grep
  - Bash
---

# /build

Run a Gradle build for the Android project.

## Context

- Working directory: !`pwd`
- Recent commits: !`git log --oneline -5 2>/dev/null | head -5`
- Project layout (root): !`ls -la | head -20`
- Gradle wrapper present: !`ls gradlew 2>/dev/null && echo "yes" || echo "no"`

## Your task

$ARGUMENTS

If `$ARGUMENTS` is empty, build the default debug variant: `./gradlew assembleDebug`. Otherwise treat `$ARGUMENTS` as a Gradle task or task list.

### Step 1: Verify Gradle is wired

If `gradlew` is missing, abort with a clear message: "No gradlew script. Run this command from your Android project root, or use a plugin that scaffolds one."

### Step 2: Pick the device (only if the user wants install after build)

If the user's request implies install-after-build (e.g. "build and install"), call `mcp__plugin_build_android_app_plugin_adb__list_devices` first. If empty, warn.

### Step 3: Run the build

Call `mcp__plugin_build_android_app_plugin_gradlew__run_task`:

```
tool: mcp__plugin_build_android_app_plugin_gradlew__run_task
args: { "task": "<assembleDebug | user's task>", "timeout": 600 }
```

If `parse_dependencies` is requested in `$ARGUMENTS`, swap to:

```
tool: mcp__plugin_build_android_app_plugin_gradlew__parse_dependencies
args: { "module": ":app", "configuration": "debugRuntimeClasspath" }
```

### Step 4: Report

Show:

- Task name + final state (BUILD SUCCESSFUL / FAILED)
- Wall time (parsed from `BUILD ... in <X>s`)
- For failures: the last 30 lines of stdout and 20 of stderr
- For dependency parsing: a one-paragraph summary

## Anti-patterns

- ❌ Don't pipe gradle output to `grep` — the MCP tool returns structured output already.
- ❌ Don't `gradlew clean` unless explicitly asked (use `/clean` for that).
- ❌ Don't run with `--offline` unless the host has no network; let Gradle resolve.
- ❌ Don't retry on transient failures more than twice — escalate.
