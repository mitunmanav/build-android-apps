---
description: "Run ./gradlew clean. Destructive: removes build/ and .gradle/. Confirms with user before running."
allowed-tools:
  - mcp__plugin_build_android_apps_gradlew__clean
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_adb__list_devices
  - Read
---

# /clean

Run `./gradlew clean`. **Destructive.** Always confirms first.

## Context

- Working directory: !`pwd`
- Gradle wrapper present: !`ls gradlew 2>/dev/null && echo yes || echo no`
- Build dir size: !`du -sh build 2>/dev/null || echo "no build dir"`

## Reporting Action

> [!IMPORTANT]
> Before proceeding, immediately tell the user: "I will run /clean."

## Your task

$ARGUMENTS

`$ARGUMENTS` is optional. If empty: clean. If "force" is given: skip confirmation.

### Step 1: Confirm

Use the elicitation tool to confirm with the user:

> "Run `./gradlew clean`? This will delete:
> - `build/` (all generated APK/AAR artifacts)
> - `.gradle/` (Gradle caches; re-downloads on next build)
> - Local build state for *all* modules
>
> Estimated impact: ~2-5 min slower next build.
>
> Proceed?"

Wait for the user's response. If `force`, skip.

### Step 2: Stop any running gradle daemon

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "--stop", "timeout": 30 }
```

### Step 3: Run clean

```
tool: mcp__plugin_build_android_apps_gradlew__clean
args: { "timeout": 120 }
```

### Step 4: Report

```
Cleaned: BUILD SUCCESSFUL in <X>s
Removed: build/ (<size>) and .gradle/ caches
Next build will: re-resolve dependencies (~3-5 min)
```

## Anti-patterns

- ❌ Don't clean without confirmation — it's destructive and slow to recover from.
- ❌ Don't use `clean` as a fix for build errors. Diagnose first.
- ❌ Don't clean in CI scripts — CI is meant to start from scratch anyway.
- ❌ Don't chain `clean` + `assembleDebug` in one go. The next build will be slow.
- ❌ Don't run `clean` if a Gradle daemon is mid-build — you'll get lock conflicts.
