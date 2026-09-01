---
description: Continue the build loop — pick the next pending task and start working on it.
allowed-tools:
  - Bash
  - Read
---

# /continue

Resume the build loop. The agent picks the next pending task whose dependencies are all done, marks it in-progress, and tells you what it's about to do.

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`

## Reporting Action

> [!IMPORTANT]
> Before invoking the tool, tell the user in one sentence what you are about to do: "I'll mark the next pending task as in-progress and tell you what it is."

## Your task

### Step 1: Run the continue command

```
tool: Bash
args: { "command": "python3 -m state continue .build-android/state.json", "description": "Advance to next pending task" }
```

If the response says `"action": "noop"`, tell the user:

> Nothing pending. The plan is complete, or we need a new task — try `/add "..."` to add one.

### Step 2: Tell the user what's next

Print the task `title` and `phase` in plain English. Example:

> Next up: **Set up notifications** (build phase). I'll start on this now.

Then either:
- Run the appropriate skill for that phase (e.g. load `android-ops` for the notifications phase), OR
- Ask the user for any missing inputs before proceeding.

## Anti-patterns

- ❌ Don't start a new phase automatically if the user hasn't approved it. `/continue` marks in-progress but the actual work still needs user buy-in for non-trivial steps.
- ❌ Don't loop `/continue` if no task moved — surface the blocker instead.
