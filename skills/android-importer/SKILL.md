---
name: android-importer
description: >
  Detect, audit, and finish an existing Android project that was built by
  another tool (Lovable, Bolt, v0, Cursor, ChatGPT, etc.). Snapshots the
  project on entry so the user can roll back. Lists gaps between the existing
  project and what's needed to ship to Play Store. Use this skill when the
  user pastes a folder containing an Android project, or runs /import. Do not
  use on a fresh project (use android-scaffold instead) or to add features to
  an already-shipped project (use /add instead).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [import, audit, snapshot, foreign-project, lovable, bolt, v0, cursor]
---

# Android Importer

> [!NOTE]
> Take ownership of an Android project you didn't build. Snapshot first,
> then list gaps, then offer /finish to auto-fill.

## Prerequisites

- A path to an existing Android project (defaults to cwd)
- ANDROID_HOME on PATH (for later /audit steps)

## Workflow

### Step 1: Snapshot the project

Before touching anything, snapshot the existing files to `.build-android/snapshot-<ts>/`:

```
tool: Bash
args: { "command": "TS=$(date +%s); mkdir -p .build-android/snapshot-$TS && rsync -a --exclude='.build-android' --exclude='.git' --exclude='build' --exclude='.gradle' ./ .build-android/snapshot-$TS/ && echo \"snapshot saved to .build-android/snapshot-$TS\"", "description": "Snapshot existing files" }
```

If `rsync` is missing, fall back to `cp -R`.

### Step 2: Detect project type

```
tool: mcp__plugin_build_android_app_plugin_gradlew__describe_project
args: { "cwd": "." }
```

Classify:

| Detection | Classification |
|---|---|
| `is_android_app: false` | NOT an Android app → abort with clear message |
| `application_id` ends in `.debug` only | Debug variant only; no release config |
| No `signingConfigs` block | Not set up for Play Store |
| No `google-services.json` | Firebase not wired (fine if user opted out) |
| Uses Java only (no Kotlin) | Legacy; warn user about Compose availability |
| Uses XML views (no Compose deps) | Legacy; offer to migrate via compose-view-refactor |

### Step 3: Build summary report

Output a 1-page import summary:

```
IMPORT REPORT: <project name>
─────────────────────────────────────
project type:    Kotlin + Compose
application id:  com.example.recipe
versions:        min=26 target=34
build files:     /build.gradle.kts, /app/build.gradle.kts
signing:         ❌ not configured (debug-only)
crash reporting: ❌ not configured
backend:         ❌ none detected
tests:           ❌ no tests detected

GAPS TO SHIP TO PLAY STORE:
1. Add signing config (release build type)
2. Add Crashlytics (optional but recommended)
3. Add privacy policy URL
4. Generate launcher icon
5. Take screenshots for store listing

Run `/finish` to auto-fill these gaps.
```

### Step 4: Persist

```
tool: Bash
args: { "command": "python3 -m state add .build-android/state.json --title \"Import existing project\" --phase scaffold --id imp1 --by agent --files '.build-android/snapshot-<ts>/'", "description": "Record import" }
```

Mark it done immediately:

```
tool: Bash
args: { "command": "python3 -m state done .build-android/state.json --task imp1", "description": "Mark import done" }
```

### Step 5: Offer next

> Run `/audit` for a deeper check, or `/finish` to auto-fill the gaps and publish.

## Anti-patterns

- **DO NOT** modify any file until the snapshot is complete.
- **DO NOT** overwrite the existing build files. The user might want to keep their structure.
- **DO NOT** delete `google-services.json` or `release/` folders — they may have user data.
- **DO NOT** assume the project uses Kotlin + Compose. Some users have Java + XML.

## Pairing

- `/import` slash command — entry point
- `/audit` slash command — deeper dependency + lint check
- `/finish` slash command — auto-fill gaps + publish

## References

- See [references/foreign-tool-fingerprints.md](references/foreign-tool-fingerprints.md)
  for how to detect projects from specific generators (Lovable, Bolt, v0, etc.).
