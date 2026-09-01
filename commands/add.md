---
description: Add a new task to the build plan. Use this to add features, screens, or fixes mid-flight without restarting.
allowed-tools:
  - Bash
---

# /add

Add a new task to the build plan without restarting anything. Use it when:

- You want a new feature, screen, or fix added to an in-flight project
- You want the agent to remember something for later
- You want to inject a manual checkpoint

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`

## Reporting Action

> [!IMPORTANT]
> State out loud what you're about to add: "I'll add this to your plan: **<title>** in the **<phase>** phase."

## Your task

### Step 1: Parse $ARGUMENTS

`$ARGUMENTS` is a free-form description like `"add a settings screen"` or `"add notifications after the build is done"`. Extract:

- **title** (required) — short name for the task
- **phase** (required) — one of `intake`, `plan`, `scaffold`, `build`, `test`, `publish`, `update`
- **deps** (optional) — task ids that must be done first; only auto-detect if user named them ("after X is done")
- **files** (optional) — file paths this task touches

If the user didn't specify a phase, ask before adding. Don't guess.

### Step 2: Run the add command

```
tool: Bash
args: { "command": "python3 -m state add .build-android/state.json --title '<title>' --phase <phase> [--deps <id1,id2>] [--files <f1,f2>]", "description": "Add plan item" }
```

### Step 3: Confirm

Print the new task to the user:

> Added **[id]** to your plan: **<title>** in the **<phase>** phase.

Then ask whether to run it now or later.

## Anti-patterns

- ❌ Don't infer phase silently. If unclear, ask.
- ❌ Don't add duplicate tasks without warning the user.
- ❌ Don't run the task immediately after adding — wait for explicit "go".
