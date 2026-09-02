---
name: android-leak-analyzer
description: 'Detect, triage, and fix memory leaks in Android apps using LeakCanary
  (debug builds), heap dumps, and reference-chain analysis. Use this skill when the
  user reports "memory keeps growing", "OOM crash", "Activity destroyed but still
  held", or asks to "find the leak". Do not use for transient GC pauses (use android-profiler)
  or for build-time dependency conflicts (use gradlew parse_dependencies). Pairs with
  the `adb` MCP server.

  '
license: Apache-2.0
compatibility: 'Requires ANDROID_HOME on PATH, a debug build with LeakCanary 3.x integrated
  (or ability to add it), and ~500MB free storage for heap dumps.

  '
allowed-tools: mcp__plugin_build_android_apps_adb__list_devices mcp__plugin_build_android_apps_adb__select_device
  mcp__plugin_build_android_apps_adb__shell_command mcp__plugin_build_android_apps_adb__pull_file
  mcp__plugin_build_android_apps_adb__start_activity
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: android, leak, leakcanary, heap-dump, hprof, oom, memory
  platform: android
  version: 0.1.0
---


# Android Leak Analyzer

## Prerequisites

- A connected device running API 24+ (LeakCanary 3.x baseline)
- Debug build of the target app
- Either:
  - LeakCanary 3.x integrated (`debugImplementation "com.squareup.leakcanary:leakcanary-android:3.x"`) — preferred
  - OR `am dumpheap` available for manual heap capture

## Workflow

### Step 1: Confirm LeakCanary is wired

If LeakCanary is not present, ask the user before adding the dependency — it's a non-trivial change that pulls in a transitive APK. Prefer to capture a manual heap dump first if LeakCanary isn't installed:

```bash
adb shell am dumpheap <package> /sdcard/heap.hprof
adb pull /sdcard/heap.hprof ./heap.hprof
```

### Step 2: Reproduce the leak

Ask the user (or infer) the navigation path that triggers the leak:

1. Launch the app: `adb shell am start -n <package>/<launch-activity>`
2. Drive the suspected flow (open screen X, navigate back, repeat 3+ times)
3. Force GC: `adb shell am send-trim-memory <package> RUNNING_CRITICAL`
4. Wait 5 seconds — LeakCanary will dump a notification to logcat if it finds anything

If LeakCanary is active, dump logcat:

```bash
adb logcat -d -s LeakCanary:V
```

Each leak report includes:
- The retained class (usually an Activity or Fragment)
- A reference chain explaining why it's held
- The expected-vs-actual reference type (e.g. expected GC root, got `static field`)

### Step 3: Read the reference chain

For each leak, identify:

1. **GC root**: what prevents the object from being collected?
   - Static field
   - Thread-local
   - JNI reference
   - Finalizer queue
2. **Strong reference path**: which holder chain connects root → leaked object?
3. **Leak point**: the user's own code on the path (skip framework noise like `MessageQueue` or `InputMethodManager`)

The standard pattern to look for:

```
LeakedActivity
  ↑ ContextWrapper
    ↑ ActivityThread.mActivities (static map)
      ↑ leaked because previous Activity reference not cleared
```

### Step 4: Common leak patterns

| Pattern | Cause | Fix |
|---|---|---|
| `static View` or `static Activity` | static field holds Activity | Convert to `@Composable` or `LocalContext.current` |
| `Handler` posted to a `View` | Handler outlives View | Use `view.removeCallbacks(handler)` in `onDestroy` |
| `Runnable` with implicit `this` capture | captures enclosing Activity | Use a `WeakReference<Activity>` or move Runnable into a top-level class |
| `Singleton` holding Context | `companion object` with `Context` | Use `applicationContext` only, never Activity |
| `LiveData` with a long-lived observer | Observer leaks Activity | Use `viewLifecycleOwner` in Fragment |
| `Job` or `Coroutine` not cancelled | coroutine outlives Activity | Cancel in `onDestroy` via `lifecycleScope` |
| `registerReceiver` without unregister | receiver kept alive | Track and unregister in `onPause`/`onDestroy` |
| `WebView` reference | native object kept alive | Destroy in `onDestroy`: `webView.destroy()` |

### Step 5: Propose fix and verify

After the user agrees on a fix:

1. Edit the offending file.
2. Run `/build` to rebuild.
3. Re-install and re-launch.
4. Repeat the same navigation flow.
5. Confirm no new leak appears in LeakCanary logcat.

If the leak persists, the reference chain will show the new suspect.

## Anti-patterns

- Do NOT add LeakCanary to a release build. It's debug-only.
- Do NOT ignore framework-leaks like `InputMethodManager` — they are real leaks if your code triggers them.
- Do NOT trust a single hprof file — capture 2-3 after identical navigation flows and compare reference counts.
- Do NOT clear app data mid-investigation (`pm clear`) — you'll lose the user's state and possibly the leak reproducer. Confirm with the user first.
- Do NOT use `android:largeHeap="true"` to "fix" a leak — it postpones the OOM. Fix the root cause.

## Pairing

- `android-profiler` — for memory growth without a clear leak (e.g. bitmap cache).
- `android-debugger-agent` — for runtime investigation of a specific lifecycle method.
- `material3-expressive` / `compose-ui-patterns` — if the leak originates from a Compose `remember` block.
