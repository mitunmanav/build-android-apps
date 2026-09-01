---
description: Generate Play Store screenshots from running app via adb screencap + asset-mcp.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_adb__screencap
  - mcp__plugin_build_android_apps_asset__generate_screenshot
---

# /screenshots

Generate Play Store screenshots.

## Context

- Working directory: !`pwd`
- Devices: !`adb devices 2>/dev/null | tail -n +2 || echo "no adb"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll capture screenshots for your Play Store listing from the running app."

## Your task

Delegate to `$build-android-apps` — load `skills/android-icons-assets/SKILL.md` + `asset-mcp` `generate_screenshot`. Save to `.build-android/listing/screenshots/`. `$ARGUMENTS`
