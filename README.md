# Build Android App Plugin

> **The only plugin needed to build and ship Android apps from your AI assistant.**
> Built for non-technical vibe coders, in plain English, end to end.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](CHANGELOG.md)

## What it does

Turn your AI assistant into a full Android dev team. Type `/make-app "a habit tracker"` and you get a working app, signed AAB, and Play Store internal-test-track submission — without writing Kotlin yourself.

| Component | Count | Purpose |
|---|---|---|
| **Skills** | 22 | Full lifecycle: intake → build → ship → update |
| **Slash commands** | 21 | Plain English: `/make-app`, `/add`, `/change`, `/publish`, `/update`, `/status`, `/where`, `/why-rejected`, … |
| **Subagents** | 6 | Parallel validators + intake clarifier + rejection parser + asset generator |
| **Hooks** | 6 | SessionStart, PreToolUse, PostToolUse, PreSubmit, Stop, monitors/ |
| **MCP servers** | 5 | Python: `adb-mcp`, `gradlew-mcp`, `play-store-mcp`, `keystore-mcp`, `asset-mcp` |
| **State file** | per-project | `<project>/.build-android/state.json` for resumable loops |

## Install

### Codex CLI

```bash
codex plugin install github.com/mitunmanav/build-android-app-plugin
```

### Claude Code CLI

```bash
claude plugin marketplace add mitun/mitun
claude plugin install build-android-app-plugin@mitun
```

### `.agents` open-standard hosts

```bash
git clone https://github.com/mitunmanav/build-android-app-plugin \
  ~/.agents/plugins/build-android-app-plugin
```

### Pair with Google's android/skills

```bash
android skills add --all
```

## Prerequisites (auto-detected by SessionStart)

- **JDK 17+** with `JAVA_HOME` set
- **Android SDK** with `ANDROID_HOME` set
- **`adb`** on `PATH`
- **Python 3.10+** for MCP servers
- An **Android device or emulator** for runtime verification
- A **Play Console account** ($25, paid once)
- A **service account JSON key** from Google Cloud (free)

First-run only: type `/setup` and the agent walks you through all of it.

## Quick start

```text
> /setup
# 10-step first-run: SDK, Play Console, service account, keystore

> /make-app "a habit tracker with daily reminders"
# intake (asks 1-5 questions) → spec → build plan → scaffold

> /preview
# installs + launches + screenshots the app

> /publish
# signed AAB → Play Store internal test track
```

## The 22 skills (full lifecycle)

| # | Skill | What it does |
|---|---|---|
| 1 | `app-intake` | Vague prompt → spec via 1-5 plain-English questions |
| 2 | `app-planner` | Spec → sequenced build plan in state.json |
| 3 | `android-scaffold` | Bootstrap Gradle + Compose + signing + Crashlytics |
| 4 | `android-build` | assembleDebug/release, lightweight verification gates |
| 5 | `android-run` | Install + launch + screenshot |
| 6 | `android-debug-fix` | Logcat + agent-driven fix loop (3-strike limit) |
| 7 | `android-ui-patterns` | Compose patterns: lists, nav, forms, state hoisting |
| 8 | `android-performance` | Recomposition, stability, baseline profiles |
| 9 | `android-test` | Screenshot tests on 9 grid sizes + smoke tests |
| 10 | `android-importer` | Take ownership of Lovable/Bolt/v0/Cursor-built projects |
| 11 | `android-backend` | Room + DataStore + Supabase + Firebase templates |
| 12 | `android-auth` | Credential Manager + Google + email + passkey |
| 13 | `android-ops` | FCM + Analytics + WorkManager + Crashlytics verify |
| 14 | `android-media` | CameraX + Media3 ExoPlayer |
| 15 | `android-restore-credentials` | Sign in across devices via restore keys |
| 16 | `android-verified-email` | OTP-less email verification |
| 17 | `android-edge-to-edge` | SDK 35+ mandatory edge-to-edge |
| 18 | `android-icons-assets` | Launcher icon + adaptive layers + feature graphic |
| 19 | `android-store-listing` | Play Store title/desc/short/long/privacy/data safety |
| 20 | `android-play` | Play Store submission flow |
| 21 | `android-publish-update` | Bump version + changelog + signed AAB + re-upload |
| 22 | `android-r8-analyzer` | APK size + keep-rule audit (strict 30-line output) |
| + | `setup-wizard` | First-run 10-step onboarding |

