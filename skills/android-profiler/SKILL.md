---
name: android-profiler
description: 'Capture and analyze Android performance traces using Perfetto (system-level
  traces), Android Studio''s CPU profiler, and macrobenchmark output. Diagnose jank,
  dropped frames, slow startups, high memory use, and excessive wakeups. Use this
  skill when the user reports "it''s slow", "scroll is janky", "startup takes forever",
  or asks to "profile" or "capture a trace". Do not use for one-shot UI bugs (use
  android-debugger-agent), for build speed issues (use gradlew run_task with `--profile`),
  or for memory leak detection (use android-leak-analyzer). Pairs with the `adb` and
  `gradlew` MCP servers.

  '
license: Apache-2.0
compatibility: 'Requires ANDROID_HOME on PATH, a connected device running Android
  8+ (API 26+ for Perfetto tracing), and ~200MB free storage for trace output.

  '
allowed-tools: mcp__plugin_build_android_apps_adb__list_devices mcp__plugin_build_android_apps_adb__shell_command
  mcp__plugin_build_android_apps_adb__pull_file mcp__plugin_build_android_apps_gradlew__run_task
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: android, perfetto, profiler, jank, frame, macrobenchmark, startup, tracing
  platform: android
  version: 0.1.0
---


# Android Profiler

## Prerequisites

- A connected device running API 26+ (Android 8.0+) for Perfetto
- ~200MB free storage on the host for trace output
- The target app installed in debug variant (release builds need `android:profileable` opt-in)
- For startup-specific traces: `androidx.benchmark:benchmark-macro-junit` configured in the project

## Workflow

### Step 1: Classify the symptom

Ask the user (or infer from context) which bucket:

1. **Slow startup**: cold start > 1s, warm start > 300ms, hot start > 100ms
2. **Janky scroll**: dropped frames, hitches in `LazyColumn`, `RecyclerView`, animations
3. **High CPU**: background drain, battery complaints, hot device
4. **Memory growth**: OOM, low-memory kills, app swapped out under memory pressure
5. **Network latency**: slow API calls, time-to-first-byte issues (usually server-side)

The bucket decides the trace type.

### Step 2: Capture the right trace

#### Startup (use Macrobenchmark)

```bash
./gradlew :benchmark:pixel6Api31BenchmarkAndroidTest \
  -P android.testInstrumentationRunnerArguments.class=androidx.benchmark.macro.junit4.MacrobenchmarkRule$StartupBenchmark
```

The output goes to `benchmark/build/outputs/connected_android_test_additional_output/.../startup-*.json`. Pull with:

```bash
adb pull /sdcard/Android/data/<package>/files/PerfettoTraces ./traces/
```

#### Janky scroll (use Perfetto system trace)

```bash
# On the device: start recording
adb shell perfetto -o /data/misc/perfetto-traces/trace.pftrace -c - \
  <<EOF
buffers: { size_kb: 65536 }
data_sources: { config { name: "linux.ftrace"     ftrace_config { atrace_categories: "am,wm,gfx,view,input,sched,freq,idle" } } }
data_sources: { config { name: "linux.processes" } }
duration_ms: 5000
EOF
adb pull /data/misc/perfetto-traces/trace.pftrace ./trace.pftrace
```

Open `https://ui.perfetto.dev/` and load `trace.pftrace`. Look for:

- Long frames in `Choreographer#doFrame` (> 16.6 ms = dropped frame)
- Main thread blocked on I/O, GC, or binder
- `WorkManager` running on UI thread
- Excessive recompositions in Compose (look at `Choreographer` + `RenderThread`)

#### High CPU (use simple perf profile)

```bash
adb shell top -n 5 -p <pid>
adb shell cat /proc/<pid>/stat   # for jiffies
```

Or use Perfetto with `sched` ftrace category to see what's on CPU.

### Step 3: Read the trace

Open in Perfetto UI and check:

1. **CPU usage over time**: spike or sustained? Which thread?
2. **Main thread idle time**: if zero, UI is bound. Find the long-running slice.
3. **RenderThread**: if RenderThread > 8ms, GPU is bound (overdraw, large layers).
4. **GC events**: frequent minor GCs indicate memory churn; major GC pauses are visible as long blocks.

For Compose-specific issues, look for `Compose.Composer` and `androidx.compose.runtime` slices.

### Step 4: Report findings

Format the report as:

```
Symptom: <one-line>
Trace: <file path + duration + size>
Evidence: <specific slice name + timestamp + duration>
Suspect: <function or code path>
Hypothesis: <why this matches the symptom>
Next: <concrete experiment to verify, e.g. "wrap in derivedStateOf">
```

### Step 5: Suggest + verify

After the user agrees on a fix, rebuild, redeploy, and re-capture the trace. Compare the two traces quantitatively (startup time before/after, frame count, etc.).

## Anti-patterns

- Do NOT capture traces on emulators with software rendering (`-gpu swiftshader_indirect`) — perf numbers will be meaningless. Use `-gpu host` or a real device.
- Do NOT capture a trace during device sleep — wake it first with `adb shell input keyevent KEYCODE_WAKEUP`.
- Do NOT trust a single trace — repeat 3 times and look for variance.
- Do NOT capture traces that include user PII in app data — Perfetto traces can contain event text. Strip before sharing.
- Do NOT skip the symptom-classification step — wrong trace type wastes 10+ minutes.

## Pairing

- `compose-performance-audit` — after the trace confirms a Compose issue, switch to this skill for the fix.
- `android-leak-analyzer` — if the trace shows memory growth without a corresponding workload.
- `android-debugger-agent` — for runtime investigation of a specific function call.
