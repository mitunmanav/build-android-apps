---
description: Diagnose a Play Store rejection and propose a fix. Reads state.json rejections, dispatches the release-auditor subagent.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_play_store__list_rejections
  - mcp__plugin_build_android_apps_play_store__get_review_status
---

# /why-rejected

Tell me why Play Store rejected my submission and how to fix it.

## Context

- State: !`cat .build-android/state.json 2>/dev/null | head -30 || echo "no state.json"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll fetch the rejection reasons from state.json and dispatch the release-auditor subagent to diagnose each one."

## Your task

### Step 1: Pull rejections

```
tool: mcp__plugin_build_android_apps_play_store__list_rejections
args: { "package_name": "<from spec.md>" }
```

If the response is empty, ask the user to paste the rejection email or read Play Console manually. The Play Console doesn't expose a public "list rejections" endpoint.

### Step 2: Dispatch release-auditor

For each rejection in the list, dispatch `release-auditor` (subagent) with the rejection id + reason.

### Step 3: Synthesize

Group fixes by file/topic:
- **Privacy policy**: edit spec.md, upload new policy URL, /finish again
- **Account deletion**: wire `deleteAccount()` per android-auth
- **Permissions**: remove unused `<uses-permission>` from AndroidManifest.xml
- **Content rating**: update the questionnaire answers in Play Console
- **Target API**: bump targetSdk to latest-stable

### Step 4: Suggest next

> Pick the fix and I'll apply it, or run /finish again with the new spec.

## Anti-patterns

- **DO NOT** blindly re-submit. The same rejection will come back.
- **DO NOT** delete the rejected release. The new one needs to be a replacement.
