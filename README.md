<div align="center">

# Build Android App Plugin

**The only plugin needed to build and ship Android apps from your AI assistant.**

Type `/make-app "a habit tracker"` and ship a signed AAB to the Play Store internal test track — without writing Kotlin yourself.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-3DDC84.svg)](CHANGELOG.md)
[![Host: Codex CLI](https://img.shields.io/badge/host-Codex_CLI-000.svg)](https://developers.openai.com/codex/plugins/)
[![Host: Claude Code](https://img.shields.io/badge/host-Claude_Code-D97757.svg)](https://docs.claude.com/en/docs/claude-code/plugins)
[![Host: .agents](https://img.shields.io/badge/host-.agents-6E56CF.svg)](https://agentskills.io/specification)
[![Platform: Android](https://img.shields.io/badge/platform-Android-3DDC84.svg?logo=android)](https://developer.android.com)
[![Pairs: android/skills](https://img.shields.io/badge/pairs_with-android%2Fskills-4285F4.svg)](https://github.com/android/skills)

</div>

---

## Table of Contents

- [Why this plugin](#why-this-plugin)
- [Quick start](#quick-start)
- [What you can do](#what-you-can-do)
- [Architecture](#architecture)
- [The 22 skills](#the-22-skills)
- [The 21 commands](#the-21-commands)
- [The 5 MCP servers](#the-5-mcp-servers)
- [Prerequisites](#prerequisites)
- [Install](#install)
- [Pairs with](#pairs-with)
- [Compatibility](#compatibility)
- [Limitations (v1.0)](#limitations-v10)
- [Contributing](#contributing)
- [License & author](#license--author)

---

## Why this plugin

You know the build loop. You know Gradle, adb, signing, listing, the Play Store API. Now imagine your AI assistant knows it too — and never forgets, never gets distracted, and follows the same patterns every time.

This plugin encodes that knowledge. 22 skills cover the full Android lifecycle. 21 slash commands use plain English, not dev jargon. 6 hooks gate destructive actions. 5 MCP servers drive the actual tools. A per-project state file makes every loop resumable.

**It's not for Android engineers.** It's for the vibe coder, the indie founder, the technical facilitator running the plugin for non-technical clients. It replaces 20 Stack Overflow tabs and 4 different Google sign-in flows with one `/make-app` and a 30-minute setup.

> *"Write me a habit tracker with daily reminders."* — that's the whole prompt. The rest is the plugin's job.

---

## Quick start

```text
# 1. One-time setup (~30 minutes)
/setup
# 10 steps: JDK → Android SDK → adb → emulator → Play Console →
#           Google Cloud → service account → upload keystore

# 2. Build your first app
/make-app "a habit tracker with daily reminders"
# intake (asks 1-5 plain-English questions) → spec → plan → scaffold

# 3. Preview on device
/preview
# installs + launches + screenshots

# 4. Ship to internal test track
/publish
# signs AAB + uploads + reports draft URL

# 5. After Google reviews
/update
# bump version + changelog + resubmit
```

That's it. No Kotlin. No Gradle files. No Play Console wiring.

---

## What you can do

- **Turn a one-liner into a working app.** `/make-app "<idea>"` runs the full intake → spec → plan → scaffold loop.
- **Take ownership of an existing project.** `/import` snapshots first (so you can roll back), audits, and lists gaps.
- **Add features mid-flight without restart.** `/add "user profiles with avatars"` mutates the build plan; the phase-router runs only what's affected.
- **Debug runtime crashes on device.** `/debug` attaches the JDWP debugger; the `android-debug-fix` skill captures logcat, localizes the call site, edits the smallest possible change, rebuilds.
- **Ship a signed AAB.** `/publish` uploads to the Play Store internal test track; the PreSubmit hook refuses the upload if the keystore, listing, or screenshots are missing.
- **Diagnose rejections.** `/why-rejected` parses the rejection list, dispatches the `rejection-parser` subagent, and groups fixes by file.
- **Generate store assets.** `asset-mcp` produces launcher icons at all densities, adaptive layers, feature graphic, and Play Store screenshots.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│   AI Host:  Codex CLI  ·  Claude Code CLI  ·  .agents standard   │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│   Plugin manifests (3 hosts)  +  plugin.lock.json (sha256-pinned)│
└──────────────┬────────────────┬───────────────────────┬──────────┘
               │                │                       │
               ▼                ▼                       ▼
         Skills (22)    Commands (21, plain EN)   MCP servers (5)
         references/    /make-app, /add, /change,  adb, gradlew,
         per skill      /publish, /where, /undo    play-store, keystore, asset
               │                │                       │
               ▼                ▼                       ▼
         Subagents (6)    Hooks (6) + monitors/    Phase router
         intake-clarifier SessionStart, Pre,        (Kahn's algorithm;
         build-validator  Post, PreSubmit, Stop    deterministic, no LLM)
         release-readiness
         rejection-parser
         phase-router
         asset-generator
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│   <project>/.build-android/state.json   (gitignored, per project)│
│   schema_version · phase · plan[] · cursor · build · device ·    │
│   store · keystore · environment · crashlytics · rejections ·   │
│   history[50]                                                    │
└──────────────────────────────────────────────────────────────────┘
```

The **state file** is the source of truth. Every `/add`, `/change`, `/remove`, `/undo`, `/continue` mutates it. `/where` reads it. The phase-router reads it to compute the minimal phase sequence (Kahn's algorithm — no LLM call).

---

## The 22 skills

Every skill is a Markdown file at `skills/<name>/SKILL.md` with a `references/` folder for detail. Use `$<skill>` (Codex) or `<skill>` (Claude) to invoke.

| # | Skill | Purpose | MCP deps |
|---|---|---|---|
| 1 | [`app-intake`](skills/app-intake/SKILL.md) | Vague prompt → spec via 1-5 plain-English questions | (state.json) |
| 2 | [`app-planner`](skills/app-planner/SKILL.md) | Spec → sequenced build plan in state.json | (state.json) |
| 3 | [`android-scaffold`](skills/android-scaffold/SKILL.md) | Bootstrap Gradle + Compose + signing + Crashlytics | `gradlew-mcp` |
| 4 | `android-build` | assembleDebug/release, lightweight verification gates | `gradlew-mcp` |
| 5 | [`android-run`](skills/android-run/SKILL.md) | Install + launch + screenshot | `adb-mcp` |
| 6 | [`android-debug-fix`](skills/android-debug-fix/SKILL.md) | Logcat + agent-driven fix loop (3-strike limit) | `adb-mcp` |
| 7 | `android-ui-patterns` | Compose patterns: lists, nav, forms, state hoisting | — |
| 8 | `android-performance` | Recomposition, stability, baseline profiles | `gradlew-mcp` |
| 9 | `android-test` | Screenshot tests on 9 grid sizes + smoke tests | `gradlew-mcp` |
| 10 | [`android-importer`](skills/android-importer/SKILL.md) | Take ownership of Lovable/Bolt/v0/Cursor-built projects | `gradlew-mcp` |
| 11 | [`android-backend`](skills/android-backend/SKILL.md) | Room + DataStore + Supabase + Firebase templates | — |
| 12 | [`android-auth`](skills/android-auth/SKILL.md) | Credential Manager + Google + email + passkey | — |
| 13 | [`android-ops`](skills/android-ops/SKILL.md) | FCM + Analytics + WorkManager + Crashlytics verify | — |
| 14 | [`android-media`](skills/android-media/SKILL.md) | CameraX + Media3 ExoPlayer | — |
| 15 | `android-restore-credentials` | Sign in across devices via restore keys | — |
| 16 | `android-verified-email` | OTP-less email verification (SD-JWT VC) | — |
| 17 | [`android-edge-to-edge`](skills/android-edge-to-edge/SKILL.md) | SDK 35+ mandatory edge-to-edge | — |
| 18 | [`android-icons-assets`](skills/android-icons-assets/SKILL.md) | Launcher icon + adaptive layers + feature graphic | `asset-mcp` |
| 19 | [`android-store-listing`](skills/android-store-listing/SKILL.md) | Title/desc/short/long/screenshots/privacy/data safety | — |
| 20 | `android-play` | Play Store submission flow | `play-store-mcp` |
| 21 | [`android-publish-update`](skills/android-publish-update/SKILL.md) | Bump version + changelog + signed AAB + re-upload | `play-store-mcp`, `keystore-mcp` |
| 22 | `android-r8-analyzer` | APK size + keep-rule audit (strict 30-line output) | `gradlew-mcp` |
| ★ | [`setup-wizard`](skills/setup-wizard/SKILL.md) | First-run 10-step onboarding | `gradlew-mcp`, `play-store-mcp` |

> Every skill follows the same body pattern: Prerequisites → Workflow (numbered steps) → Anti-patterns → Pairing → References → Final Checklist.

---

## The 21 commands

Plain English. No gradlew jargon.

| Command | What it does |
|---|---|
| `/setup` | First-run wizard (SDK, Play Console, service account, keystore) |
| `/make-app "<idea>"` | Start a new app from a one-liner |
| `/add "<feature>"` | Add a feature without restarting |
| `/change "<spec>"` | Modify an existing plan item |
| `/remove` | Remove or skip a task |
| `/continue` | Resume the build loop |
| `/where` | Show current phase + plan progress |
| `/status` | Post-publish dashboard (downloads, ratings, crashes) |
| `/publish` | Store listing + submit to internal test track |
| `/update` | New version + changelog + resubmit |
| `/reset` | Reset project state (double-confirm) |
| `/backup-keystore` | Copy keystore to safe place (Google Drive, USB) |
| `/why-rejected` | Diagnose a Play Store rejection |
| `/import` | Detect existing Android project |
| `/audit` | Deep audit for Play Store readiness |
| `/finish` | Auto-fill gaps + publish to internal test |
| `/screenshots` | Generate store screenshots |
| `/privacy-policy` | Generate privacy policy template |
| `/help` | List commands in plain English |
| `/preview` | Install + launch + screenshot the app |
| `/debug` · `/lint` | Dev aliases |

---

## The 5 MCP servers

All Python (MCP SDK), all stdio, all dependency-light.

| Server | Tools | What it does |
|---|---|---|
| **adb-mcp** | 17 | `list_devices`, `install_apk`, `start_activity`, `screencap`, `logcat_filter` (subscribable), `dump_layout` (JSON UI tree), … |
| **gradlew-mcp** | 12 | `list_tasks`, `run_task`, `describe_project` (matches `android describe`), `manage_sdk`, `run_help` + `run_build_dry` (lightweight gates), `generate_keystore` + `verify_keystore`, … |
| **play-store-mcp** | 9 | `auth`, `upload_aab`, `upload_listing`, `get_review_status`, `list_rejections`, `submit_for_review`, `rollout_staged`, `get_stats` |
| **keystore-mcp** | 5 | `generate`, `verify`, `rotate`, `backup`, `fingerprint` |
| **asset-mcp** | 4 | `generate_icon` (5 densities + adaptive), `generate_feature_graphic` (1024×500), `generate_screenshot` (1080×1920), `compose_marketing` |

---

## Prerequisites

Auto-detected by the SessionStart hook. If anything's missing, `/setup` walks you through it.

- **JDK 17+** with `JAVA_HOME` set
- **Android SDK** with `ANDROID_HOME` set; `cmdline-tools`, `platform-tools`, `build-tools;35.0.0`, `platforms;android-35`
- **`adb`** on `PATH` (`$ANDROID_HOME/platform-tools/adb`)
- **Python 3.10+** for the MCP servers
- An **Android device or emulator** for runtime verification
- A **Play Console account** ($25, paid once)
- A **service account JSON key** from Google Cloud (free, ~5 min to create)

---

## Install

### Codex CLI

```bash
codex plugin install github.com/mitunmanav/build-android-app-plugin
```

Or for local development:

```bash
git clone https://github.com/mitunmanav/build-android-app-plugin
cd build-android-app-plugin
codex --plugin-dir .
```

### Claude Code CLI

```bash
claude plugin marketplace add mitun/mitun
claude plugin install build-android-app-plugin@mitun
```

Or load directly:

```bash
git clone https://github.com/mitunmanav/build-android-app-plugin
cd build-android-app-plugin
claude --plugin-dir .
```

### `.agents` open-standard hosts

```bash
git clone https://github.com/mitunmanav/build-android-app-plugin \
  ~/.agents/plugins/build-android-app-plugin
```

Then restart your host (VS Code Copilot, Cursor, Gemini CLI, etc.).

### Pair with Google's android/skills

```bash
android skills add --all
```

---

## Pairs with

This plugin complements, does not replace:

- **[`openai/plugins/test-android-apps`](https://github.com/openai/plugins)** — advanced profiling (Perfetto, Simpleperf, heap dumps). Install alongside for power profiling.
- **[`android/skills` (Google)](https://github.com/android/skills)** — 16 domain SKILLs (Compose, camera, media, navigation, performance, security, etc.). Install via `android skills add --all`.
- **[`ayush016/android-lead-agent-skills`](https://github.com/ayush016/android-lead-agent-skills)** — team standards reference. Copy patterns into your project's `AGENTS.md`.

---

## Compatibility (pinned)

| Component | Version | Source |
|---|---|---|
| Android Gradle Plugin | 8.7+ | `android-scaffold/references/versions-pinned.md` |
| Gradle | 8.9+ | `android-scaffold/references/versions-pinned.md` |
| Kotlin | 2.0.21 | `android-scaffold/references/versions-pinned.md` |
| Compose BOM | 2024.12.01 | `android-scaffold/references/versions-pinned.md` |
| Material 3 | 1.3.1 | `android-scaffold/references/versions-pinned.md` |
| Navigation Compose | 2.8.4 | `android-scaffold/references/versions-pinned.md` |
| Hilt | 2.52 | `android-scaffold/references/versions-pinned.md` |
| Room | 2.6.1 | `android-scaffold/references/versions-pinned.md` |
| DataStore | 1.1.1 | `android-scaffold/references/versions-pinned.md` |
| CameraX | 1.4.1 | `android-scaffold/references/versions-pinned.md` |
| Media3 | 1.4.1 | `android-scaffold/references/versions-pinned.md` |
| min SDK | 26 (Android 8.0, ~98% coverage) | SPEC §16 |
| target SDK | latest-stable | ask during intake |
| JVM target | 17 | SPEC §16 |

---

## Limitations (v1.0)

| Out of scope | Will be addressed in |
|---|---|
| iOS, Wear, TV, Auto, XR | sibling plugins TBD |
| Custom backend hosting (raw) | v1.1 (Firebase + Supabase only today) |
| Multi-user collaboration | v1.1+ (single-user per project state.json) |
| Advanced IAP / subscriptions | v1.1 (basic consumable IAP template only) |
| AGP 9.x | v1.1 (AGP 8.7 stable for v1.0) |
| State schema v2+ migrations | v1.1 (only v1 schema supported) |

---

## Contributing

PRs welcome. Each slice should:

1. Pass `bash scripts/smoke.sh` locally
2. Pass the `smoke` GitHub Actions workflow on your PR
3. Update the affected docs (skills/, commands/, SPEC.md)
4. Stay under the project's [Apache-2.0](LICENSE) license
5. Author: **Mitun only**. No `Co-authored-by:` footers.

The repo uses:

- **Semantic Versioning** ([semver.org](https://semver.org))
- **Keep a Changelog** ([keepachangelog.com](https://keepachangelog.com/en/1.1.0/))
- **open-standard SKILL.md** format ([agentskills.io](https://agentskills.io/specification))
- **Conventional Commits** in spirit (no formal lint)

---

## License & author

Apache-2.0. See [LICENSE](LICENSE), [PRIVACY.md](PRIVACY.md), [TERMS.md](TERMS.md).

**Mitun** — single maintainer · [github.com/mitunmanav](https://github.com/mitunmanav) · [mitunmanav933@gmail.com](mailto:mitunmanav933@gmail.com)

<div align="center">

*Shipped on 2026-09-01 from Bangalore.*

</div>
