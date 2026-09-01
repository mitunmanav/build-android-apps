---
description: Undo the last plan mutation (add, remove, change, status change).
allowed-tools:
  - Bash
---

# /undo

Revert the most recent change to the plan. Useful when:

- `/add` added the wrong task
- `/remove --hard` deleted too much
- `/change` produced the wrong title or phase
- A status flip (pending → in_progress) was premature

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, tell the user: "I'll revert the last change. Tell me if you'd rather not."

## Your task

### Step 1: Run undo

```
tool: Bash
args: { "command": "python3 -m state undo .build-android/state.json", "description": "Undo last mutation" }
```

### Step 2: Report

- If `{"action": "undone", "entry": {...}}`: print what was reverted:
  > Undone: `<summary>` at `<at>`. The state is now as it was before.
- If `"nothing to undo"`: say "Nothing to undo — your plan has no recent mutations."
- If `"undo_failed"`: say "Can't undo that one — the snapshot was rotated out of the ring buffer."

### Step 3: Suggest follow-up

After a successful undo, suggest:

> Run `/where` to see your plan as it stands now.

## Anti-patterns

- ❌ Don't chain undos silently. Each one is a separate, user-visible action.
- ❌ Don't undo mutations older than the 50-entry ring buffer — surface that limitation.
