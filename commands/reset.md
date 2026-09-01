---
description: Reset project state (.build-android/state.json) — double-confirm destructive gate.
allowed-tools:
  - Bash
  - Read
---

# /reset

Reset project state. Destructive — requires double confirm.

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null | head -20 || echo "no state.json"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll reset your project state — this clears the plan and cursor. This is destructive. Confirm twice to proceed."

## Your task

Delegate to `$build-android-apps` intent `reset` — ask for double confirm, then `python -m state reset .build-android/state.json`. Preserve `.build-android/snapshot-*` if exists. `$ARGUMENTS`
