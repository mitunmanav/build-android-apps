---
name: android-scaffold
description: >
  Bootstrap a fresh Android project from a completed app-intake spec. Generates
  Gradle build files, Compose UI scaffold, signing config, Material 3 theme,
  Firebase Crashlytics wiring, and runs the first assembleDebug to verify.
  Use this skill when the spec is ready and the user has approved the build
  plan, or whenever the agent needs to scaffold a new module. Do not use this
  skill to edit an existing project (use /change instead) or to import an
  external app (use android-importer).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [scaffold, gradle, compose, kotlin, crashlytics, signing]
---

# Android Scaffold

> [!NOTE]
> Generate a working Compose + Material 3 + Crashlytics project from the
> approved spec. One assembleDebug at the end to prove it builds.

## Prerequisites

- A spec at `.build-android/spec.md` (from app-intake)
- A planned state.json with a `scaffold` phase item (from app-planner)
- ANDROID_HOME on PATH (set by /setup)
- JDK 17+ on PATH

## Workflow

### Step 1: Read the spec

Read `.build-android/spec.md` and extract:
- `name` — the app's display name
- `application_id` — reverse-DNS package (default: `com.mitun.<name-lowercase>`)
- `min_sdk` / `target_sdk` — from spec, default to 26 / latest-stable
- `core_action` — used to name the first screen

### Step 2: Generate files

Write the following to the project root (do not overwrite existing files):

```
settings.gradle.kts
build.gradle.kts
gradle.properties
gradle/libs.versions.toml
gradle/wrapper/gradle-wrapper.properties  (Gradle 8.9)
gradlew  +  gradlew.bat  (download from gradle.org/gradle-8.9-bin.zip if missing)
app/build.gradle.kts
app/src/main/AndroidManifest.xml
app/src/main/kotlin/<package>/MainActivity.kt
app/src/main/kotlin/<package>/ui/Theme.kt
app/src/main/kotlin/<package>/ui/<FirstScreen>.kt
app/src/main/res/values/strings.xml
app/src/main/res/values/themes.xml
```

Use the pinned versions from SPEC.md §16.

### Step 3: Wire signing config

Reference keystore from `.build-android/upload-keystore.jks` if it exists:

```kotlin
signingConfigs {
    create("release") {
        storeFile = file("${rootProject.projectDir}/.build-android/upload-keystore.jks")
        storePassword = System.getenv("KEYSTORE_PASSWORD") ?: ""
        keyAlias = System.getenv("KEYSTORE_ALIAS") ?: "upload"
        keyPassword = System.getenv("KEY_PASSWORD") ?: ""
    }
}
buildTypes {
    release {
        signingConfig = signingConfigs.getByName("release")
        ...
    }
}
```

If the keystore doesn't exist, generate it now:

```
tool: mcp__plugin_build_android_apps_gradlew__generate_keystore
args: { "password": "<from user>", "key_password": "<from user or same>" }
```

Always warn the user to back up the keystore before continuing.

### Step 4: Silent-add Crashlytics

Without asking, add the Firebase Crashlytics plugin and DSN placeholder. The user opted in by selecting Firebase as a backend option (or by reaching the publish phase). Skip only if the user explicitly said "no analytics".

Add to `app/build.gradle.kts`:
```kotlin
plugins {
    id("com.google.gms.google-services")
    id("com.google.firebase.crashlytics")
}
```

Add to `app/src/main/AndroidManifest.xml`:
```xml
<meta-data android:name="com.google.firebase.crashlytics.enable" android:value="true" />
```

Write `app/google-services.json` placeholder with a comment saying "replace with your Firebase project's google-services.json".

### Step 5: First build verification

```
tool: mcp__plugin_build_android_apps_gradlew__run_help
args: { "cwd": "." }
```

Then:

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "assembleDebug", "cwd": ".", "timeout": 600 }
```

If `run_help` succeeds but `assembleDebug` fails, fix the obvious (sync issues, missing deps) before declaring done.

### Step 6: Update state.json

Mark the scaffold task done:

```
tool: Bash
args: { "command": "python3 -m state done .build-android/state.json --task <scaffold-task-id>", "description": "Mark scaffold done" }
```

## Anti-patterns

- **DO NOT** overwrite existing files. Read first; abort if a file exists unless the user has approved a rewrite.
- **DO NOT** ask the user about Crashlytics. They opted in by picking Firebase (or by reaching publish). Silent add.
- **DO NOT** commit the keystore to git. Add `*.jks` and `*.keystore` to `.gitignore`.
- **DO NOT** use the Gradle daemon in CI. Always pass `--no-daemon` for portability.

## Pairing

- `app-intake` — upstream (writes the spec)
- `app-planner` — produces the scaffold task in state.json
- `android-build` — used by /build for later assembleDebug runs
- `android-icons-assets` — Phase 11 adds launcher icon + adaptive layers

## References

- See [references/template-files.md](references/template-files.md) for the
  full template content of every file this skill writes.
- See [references/versions-pinned.md](references/versions-pinned.md) for the
  version pins per SPEC.md §16.
