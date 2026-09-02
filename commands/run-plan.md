---
description: Execute the whole plan autonomously — orchestrator runs task-by-task with reviews and evidence until done.
allowed-tools:
  - Bash
  - Read
  - Grep
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_gradlew__run_help
  - mcp__plugin_build_android_apps_gradlew__run_build_dry
  - mcp__plugin_build_android_apps_adb__list_devices
---

# /run-plan

Run the plan end-to-end via the `agent-orchestrator` skill: a fresh
implementer per task, device evidence, two read-only reviewers per task, a
bounded fix loop, and a resumable ledger. You can walk away — it stops only
for destructive actions, publishing, security issues, or a broken plan.

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null | head -5 || echo "no state yet"`
- Pending: !`python3 -m state summary .build-android/state.json 2>/dev/null || echo "no state"`

## Reporting Action

> [!IMPORTANT]
> Before starting, tell the user in one sentence: "I'll run the plan task by
> task — building, checking on the device, and reviewing each step. I'll
> report back in plain English when it's done or if I need you."

## Your task

Invoke the `agent-orchestrator` skill and follow its Workflow exactly,
starting at Step 1 (pre-flight). If no state.json exists, route to
`app-intake` first — there is nothing to run yet.

## Anti-patterns

- **DO NOT** run tasks inline yourself — dispatch implementers; you coordinate.
- **DO NOT** read implementer reports or diffs into your context.
- **DO NOT** continue past the staleness cap (3) or fix-round cap (5).

## Final Checklist

- [ ] Pre-flight passed before task 1
- [ ] Every task has a ledger line; no silent discards
- [ ] Plain-English final report delivered (what was built, evidence, parked items)
