---
description: Show where I am in the build loop — current phase, plan progress, and next task. No changes.
allowed-tools:
  - Bash
  - Read
---

# /where

Tell me exactly where we are: which phase, what's done, what's next.

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`

## Your task

Run this and report the result to the user in plain English.

### Step 1: Run the query

```
tool: Bash
args: { "command": "python3 -m state where .build-android/state.json", "description": "Print current phase + plan" }
```

If the file is missing, skip the python call and say: "We haven't started yet. Run `/make-app` to bootstrap your app, or `/setup` if you've never run the plugin before."

### Step 2: Translate to plain English

If state.json exists, take the `where` output and rewrite it for a non-technical user. Example:

> We're in the **build** phase. Of 4 plan items, 1 is done, 1 is in progress, 2 are pending.
>
> ✓ Add home screen
> ▶ Build the app
> · Set up notifications
> · Submit to Play Store
>
> Next up: **Set up notifications**. Say "go" or run `/continue`.

### Step 3: Report

- Print the translated summary.
- Do NOT mutate state.json. If the user wanted to advance, they should run `/continue`.

## Anti-patterns

- ❌ Don't mutate state.json in response to `/where`. This is read-only.
- ❌ Don't auto-run `/continue` after `/where` — wait for explicit user input.
