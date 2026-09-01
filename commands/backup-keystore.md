---
description: Back up upload keystore to safe location — warns to keep it safe.
allowed-tools:
  - Bash
  - Read
  - mcp__plugin_build_android_apps_keystore__backup
  - mcp__plugin_build_android_apps_keystore__fingerprint
---

# /backup-keystore

Back up upload keystore.

## Context

- Working directory: !`pwd`
- Keystore: !`ls -lh .build-android/upload-keystore.jks 2>/dev/null || echo "no keystore"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll back up your upload keystore. Keep the backup safe — losing it means you can't update your app."

## Your task

Delegate to `$build-android-apps` intent `backup-keystore` — call `keystore-mcp backup` to copy to user-chosen safe path. Verify fingerprint. `$ARGUMENTS`
