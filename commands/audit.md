---
description: Deep audit of an Android project: deps, lint, signing, gaps for Play Store.
allowed-tools:
  - mcp__plugin_build_android_app_plugin_gradlew__parse_dependencies
  - mcp__plugin_build_android_app_plugin_gradlew__find_duplicate_classes
  - mcp__plugin_build_android_app_plugin_gradlew__run_lint
  - mcp__plugin_build_android_app_plugin_gradlew__describe_project
  - Read
  - Bash
---

# /audit

Deep audit of an Android project. Checks dependency tree, duplicate classes, lint, signing config, and Play Store readiness gaps.

## Context

- Working directory: !`pwd`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll run a deep audit: deps, duplicates, lint, and Play Store gaps. Takes 1-3 minutes."

## Your task

### Step 1: Project shape

```
tool: mcp__plugin_build_android_app_plugin_gradlew__describe_project
args: { "cwd": "." }
```

### Step 2: Dependencies + duplicates

```
tool: mcp__plugin_build_android_app_plugin_gradlew__parse_dependencies
args: { "module": ":app", "configuration": "releaseRuntimeClasspath", "cwd": "." }
```

```
tool: mcp__plugin_build_android_app_plugin_gradlew__find_duplicate_classes
args: { "module": ":app", "cwd": "." }
```

### Step 3: Lint

```
tool: mcp__plugin_build_android_app_plugin_gradlew__run_lint
args: { "variant": "Debug", "cwd": ".", "timeout": 600 }
```

### Step 4: Gaps

For each, check if it's present in the project:

- `signingConfigs` block in `app/build.gradle.kts` → release signing
- `applicationId` matches the package in `MainActivity.kt`
- `google-services.json` present at `app/google-services.json`
- `app/src/main/res/values/strings.xml` has `app_name`
- `app/src/main/res/mipmap-*/ic_launcher.*` exists (icon)
- At least one test in `app/src/test` or `app/src/androidTest`

### Step 5: Summary

Print:

```
AUDIT: <project name>
─────────────────────
deps:           <N> libraries
duplicates:     <N> classes (warning: 0 is good)
lint:           <N> errors, <N> warnings
signing:        ✓ / ❌
icon:           ✓ / ❌
crashlytics:    ✓ / ❌ / optional
tests:          ✓ / ❌

GAPS:
1. ...
2. ...

Run `/finish` to auto-fix what's reasonable.
```

## Anti-patterns

- **DO NOT** modify any files during /audit. This is read-only.
- **DO NOT** run lint on the release variant if signing isn't configured (it fails).
