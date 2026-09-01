---
name: android-r8-analyzer
description: >
  Analyze APK/AAB size via R8 keep-rule audit + dependency tree analysis.
  Use this when the user asks "why is my APK so big", "shrink the APK", or
  before publishing. Strict-output-limit pattern: keep chat output under 30
  lines; details go to .scratch/. Do not use for compile errors (use /build),
  runtime errors (use android-debug-fix), or release-signed APK signing
  issues (use /publish).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [r8, proguard, apk-size, shrink, optimize, keep-rules]
---

# Android R8 Analyzer

> [!NOTE]
> Diagnose → report → prescribe. Strict output limit: 30 lines max in chat.
> Full report goes to `.scratch/r8-analyzer-<uuid>/report.md`.

## Prerequisites

- A built release AAB at `app/build/outputs/bundle/release/app-release.aab`
- ANDROID_HOME on PATH

## Workflow

### Step 1: Pick a containment dir

```bash
TS=$(date +%s)
SCRATCH=".scratch/r8-analyzer-$TS"
mkdir -p "$SCRATCH"
```

### Step 2: Run the analyze task

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "analyzeReleaseBundle", "cwd": ".", "timeout": 300 }
```

Capture output to `$SCRATCH/gradle-analyze.txt`.

### Step 3: Parse the bundle for size breakdown

Use the bundle tool directly:

```bash
$ANDROID_HOME/cmdline-tools/latest/bin/apkanalyzer bundle file-size app-release.aab
$ANDROID_HOME/cmdline-tools/latest/bin/apkanalyzer dex packages app-release.aab
```

Save both to `$SCRATCH/`.

### Step 4: Inspect R8 keep rules

```
tool: Read
args: { "file_path": "app/proguard-rules.pro" }
```

Cross-reference with `find_duplicate_classes` to spot overly broad `-keep` rules.

### Step 5: Write the report

Write to `$SCRATCH/report.md`:

```markdown
# R8 / APK Size Report

## Bundle size: <X> MB
## Top 10 contributors: ...
## Unused dependencies: ...
## Overly broad keep rules: ...
## Recommended actions:
- [ ] drop `unused-library-x:1.0.0`
- [ ] tighten `-keep class com.example.** { *; }` to specific class names
- [ ] enable `isShrinkResources = true` (already on per project, verify)
```

### Step 6: Output to chat (30 lines max)

```
R8 report: .scratch/r8-analyzer-<ts>/report.md

bundle size: 12.4 MB
top contributors:
- androidx.compose.runtime: 3.2 MB
- firebase-firestore: 2.1 MB
- kotlinx-coroutines: 1.4 MB

recommended actions (3):
1. Drop unused dep `lifecycle-viewmodel-savedstate`
2. Tighten `-keep class com.example.** { *; }` to specific signatures
3. Enable resource shrinking in release (verify in app/build.gradle.kts)

Run /build --release after fixes.
```

## Anti-patterns

- **DO NOT** dump the full report to chat. Use the scratch dir.
- **DO NOT** recommend removing a library without checking if it's transitively used.
- **DO NOT** suggest disabling R8. It's the shrinker.
- **DO NOT** run on a debug build. Always release.

## Pairing

- `android-build` — produces the bundle to analyze
- `apk-inspector` subagent — for deeper binary inspection

## References

- See [references/keep-rule-catalog.md](references/keep-rule-catalog.md)
  for the canonical keep rules for common libraries (Hilt, Room, Retrofit, etc.).
