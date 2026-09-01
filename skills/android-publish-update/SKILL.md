---
name: android-publish-update
description: >
  Ship a new version of an existing Play Store app: bump versionCode, write
  changelog, rebuild signed AAB, upload to internal test track. Use this when
  the user asks to "publish an update" or "ship a new version". Do not use
  for the first release (use /publish) or for hot-fix rollbacks (use
  /publish --rollback).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [update, version-bump, changelog, signed-aab, internal-track]
---

# Android Publish Update

> [!NOTE]
> Bump version + changelog + sign + upload. Same internal-test-track default
> as first publish.

## Prerequisites

- An app already on Play Store internal test track
- The keystore is intact
- ANDROID_HOME on PATH

## Workflow

### Step 1: Bump version

In `app/build.gradle.kts`, increment `versionCode` and `versionName`:

```kotlin
defaultConfig {
    versionCode = <new>  // increment by 1
    versionName = "<new>"  // semver, e.g., "1.1.0"
}
```

> [!CAUTION]
> Never decrement `versionCode`. Play Store rejects.

### Step 2: Write changelog

Generate `.build-android/changelog-<versionCode>.txt`:

```
v1.1.0 (build 2)
─────────────────
- New: dark mode
- Fixed: crash on photo upload
- Improved: startup time
```

Format: short, scannable, user-facing language. Skip internal refactors.

### Step 3: Build signed AAB

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "bundleRelease", "cwd": ".", "timeout": 600 }
```

Verify `app/build/outputs/bundle/release/app-release.aab` exists and is signed:

```
tool: mcp__plugin_build_android_apps_keystore__verify
args: { "keystore_path": ".build-android/upload-keystore.jks", "alias": "upload", "password": "<from env>" }
```

### Step 4: Upload

```
tool: mcp__plugin_build_android_apps_play_store__upload_aab
args: { "package_name": "<from spec>", "aab_path": "app/build/outputs/bundle/release/app-release.aab", "track": "internal" }
```

### Step 5: Hand off

> New build uploaded to internal test track. Open Play Console to test, or run `/publish --promote internal production` to release to all users.

## Anti-patterns

- **DO NOT** bump `versionCode` without bumping `versionName` (or vice versa). Mismatched → Play Store rejects.
- **DO NOT** ship without a changelog. Internal testers want to know what changed.
- **DO NOT** delete the keystore between updates. The same keystore must sign every update.

## Pairing

- `/publish` — first publish
- `/why-rejected` — diagnose Play Store rejections
- `/status` — post-publish dashboard

## References

- See [references/version-strategy.md](references/version-strategy.md) for
  the versionCode/versionName + changelog conventions.
