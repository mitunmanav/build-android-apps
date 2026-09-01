---
description: Bump version, add changelog, build signed AAB, re-upload to Play Store.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_play_store__upload_aab
  - mcp__plugin_build_android_apps_gradlew__run_task
---

# /update

Bump version + changelog + re-upload. For already-published apps.

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null | head -20 || echo "no state.json"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll bump version, build a new AAB, and re-upload to Play Store."

## Your task

Delegate to `$build-android-apps` intent `update` — load `skills/android-publish-update/SKILL.md` steps for version bump. Print new version + draft URL. `$ARGUMENTS`
