---
name: android-icons-assets
description: >
  Generate launcher icon, adaptive layers, feature graphic, and store
  screenshots for an Android app. Use this when the user asks for a logo,
  icon, feature graphic, or screenshots, or as part of /publish. Do not use
  for in-app icons (use material icons), for animated splash (use Compose),
  or for icon-source editing.
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [icon, adaptive, feature-graphic, screenshots, store-listing]
---

# Android Icons + Assets

> [!NOTE]
> Two-tier checklist: agent self-check (always) + user checklist (always ask).

## Prerequisites

- A scaffolded project
- The app's `application_id` (from `state.json` or `gradlew-mcp.describe_project`)
- An image source (user's logo) or permission to generate from spec

## Workflow

### Step 1: Two-tier checklist (BEFORE generating)

**Agent self-check (always):**
- [ ] Source image is at least 1024×1024 px (or spec says "generate from scratch")
- [ ] Target file paths exist (or will be created)
- [ ] Output dimensions match Play Store requirements:
  - `ic_launcher`: 48dp / 72dp / 96dp / 144dp / 192dp × hdpi/xhdpi/xxhdpi/xxxhdpi
  - Adaptive layers: 108dp × hdpi/xhdpi/xxhdpi/xxxhdpi (foreground + background + monochrome)
  - Feature graphic: 1024×500
  - Screenshots: 1080×1920 minimum, 3200×3840 max

**User checklist (ask before generating):**
- [ ] What color should the icon be?
- [ ] Should it include the app name as text, or be icon-only?
- [ ] What's the visual concept? (abstract / letter / object / photo)
- [ ] Are there brand colors or fonts I should match?

### Step 2: Generate via asset-mcp

For launcher icon:
```
tool: mcp__plugin_build_android_app_plugin_asset__generate_icon
args: { "source": "<path>", "out_dir": "app/src/main/res" }
```

For feature graphic:
```
tool: mcp__plugin_build_android_app_plugin_asset__generate_feature_graphic
args: { "source": "<path>", "out": "feature-graphic.png" }
```

For store screenshots (from a running app on device):
```
tool: mcp__plugin_build_android_app_plugin_asset__generate_screenshot
args: { "adb_serial": "<serial>", "out": "screenshots/home.png" }
```

### Step 3: Place files

Verify files exist at:
- `app/src/main/res/mipmap-mdpi/ic_launcher.png`
- `app/src/main/res/mipmap-mdpi/ic_launcher_round.png`
- `app/src/main/res/mipmap-mdpi/ic_launcher_foreground.png`
- `app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` (adaptive)
- `feature-graphic.png` (project root, for Play Store upload)
- `screenshots/home.png`, `screenshots/screen2.png`, etc.

If `mipmap-anydpi-v26/ic_launcher.xml` is missing, create it:

```xml
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
```

### Step 4: Verify

```
tool: mcp__plugin_build_android_app_plugin_gradlew__run_task
args: { "task": "assembleDebug", "cwd": ".", "timeout": 600 }
```

Launch on a device. Take a screenshot. Confirm the icon shows correctly in the launcher.

### Step 5: User sign-off

> Here's what I generated. Look at the icon, feature graphic, and screenshots. Approve, or tell me what to change.

## Anti-patterns

- **DO NOT** generate without asking the user for the visual concept first.
- **DO NOT** use copyrighted images. Generate or use the user's own.
- **DO NOT** skip the two-tier checklist. It catches the most common errors.
- **DO NOT** generate screenshots at <1080×1920. Play Store rejects small ones.

## Pairing

- `/screenshots` slash command — for screenshot-only runs
- `android-store-listing` — consumes the screenshots and feature graphic

## References

- See [references/asset-sizes.md](references/asset-sizes.md) for the
  full Play Store asset size table.
