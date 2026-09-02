---
description: Undo the last plan mutation (add, remove, change, status change).
allowed-tools:
  - Bash
---

# /undo

Two undo layers, checked in order:

1. **Loop task undo**: if the most recent ledger line is a completed loop
   task (`Task N: complete (commits a..b, ...)`) and the working tree is
   clean, revert that task's commit range (`git revert --no-commit a..b`
   then commit) and ledger `Ruling: Task N reverted — user request —
   state rolled back`. Use this when the loop just built something the user
   doesn't want.
2. **Plan mutation undo** (below): revert the most recent state.json
   mutation. Useful when `/add` added the wrong task, `/remove --hard`
   deleted too much, or a status flip was premature.

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
