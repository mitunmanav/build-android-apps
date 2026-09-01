---
description: Submit to Play Store internal track — gated on keystore, listing, screenshots.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_play_store__upload_aab
  - mcp__plugin_build_android_apps_play_store__upload_listing
  - mcp__plugin_build_android_apps_play_store__get_review_status
  - mcp__plugin_build_android_apps_keystore__verify
---

# /publish

Submit to Play Store internal track. Gated by `release-check.sh` — keystore, listing, screenshots must exist.

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null | head -20 || echo "no state.json"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll publish to Play Store internal track. This builds a signed AAB and uploads it. Gated checks will block if listing or keystore is missing."

## Your task

Delegate to frontdoor `$build-android-apps` intent `publish` — load `skills/android-publish-update/SKILL.md` and follow its steps. If gated, fix gaps then retry. Print draft URL on success. `$ARGUMENTS`
