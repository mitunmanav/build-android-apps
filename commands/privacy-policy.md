---
description: Generate privacy policy + Play Data Safety section from dependencies.
allowed-tools:
  - Bash
  - Read
  - Write
  - mcp__plugin_build_android_apps_gradlew__parse_dependencies
---

# /privacy-policy

Generate privacy policy template + Data Safety answers.

## Context

- Working directory: !`pwd`
- Dependencies: !`./gradlew :app:dependencies 2>/dev/null | head -20 || echo "no gradle"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll generate a privacy policy template and Data Safety form answers from your dependencies."

## Your task

Delegate to `$build-android-apps` intent `privacy-policy` — load `skills/android-store-listing/SKILL.md` privacy section. Write `.build-android/listing/privacy-policy.md`. `$ARGUMENTS`
