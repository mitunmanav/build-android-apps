---
description: Change a plan item's title, phase, or dependencies.
allowed-tools:
  - Bash
---

# /change

Edit an existing plan item. Use it to:

- Rename a task
- Move a task to a different phase
- Update dependencies (e.g. "make X depend on Y")
- Add or change files the task is expected to touch

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`

## Your task

### Step 1: Identify the task

Same resolution rules as `/remove`: by id or title fragment. If ambiguous, ask.

### Step 2: Parse changes from $ARGUMENTS

`$ARGUMENTS` should be in the form:

```
<id-or-fragment> [--title "new title"] [--phase <phase>] [--deps d1,d2] [--files f1,f2]
```

Only the fields you actually want to change. Anything omitted is left alone.

### Step 3: Run the change

```
tool: Bash
args: { "command": "python3 -m state change .build-android/state.json --task <id> [--title ...] [--phase ...] [--deps ...] [--files ...]", "description": "Update plan item" }
```

### Step 4: Confirm

Print the updated item and explain the diff in plain English.

## Anti-patterns

- ❌ Don't change `status` (use `/continue`, `/undo`, or remove+readd for that).
- ❌ Don't change `id` — if you want a new id, remove and add.
- ❌ Don't silently add deps that create cycles — verify with the user first if a cycle is implied.
