---
description: Start a brand-new Android app from a one-line description. Drives intake, planning, and scaffolding.
allowed-tools:
  - Bash
  - Read
  - Write
---

# /make-app

Bootstrap a brand-new Android app from a one-line description. Walks the user through intake → spec → plan → scaffold.

## Context

- Working directory: !`pwd`
- Project layout: !`ls -la | head -10`
- State file: !`ls .build-android/state.json 2>/dev/null && echo "(exists)" || echo "(none)"`

## Reporting Action

> [!IMPORTANT]
> Before invoking the tool, say: "I'll start a new Android app. Tell me in 1-3 sentences what it should do."

## Your task

### Step 1: Collect the prompt

`$ARGUMENTS` is the user's idea. If empty, ask the user.

### Step 2: Bootstrap state.json

```
tool: Bash
args: { "command": "mkdir -p .build-android && python3 -m state save .build-android/state.json '{\"schema_version\":1,\"phase\":\"intake\",\"plan\":[],\"cursor\":{\"phase\":\"intake\",\"task_id\":\"\"},\"history\":[]}'", "description": "Init state.json" }
```

### Step 3: Run app-intake

Load `skills/app-intake/SKILL.md` and follow its steps. Ask the user 1-5 plain-English questions, then write `.build-android/spec.md`.

### Step 4: Run app-planner

Load `skills/app-planner/SKILL.md` and follow its steps. Persist plan items to state.json.

### Step 5: Confirm + offer next

Print the routed plan and ask:

> Run `/continue` to start on item 1, or `/where` to review the plan first.

## Anti-patterns

- **DO NOT** skip the intake step. The user might have a different idea than what they typed.
- **DO NOT** auto-scaffold without a confirmed plan.
- **DO NOT** overwrite an existing state.json without confirming with the user.
