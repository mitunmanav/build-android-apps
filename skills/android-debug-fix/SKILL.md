---
name: android-debug-fix
description: >
  Debug a failing Android app via logcat + structured fix-loop. Use this when
  the app crashes, freezes, hangs, gets stuck, throws an exception, or
  produces unexpected behavior at runtime. The skill captures logcat,
  localizes the failing call site, edits the smallest possible change,
  rebuilds, reinstalls, and verifies. Do not use for compile-time errors (use
  /build or /lint) or for design issues without a crash (use /preview or
  compose-ui-patterns).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [debug, logcat, crash, fix, agent-loop, jdwp]
---

# Android Debug Fix

> [!NOTE]
> Diagnose → report → prescribe → fix → verify. Strict-output-limit pattern:
> keep chat responses under 30 lines.

## Prerequisites

- The app installed on a device
- Source tree readable (project root)

## Workflow

### Step 1: Choose the entry point

Two paths:
- **Symptom-driven**: user says "the app crashes when I tap X" → reproduce, capture logcat, localize.
- **Crash-driven**: user pastes a stack trace → start at Step 3.

### Step 2: Reproduce + capture

For symptom-driven:
1. Use `adb-mcp.logcat_clear` (with confirmation) to clear the log buffer.
2. Tap the failing UI element.
3. Use `adb-mcp.logcat_dump` with `{"since": "boot"}` and filter for the package tag + `AndroidRuntime`.

For crash-driven, the user already has the trace. Skip directly to Step 3.

### Step 3: Localize

Search the source for the failing class/symbol:

```
tool: Grep
args: { "pattern": "<symbol from trace>", "path": "app/src/main/kotlin" }
```

Read the offending file with `Read`. Quote the exact line and the surrounding 5 lines. Cite `path:line` in your report.

### Step 4: Prescribe

Output ONE minimal change proposal:

> File: `app/src/main/kotlin/.../HomeViewModel.kt:42`
>
> Current:
> ```kotlin
> viewModelScope.launch { repo.fetch() }
> ```
>
> Proposed:
> ```kotlin
> viewModelScope.launch(Dispatchers.IO) { repo.fetch() }
> ```
>
> Reason: `fetch()` does network I/O on the main thread; the call needs to be moved off-main.

Do not propose multiple changes at once. One fix, one reason.

### Step 5: Apply + rebuild + reinstall + verify

1. `Edit` the file with the smallest possible change.
2. `gradlew-mcp.run_task {"task": "assembleDebug", "cwd": ".", "timeout": 300}`.
3. `adb-mcp.install_apk {"serial": "...", "path": "..."}`.
4. `adb-mcp.start_activity {"serial": "...", "package": "...", "activity": ".MainActivity"}`.
5. Re-trigger the original failing action.
6. `adb-mcp.logcat_filter {"tag": "<package>", "level": "ERROR"}` to confirm no new errors.

If the symptom persists, return to Step 2 (different angle). After 3 unsuccessful attempts, escalate to the user with what was tried.

### Step 6: Report (strict limit)

Final output to the user, max 30 lines:

```
FIXED: <one-line description of what was changed>
file: <path:line>
reason: <why this fixes the symptom>
verified: <one-line observation from the re-run>
```

## Anti-rationalizations

| If you catch yourself thinking… | The answer is |
|---|---|
| "The stack trace is clear, skip logcat" | Read the actual logcat — the trace you imagine and the trace on the device differ. |
| "Reproduce is obvious, just fix it" | Prove-It: the repro must FAIL before your fix, or you cannot prove the fix worked. |
| "User said crashes are random, no repro possible" | Random still has a trigger. Capture device state (logcat, layout) before theorizing. |
| "It worked on the emulator, ship it" | Emulator ≠ device. Note the difference; verify on the target if one is connected. |

## Anti-patterns

- **DO NOT** propose multiple changes at once. Iterate.
- **DO NOT** modify code without first reading and showing the snippet.
- **DO NOT** use `adb logcat -c` without user confirmation — destroys evidence.
- **DO NOT** rely on `am force-stop` + `am start` to clear state.
- **DO NOT** continue past 3 unsuccessful attempts without telling the user.

## Pairing

- `android-run` — installs + launches before this skill can debug
- `adb-mcp.logcat_dump`, `adb-mcp.logcat_filter` — log capture
- `gradlew-mcp.run_task` — rebuild after edit

## References

- See [references/strict-output-limit.md](references/strict-output-limit.md)
  for the report-format rules (matches Google's `r8-analyzer` pattern).
