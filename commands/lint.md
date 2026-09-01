---
description: Run Android lint and summarize the results.
allowed-tools:
  - mcp__plugin_build_android_apps_gradlew__run_lint
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_gradlew__list_tasks
  - Read
  - Bash
---

# /lint

Run `./gradlew lint` and present the issue summary.

## Context

- Working directory: !`pwd`
- Gradle wrapper present: !`ls gradlew 2>/dev/null && echo yes || echo no`
- Existing lint reports: !`find . -name 'lint-results-*.xml' 2>/dev/null | head -5`

## Your task

$ARGUMENTS

`$ARGUMENTS` is optional. If empty: run `lintDebug`. If a variant is given (e.g. `release`), run `lintRelease`.

### Step 1: Run lint

```
tool: mcp__plugin_build_android_apps_gradlew__run_lint
args: { "variant": "<variant | null>", "timeout": 600 }
```

### Step 2: Locate the HTML report

After the build, the report is at `app/build/reports/lint-results-<variant>.html` (and `<variant>.xml` for tooling).

```bash
find app/build/reports -name "lint-results-*" 2>/dev/null | head -5
```

### Step 3: Parse and summarize

Use `mcp__plugin_build_android_apps_gradlew__run_lint`'s returned `summary` for high-level counts. For deeper analysis, read the XML and bucket issues:

- **Errors** (must fix before ship)
- **Warnings** (review; many are auto-suppressable with valid justification)
- **By category**: Performance, Security, Accessibility, Correctness, Style

### Step 4: Present

```
Lint <variant>: <N> errors, <M> warnings

Top categories:
  - Security: 5 (3 Critical)
  - Performance: 12
  - Correctness: 1

Next: <one-sentence suggestion; e.g. "review the Security:HardcodedDebugMode error in NetworkModule.kt">
```

## Anti-patterns

- ❌ Don't auto-suppress lint warnings. Add `@Suppress` with a justification comment, or fix the root cause.
- ❌ Don't run lint on every save; let it ride with `/build`.
- ❌ Don't ship if there are unaddressed errors. Warnings are at your discretion.
- ❌ Don't ignore Security-category findings without review — they often flag real issues.
