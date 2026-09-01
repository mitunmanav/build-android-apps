---
description: Install + launch + screenshot the app on a connected device. Reports what it sees.
allowed-tools:
  - mcp__plugin_build_android_apps_adb__list_devices
  - mcp__plugin_build_android_apps_adb__select_device
  - mcp__plugin_build_android_apps_adb__install_apk
  - mcp__plugin_build_android_apps_adb__start_activity
  - mcp__plugin_build_android_apps_adb__screencap
  - mcp__plugin_build_android_apps_gradlew__describe_project
  - mcp__plugin_build_android_apps_gradlew__run_task
---

# /preview

Install + launch + screenshot the app. One-shot. No fixes (use `/build` then come back).

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null | head -20 || echo "no state.json"`

## Reporting Action

> [!IMPORTANT]
> Before invoking, say: "I'll install your app on the connected device and take a screenshot. This takes about 1-2 minutes."

## Your task

### Step 1: Confirm APK exists

```
tool: mcp__plugin_build_android_apps_gradlew__describe_project
args: { "cwd": "." }
```

If the response says `is_android_app: false` or the APK path doesn't exist, run `assembleDebug` first:

```
tool: mcp__plugin_build_android_apps_gradlew__run_task
args: { "task": "assembleDebug", "cwd": ".", "timeout": 600 }
```

### Step 2: Load android-run skill

Follow `skills/android-run/SKILL.md` Steps 1-6. Pick device, install, launch, capture.

### Step 3: Show the screenshot

Print the path to the user. If your host supports it, embed the image inline. Then ask:

> Does this look right? If something's off, tell me what you see and I'll fix it.

## Anti-patterns

- **DO NOT** reinstall over an existing install with mismatched signatures without asking.
- **DO NOT** auto-launch on multiple devices — ask which one first.
- **DO NOT** claim success without actually capturing the screenshot.
