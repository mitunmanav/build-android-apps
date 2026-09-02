---
description: Continue the build loop — pick the next pending task and start working on it.
allowed-tools:
  - Bash
  - Read
---

# /continue

Resume the loop. If a plan run was interrupted, the `agent-orchestrator`
skill rebuilds its position from the ledger + resume.md and continues where
it left off. If only the next single task is wanted, use the state CLI
directly (below).

## Context

- Working directory: !`pwd`
- State file: !`ls -la .build-android/state.json 2>/dev/null || echo "no state.json yet"`
- Loop state: !`python3 -c "import json;d=json.load(open('.build-android/state.json'));o=d.get('orchestration',{});print(o.get('status','idle'), o.get('mode','guided'))" 2>/dev/null || echo idle`

## Reporting Action

> [!IMPORTANT]
> Before invoking, tell the user in one sentence: "I'll pick up where things
> left off — say the word if you'd rather just see the status."

## Your task

### Step 0: Route by loop state

- If state.json exists and `orchestration.status` is `running` or `stopped`
  (a run was interrupted): invoke the `agent-orchestrator` skill — it resumes
  from the ledger at the first task without a `complete` line (or the next
  fix round). Do NOT re-plan or re-ask what state already knows.
- Otherwise (plain phase loop): advance one task:

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
