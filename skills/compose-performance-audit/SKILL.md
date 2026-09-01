---
name: compose-performance-audit
description: >
  Audit Jetpack Compose UI for recomposition, stability, and runtime performance
  issues. Diagnose wasted recompositions, missing `key()` calls, non-stable parameters,
  deferred reads, and missing baseline profile optimizations. Use this skill when
  the user asks to "review Compose performance", "why is this recomposing", "is this
  stable", "add a baseline profile", or after jank is observed in a Perfetto trace
  (use android-profiler first). Do not use for plain Kotlin performance, for build
  speed, or for Material 3 design questions. No MCP server required.
license: Apache-2.0
compatibility: >
  Requires Compose Compiler 1.5+ for stability inference. Baseline profile requires
  Compose 1.4+ and `androidx.profileinstaller`. No MCP server required.
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [android, jetpack-compose, performance, recomposition, stability, baseline-profile, skipping]
  platform: android
  version: 0.1.0
---

# Compose Performance Audit

## Prerequisites

- Compose Compiler 1.5+ (1.5.15+ recommended for stable inference accuracy)
- Android Studio Iguana+ or Hedgehog+ for Layout Inspector / Recomposition counts
- For baseline profile generation: `androidx.profileinstaller` + Macrobenchmark module
- A debug build of the target app (release needed only for baseline profile artifacts)

## Workflow

### Step 1: Classify the issue

Ask which category:

1. **Wasted recompositions**: composables re-running without input changes
2. **Stability problem**: a parameter type prevents the compiler from skipping recomposition
3. **Heavy computation in composition**: a function called every recomposition that does work
4. **Skipped frames**: visible jank, dropped frames, slow animations
5. **Large object allocation**: hot path allocations causing GC pressure

### Step 2: Wasted recompositions (Composition Counting)

Enable counts in `build.gradle.kts`:

```kotlin
android {
    buildTypes {
        create("release") {
            isMinifyEnabled = true
            // ...
        }
    }
}
composeCompiler {
    reportsDestination.set(layout.buildDirectory.dir("compose_compiler"))
}
```

In debug, use Layout Inspector → tick "Show recomposition counts". Numbers > 1 on a static parent indicate wasted recomposition.

**Common fix**:

```kotlin
// BAD — recomposes every parent recomposition
@Composable
fun Header(name: String) {
    Text("Hello $name")
}

// GOOD — skipped if name unchanged (Stable param)
@Composable
fun Header(name: String, modifier: Modifier = Modifier) {
    Text("Hello $name", modifier = modifier)
}
```

### Step 3: Stability problems

If Layout Inspector highlights a parameter type with a "non-stable" badge, wrap with `@Stable` or `@Immutable`:

```kotlin
@Immutable
data class UserUi(val id: Long, val name: String, val avatarUrl: String?)

// Or for non-data classes:
@Stable
class UserState {
    var name by mutableStateOf("")
    var age by mutableStateOf(0)
}
```

Avoid:

- `List<T>` and `Set<T>` parameters — these are unstable by default in Compose Compiler < 1.5.15. Use `ImmutableList<T>` (kotlinx.collections.immutable) or annotate your wrapper.
- `MutableState<T>` as a composable parameter — pass the underlying value and the setter.
- Java types without `@Stable` or `@Immutable` annotation.

### Step 4: Deferred reads

Hoist reads out of lambdas:

```kotlin
// BAD — the lambda reads State every recomposition, defeating memoization
LazyColumn {
    items(items) { item ->
        Text(item.name)
        if (showDetails.value) Text(item.description)
    }
}

// GOOD — read once outside the lambda
val showDetailsState = showDetails.value
LazyColumn {
    items(items) { item ->
        Text(item.name)
        if (showDetailsState) Text(item.description)
    }
}
```

In Compose 1.7+, the compiler issues "Deferred reads in composable lambdas" warnings. Treat every warning as a finding.

### Step 5: Heavy computation in composition

```kotlin
// BAD — recomputed every recomposition
@Composable
fun Stats(items: List<Item>) {
    val total = items.sumOf { it.value }
    Text("Total: $total")
}

// GOOD — `remember` + key
@Composable
fun Stats(items: List<Item>) {
    val total = remember(items) { items.sumOf { it.value } }
    Text("Total: $total")
}
```

For expensive derivation, consider `derivedStateOf`:

```kotlin
val showButton by remember {
    derivedStateOf { scrollState.value > threshold }
}
```

### Step 6: Baseline profiles

For startup and hot-path performance:

1. Add `androidx.profileinstaller` (already in Compose BOM).
2. Add the macrobenchmark module if not present.
3. Write startup, scroll, and navigation benchmarks.
4. Run `./gradlew :benchmark:pixel6Api31BenchmarkAndroidTest` from Android Studio.
5. The artifact `*_baseline-prof.txt` goes to `app/src/main/`.

Validate via:

```bash
./gradlew :app:installRelease
# Cold start should be measurably faster
```

### Step 7: Report findings

Format as:

```
Issue: <one-line description>
File: <path:line>
Evidence: <recomposition count / stability badge / trace slice>
Fix: <code snippet>
Expected: <quantitative improvement, e.g. "skips 5 redundant recompositions per frame">
```

## Anti-patterns

- Do NOT wrap every value in `remember` blindly — over-memoization adds overhead. Use it only for computations with measurable cost.
- Do NOT use `key()` inside `LazyColumn` with non-stable types — the compiler warns and the key is ignored.
- Do NOT block composition with `runBlocking`. Move blocking I/O to viewModelScope or a dispatcher.
- Do NOT trust a single Layout Inspector session — recompile with `reportsDestination` and read the generated CSV.
- Do NOT ship baseline profiles generated on emulator to production without a device-side validation.

## Pairing

- `android-profiler` — first, capture a trace to know whether recomposition is actually the bottleneck.
- `compose-ui-patterns` — for the broader idiom set; performance often comes from using the right pattern.
- `material3-expressive` — when motion choreography is the cause of recomposition storms.
