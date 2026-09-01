---
description: Auto-fill the gaps from /audit + submit to Play Store internal test track.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_keystore__generate
  - mcp__plugin_build_android_apps_keystore__verify
  - mcp__plugin_build_android_apps_keystore__fingerprint
---

# /finish

Auto-fix the gaps from `/audit` and ship to Play Store internal test track.

## Context

- Working directory: !`pwd`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll auto-fix gaps and publish to Play Store internal test track. This builds a signed AAB and uploads it. Confirm when ready."

## Your task

### Step 1: Run /audit first

If /audit hasn't been run in this session, run it now. Print the gap list.

### Step 2: Plan the fixes

For each gap, decide: fix automatically, or ask the user?

| Gap | Auto-fix? |
|---|---|
| Missing signing config | Ask user for keystore password |
| Missing Crashlytics | Auto-add (silent) |
| Missing launcher icon | Auto-generate via `asset-mcp` (Phase 11) |
| Missing privacy policy | Auto-generate template; user fills in URL |
| Missing tests | Skip; recommend /test instead |
| Lint errors | Show first; ask user |

### Step 3: Apply fixes

For each auto-fix, do the smallest possible change. Build between fixes if any are interdependent.

### Step 4: Build signed release AAB

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "bundleRelease", "cwd": ".", "timeout": 600 }
```

Verify the AAB exists at `app/build/outputs/bundle/release/app-release.aab`.

### Step 5: Publish

Use the play-store-mcp tools (Phase 13). Upload the AAB to internal test track. Print the draft URL.

## Anti-patterns

- **DO NOT** skip the audit. Shipping without knowing what's broken wastes Play Store review cycles.
- **DO NOT** generate a keystore without warning the user to back it up.
- **DO NOT** submit to production track. Internal test only.
