---
description: Remove a task from the build plan. Soft (skip) by default; hard delete with --hard.
allowed-tools:
  - Bash
  - Read
---

# /remove

Remove a task from the build plan. Two modes:

- **Soft (default)**: marks the task as `skipped`. The agent won't work on it. Easy to undo.
- **Hard (`--hard`)**: deletes the task from the plan entirely. Cannot be undone via `/undo`.

Use soft unless the task was a complete mistake. Hard delete is for cleaning up duplicate entries.

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`

## Reporting Action

> [!IMPORTANT]
> If `--hard` was requested, confirm with the user before invoking the tool: "This will permanently delete the task. Proceed?"

## Your task

### Step 1: Identify the task

`$ARGUMENTS` is either:
- A task id (e.g. `a3f8b2c1`)
- A title fragment (e.g. `"the settings screen"`)

If by id, use directly. If by fragment, run:

```
tool: Bash
args: { "command": "python3 -m state load .build-android/state.json", "description": "List tasks to find id" }
```

Then pick the best match. If ambiguous, ask the user.

### Step 2: Run the remove

Soft:

```
tool: Bash
args: { "command": "python3 -m state remove .build-android/state.json --task <id>", "description": "Skip task" }
```

Hard:

```
tool: Bash
args: { "command": "python3 -m state remove .build-android/state.json --task <id> --hard", "description": "Delete task (irreversible)" }
```

### Step 3: Confirm

- Soft: "Skipped **[id]** — `<title>`. Run `/undo` to restore."
- Hard: "Deleted **[id]** — `<title>`."

## Anti-patterns

- ❌ Don't hard-delete without explicit `--hard` from the user.
- ❌ Don't auto-clean files the task touched. The user can do that manually or via a follow-up task.
