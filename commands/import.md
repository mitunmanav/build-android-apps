---
description: Import an existing Android project from another tool. Snapshots first, audits, offers /finish.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_gradlew__describe_project
---

# /import

Take ownership of an existing Android project. Snapshots first, audits for Play Store readiness, offers /finish.

## Context

- Working directory: !`pwd`
- Project layout: !`ls -la | head -10`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll snapshot your project first so we can roll back if needed. Then I'll audit it for Play Store readiness."

## Your task

### Step 1: Snapshot

Run the snapshot step from `skills/android-importer/SKILL.md` Step 1.

### Step 2: Run importer

Follow Steps 2-5 of the importer skill.

### Step 3: Hand off

Print the import report and ask:

> Run `/audit` for a deeper check, or `/finish` to auto-fill the gaps and publish.

## Anti-patterns

- **DO NOT** modify any project file during import. Read-only until the user approves a /finish plan.
- **DO NOT** skip the snapshot. Users will regret losing their work.