## Slash commands (21, plain English)

| Command | Purpose |
|---|---|
| `/setup` | First-run wizard |
| `/make-app "<idea>"` | Start a new app from a one-liner |
| `/add "<feature>"` | Add a feature without restarting |
| `/change "<spec>"` | Modify an existing plan item |
| `/remove` | Remove or skip a task |
| `/continue` | Resume the build loop |
| `/where` | Show current phase + plan progress |
| `/status` | Post-publish dashboard |
| `/publish` | Store listing + submit to internal test track |
| `/update` | New version + changelog + resubmit |
| `/reset` | Reset project state (double-confirm) |
| `/backup-keystore` | Copy keystore to safe place |
| `/why-rejected` | Diagnose a Play Store rejection |
| `/import` | Detect existing Android project |
| `/audit` | Deep audit for Play Store readiness |
| `/finish` | Auto-fill gaps + publish to internal test |
| `/screenshots` | Generate store screenshots |
| `/privacy-policy` | Generate privacy policy template |
| `/help` | List commands in plain English |
| `/preview` | Install + launch + screenshot |
| `/debug`, `/lint` | Dev aliases |

## MCP servers (5, Python stdio)

### `adb-mcp` — device interaction
17 tools including `list_devices`, `install_apk`, `start_activity`, `screencap`, `logcat_filter` (subscribable resource), `dump_layout` (JSON UI tree).

### `gradlew-mcp` — Gradle + SDK + signing
12 tools: `list_tasks`, `run_task`, `parse_dependencies`, `find_duplicate_classes`, `describe_project` (matches `android describe`), `manage_sdk` (sdkmanager wrapper), `run_help` + `run_build_dry` (lightweight gates), `generate_keystore` + `verify_keystore` (elicitation).

### `play-store-mcp` — Play Developer API
9 tools: `auth`, `upload_aab`, `upload_listing`, `get_review_status`, `list_rejections`, `submit_for_review`, `rollout_staged`, `get_stats`.

### `keystore-mcp` — upload keystore (canonical home)
5 tools: `generate`, `verify`, `rotate`, `backup`, `fingerprint`.

### `asset-mcp` — icon + screenshot generator
4 tools: `generate_icon`, `generate_feature_graphic`, `generate_screenshot`, `compose_marketing`. Requires `pip install Pillow`.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         AI Host (Codex CLI / Claude Code CLI /
│         .agents standard)
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Plugin manifests (.codex-plugin/, .claude-plugin/,
│  .agents/plugins/) + plugin.lock.json (sha256)
└──────────┬───────────────┬─────────────────┬─────────────┘
           │               │                 │
           ▼               ▼                 ▼
       Skills (22)   Commands (21)   MCP servers (5)
       references/   plain-English    adb, gradlew, play-store,
       per skill                      keystore, asset
              │                            │
              ▼                            ▼
          Subagents (6)              Hooks (6) + monitors/
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  Per-project state.json (<project>/.build-android/)
│  schema_version, phase, plan[], cursor, build, device,
│  store, keystore, environment, crashlytics, rejections,
│  history[50] — gitignored, deterministic phase-router
└─────────────────────────────────────────────────────────┘
```

## Compatibility (pinned)

| Component | Version |
|---|---|
| Android Gradle Plugin | 8.7+ |
| Gradle | 8.9+ |
| Kotlin | 2.0.21 |
| Compose BOM | 2024.12.01 |
| min SDK | 26 |
| target SDK | latest-stable |

## Pairs with

- **[openai/plugins/test-android-apps](https://github.com/openai/plugins)** — advanced profiling (Perfetto, Simpleperf).
- **[android/skills (Google)](https://github.com/android/skills)** — domain knowledge (Compose, camera, navigation, etc).
- **[ayush016/android-lead-agent-skills](https://github.com/ayush016/android-lead-agent-skills)** — team standards reference.

## Limitations (v1.0)

- iOS, Wear, TV, Auto, XR — out of scope (sibling plugins TBD)
- Custom backend hosting — Firebase + Supabase only
- Multi-user collaboration — single-user per project
- AGP 9.x — AGP 8.7 stable; AGP 9 in v1.1

## License

Apache-2.0. See [LICENSE](LICENSE).

## Author

Mitun — single maintainer.
