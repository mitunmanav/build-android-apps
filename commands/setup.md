---
description: First-run setup wizard. Idempotent. Run only when state.json or /setup indicates first-run.
allowed-tools:
  - Bash
  - mcp__plugin_build_android_app_plugin_gradlew__manage_sdk
  - mcp__plugin_build_android_app_plugin_gradlew__generate_keystore
---

# /setup

First-run setup wizard. Walks you through SDK install, Play Console signup, service account, and upload keystore.

## Context

- OS: !`uname -a 2>/dev/null || echo "$OS"`
- Java: !`java -version 2>&1 | head -3 || echo "java not found"`
- ANDROID_HOME: !`echo "${ANDROID_HOME:-not set}"`
- adb: !`command -v adb && adb version | head -1 || echo "adb not found"`
- adb devices: !`adb devices 2>/dev/null || echo "adb not found"`
- Existing state.json: !`ls .build-android/state.json 2>/dev/null || echo "none"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll walk you through 10 setup steps. Each takes 1-3 minutes. Total ~30 minutes. You can stop at any time and resume by running `/setup` again."

## Your task

### Step 1: Run setup-wizard

Load `skills/setup-wizard/SKILL.md` and follow its 10 steps in order.

### Step 2: Record completion

After all 10 steps pass:

```
tool: Bash
args: { "command": "python3 -m state save .build-android/state.json '{\"schema_version\":1,\"phase\":\"idle\",\"plan\":[],\"cursor\":{\"phase\":\"idle\",\"task_id\":\"\"},\"environment\":{\"sdk_installed\":true,\"jdk_installed\":true,\"adb_in_path\":true,\"play_console_email\":\"<from user>\",\"billing_setup\":true},\"history\":[]}'", "description": "Persist setup complete" }
```

### Step 3: Hand off

> Setup complete! Next, run `/make-app "<your idea>"` to start building your first app.

## Anti-patterns

- **DO NOT** skip steps. The Play Console steps are non-skippable for any user who wants to publish.
- **DO NOT** save the service account JSON file path or password in chat history.
- **DO NOT** run this wizard if state.json shows `environment.sdk_installed=true` AND all other env flags are set. Tell the user to use `/reset` only if they want to start over.
