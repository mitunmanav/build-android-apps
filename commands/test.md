---
description: Run unit tests and summarize the results (pass/fail/flake counts, top failures).
allowed-tools:
  - mcp__plugin_build_android_apps_gradlew__run_tests
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_gradlew__list_tasks
  - Read
  - Bash
---

# /test

Run unit tests and report.

## Context

- Working directory: !`pwd`
- Test source dirs: !`find . -path '*/src/test/*Test.kt' -o -path '*/src/test/*Test.java' 2>/dev/null | head -10`

## Reporting Action

> [!IMPORTANT]
> Before proceeding, immediately tell the user: "I will run /test."

## Your task

$ARGUMENTS

`$ARGUMENTS` is optional. If empty: `testDebugUnitTest`. If a variant is given: `test<variant>UnitTest`.

### Step 1: Run tests

```
tool: mcp__plugin_build_android_apps_gradlew__run_tests
args: { "variant": "<variant | null>", "timeout": 900 }
```

For instrumentation tests, use `run_task` directly:

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "connectedDebugAndroidTest", "timeout": 900 }
```

### Step 2: Locate the report

The XML reports are at `app/build/test-results/test<variant>UnitTest/` and the HTML at `app/build/reports/tests/test<variant>UnitTest/`.

```bash
find app/build/test-results -name "TEST-*.xml" 2>/dev/null | head -10
```

### Step 3: Parse and bucket

For each test result XML:

- Total tests
- Failures (with the first failure stack frame)
- Errors (e.g. uncaught exception)
- Skipped
- Flake rate (if Gradle's `testRetry` is configured)

For failures, find the test class + method, then read the source:

```bash
grep -rn "fun <testMethodName>" app/src/test/
```

### Step 4: Present

```
Tests: <total> | Passed: <P> | Failed: <F> | Errors: <E> | Skipped: <S>

Top failures:
  1. <ClassName>.<method>: <one-line assertion message>
     File: <path>:<line>
     Suggested: <one-sentence fix or next step>

  2. ...
```

## Anti-patterns

- ❌ Don't ship with failing tests. Investigate every red bar.
- ❌ Don't `@Ignore` failing tests to make CI green. Fix or delete.
- ❌ Don't conflate unit tests with instrumented tests — they need different tasks.
- ❌ Don't skip the stack-trace read. The class name alone rarely tells you why.
- ❌ Don't commit tests that flake repeatedly. Quarantine or fix.
