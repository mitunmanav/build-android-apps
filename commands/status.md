---
description: Post-publish dashboard — downloads, ratings, crashes from Play Store.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_play_store__get_stats
  - mcp__plugin_build_android_apps_play_store__get_review_status
---

# /status

Show post-publish dashboard.

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null | head -20 || echo "no state.json"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll fetch your Play Store stats — downloads, ratings, review status, crashes."

## Your task

Delegate to `$build-android-apps` — call `play-store-mcp` `get_stats` + `get_review_status`. Summarize in plain English. `$ARGUMENTS`
