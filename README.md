<p align="center">
  <a href="https://github.com/mitunmanav/build-android-apps">
    <img src="assets/logo.svg" width="92" height="92" alt="Build Android App — green Android head + build stack + Play badge" />
  </a>
</p>

<h1 align="center">Build Android Apps</h1>

<p align="center">
  <strong>The only plugin you need to build & ship Android apps from your AI assistant.</strong><br/>
  One prompt → working app → signed AAB on Play Store. No Kotlin. No Gradle. No Console maze.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=flat-square" alt="License: Apache 2.0" /></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-2.0.0-3DDC84?style=flat-square" alt="Version 2.0.0" /></a>
  <a href="SPEC.md"><img src="https://img.shields.io/badge/spec-v2.0-6E56CF?style=flat-square" alt="Spec v2.0" /></a>
  <img src="https://img.shields.io/badge/platform-Android-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Platform Android" />
  <img src="https://img.shields.io/badge/hosts-Codex%20%E2%80%A2%20Claude%20%E2%80%A2%20.agents-000?style=flat-square" alt="Hosts: Codex, Claude, .agents" />
  <a href="https://github.com/mitunmanav/build-android-apps/stargazers"><img src="https://img.shields.io/github/stars/mitunmanav/build-android-apps?style=flat-square&label=stars" alt="GitHub stars" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> •
  <a href="#how-it-works">How it works</a> •
  <a href="#install">Install</a> •
  <a href="#skills">Skills</a> •
  <a href="#commands">Commands</a> •
  <a href="CONTRIBUTING.md">Contributing</a> •
  <a href="SPEC.md">Spec</a> •
  <a href="docs/ARCHITECTURE.md">Docs</a>
</p>

<p align="center">
  <sub>If this saves you a weekend, please <a href="https://github.com/mitunmanav/build-android-apps">⭐ star the repo</a> — report issues <a href="https://github.com/mitunmanav/build-android-apps/issues">here</a>.</sub>
</p>

---

> **Built for vibe coders, indie founders, and facilitators** — not Android engineers.
> If you can describe the app in one sentence, this plugin can build it.

```text
/make-app "a habit tracker with daily reminders and streaks"
# → asks 3 questions → writes spec → plans → scaffolds → builds → previews → ships
```

---

## Why this plugin?

**You type the idea. The plugin handles the rest** — scaffold, state, signing, store listing, upload — and remembers where you left off.

| You say | Plugin does |
|---|---|
| `a habit tracker` | Intake → spec → plan (Kahn's algorithm, no LLM) → Compose scaffold with signing + Crashlytics |
| `/preview` | `adb` install → launch → screenshot → annotated layout dump |
| `/publish` | Pre-submit gate → signed AAB → Play Store internal track → draft URL |
| `add dark mode` | Mutates `state.json` → re-runs only affected phases |

Every project gets `<project>/.build-android/state.json` (gitignored) — `SessionStart` re-hydrates `phase X step Y`, so `/where` works after you close the laptop. Pairs with Google's [`android/skills`](https://github.com/android/skills): `android skills add --all` for deeper domain coverage.

---

## Quick start

Prerequisites auto-detected on `SessionStart` — missing anything, `/setup` fixes it. You need: JDK 17+ · Android SDK 35 · `adb` · Python 3.10+ · Play Console ($25) + service-account JSON.

```bash
/setup                                          # 10-step wizard: JDK/SDK/adb/device/Play/keystore (~30 min)
/make-app "a habit tracker with daily reminders" # intake → spec → scaffold
/preview                                        # install + launch + screenshot
/publish                                        # gated → signed AAB → Play internal track
```

Taking over a Lovable / Bolt / v0 / Cursor app? `/import` → `/audit` → `/finish`. Mid-build changes: `/add` · `/change` · `/remove` · `/where` · `/undo` · `/continue`.

---

## How it works

```mermaid
flowchart TB
  Host[AI Host - Codex / Claude / .agents]
  Manifests[Plugin Manifests + plugin.lock.json]
  Skills[28 Skills - 1 frontdoor + 27 specialists]
  Commands[22 Commands - plain English]
  MCP[5 MCP Servers - adb / gradlew / play-store / keystore / asset]
  State[state.json - plan / cursor / build / device / store]
  Router[Kahn Router - deterministic no LLM]

  Host --> Manifests
  Manifests --> Skills
  Manifests --> Commands
  Manifests --> MCP
  Skills --> State
  Commands --> State
  MCP --> State
  State --> Router
```

Every `/add` / `/change` / `/undo` mutates `state.json`; the router computes the minimal phase order via Kahn's algorithm. Frontdoor `build-android-apps` is the only skill loaded at startup (under 8k budget), specialists lazy-load. Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`SPEC.md`](SPEC.md) · [`state/README.md`](state/README.md)

---

## Features

| | Capability | What you get |
|---|---|---|
| 💬 | One-liner to app | `/make-app` → 1–5 questions → spec → plan → scaffold |
| 🔀 | Mid-flight edits | Patch plan without restart; only affected phases re-run |
| 📱 | Real device loop | `adb` install / logcat / JDWP / layout dump + 3-strike auto-fix |
| ✅ | Ship with confidence | `/publish` gated on keystore/listing/screenshots; `/why-rejected` diagnoses rejections |
| 🎨 | Store assets from code | Icons (5 densities + adaptive), feature graphic, screenshots via `asset-mcp` |
| 🔁 | Take ownership | Snapshot + audit foreign projects, then `/finish` to publish |

Use `$build-android-apps` for everything — it routes. You never need to name a specialist.

---

## Skills

28 skills — 1 frontdoor `build-android-apps` + 27 specialists. Frontdoor intent-classifies plain English and delegates. Full catalog: [`docs/SKILLS-CATALOG.md`](docs/SKILLS-CATALOG.md)

- **Lifecycle:** `app-intake` · `app-planner` · `android-scaffold` · `android-run` · `android-debug-fix` · `setup-wizard`
- **Quality:** `compose-ui-patterns` · `compose-performance-audit` · `compose-view-refactor` · `material3-expressive` · `android-edge-to-edge`
- **Data & auth:** `android-backend` · `android-auth` · `android-ops` · `android-media` · `android-app-functions` · `android-restore-credentials` · `android-verified-email`
- **Shipping:** `android-icons-assets` · `android-store-listing` · `android-publish-update` · `android-r8-analyzer` · `android-importer`
- **Diagnostics:** `android-profiler` · `android-leak-analyzer` · `android-debugger-agent` · `android-emulator-browser`

---

## Commands

Plain English — all delegate to the frontdoor. Full list: [`commands/`](commands/)

| Command | Does |
|---|---|
| `/setup` | First-run wizard (SDK, Play Console, service account, keystore) |
| `/make-app "<idea>"` | Intake → spec → scaffold |
| `/preview` | Install + launch + screenshot |
| `/publish` · `/update` | Submit to Play internal track · bump version + resubmit |
| `/import` · `/audit` · `/finish` | Take over → check gaps → auto-fill & ship |
| `/add` · `/change` · `/remove` · `/where` · `/undo` · `/continue` | Mutate & navigate plan |
| `/why-rejected` · `/screenshots` · `/backup-keystore` | Diagnose rejection · generate assets |
| `/help` · `/status` · `/reset` | Help · post-publish dashboard · reset |

---

## MCP servers

All Python, stdio. Config: [`.mcp.json`](.mcp.json) — details: [`docs/MCP.md`](docs/MCP.md)

| Server | Tools | Highlights |
|---|---|---|
| **adb-mcp** | 17 | `list_devices`, `install_apk`, `screencap`, `logcat_filter`, `dump_layout` |
| **gradlew-mcp** | 12 | `run_task`, `describe_project`, `manage_sdk`, `generate_keystore` |
| **play-store-mcp** | 9 | `auth`, `upload_aab`, `get_review_status`, `rollout_staged` |
| **keystore-mcp** | 5 | `generate`, `verify`, `rotate`, `backup`, `fingerprint` |
| **asset-mcp** | 4 | `generate_icon` (5 densities + adaptive), `generate_feature_graphic` |

---

## Install

**Codex CLI**

```bash
codex plugin install github.com/mitunmanav/build-android-apps
# local dev: git clone https://github.com/mitunmanav/build-android-apps && codex --plugin-dir .
```

**Claude Code CLI**

```bash
claude plugin marketplace add mitun/mitun
claude plugin install build-android-apps@mitun
# local dev: git clone ... && claude --plugin-dir .
```

**.agents hosts** (VS Code Copilot / Cursor / Gemini CLI)

```bash
git clone https://github.com/mitunmanav/build-android-apps ~/.agents/plugins/build-android-apps
# restart host
```

Verify: `bash scripts/smoke.sh` (6 checks must pass). Optional: `android skills add --all` (https://github.com/android/skills). No telemetry — local `adb`/Gradle/Play API only.

---

## Compatibility

Pinned: [`android-scaffold/references/versions-pinned.md`](skills/android-scaffold/references/versions-pinned.md)

| AGP | Gradle | Kotlin | Compose BOM | M3 | min SDK | target SDK | JVM |
|---|---|---|---|---|---|---|---|
| 8.7+ | 8.9+ | 2.0.21 | 2024.12.01 | 1.3.1 | 26 (Android 8) | latest-stable | 17 |

Also: Navigation 2.8.4 · Hilt 2.52 · Room 2.6.1 · DataStore 1.1.1 · CameraX 1.4.1 · Media3 1.4.1 · Python 3.10+

---

## Limitations

| Out of scope (v1–v2) | Planned |
|---|---|
| iOS, Wear, TV, Auto, XR | Sibling plugins |
| Raw custom backend | Firebase + Supabase only today |
| Multi-user `state.json` | Single-user only today |
| AGP 9.x, schema v2 | v2.1+ |

Pairs with: [`openai/plugins/test-android-apps`](https://github.com/openai/plugins) (profiling) · [`android/skills`](https://github.com/android/skills) (domain) · [`ayush016/android-lead-agent-skills`](https://github.com/ayush016/android-lead-agent-skills) (team standards copy into `AGENTS.md`).

---

## Contributing

PRs welcome. 1) `bash scripts/smoke.sh` must pass 2) `smoke` CI must pass 3) update `CHANGELOG.md` + `SPEC.md` if behavior changed 4) Apache-2.0, author **Mitun only** — no `Co-authored-by`.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) — report vulns to `mitunmanav933@gmail.com` (72h ack).

---

## License and author

[Apache-2.0](LICENSE) · [PRIVACY.md](PRIVACY.md) · [TERMS.md](TERMS.md)

**Mitun** — [github.com/mitunmanav](https://github.com/mitunmanav) · [mitunmanav933@gmail.com](mailto:mitunmanav933@gmail.com)

<p align="center"><sub>Shipped 2026-09-01 from Bangalore. · <a href="https://github.com/mitunmanav/build-android-apps/issues">Issues</a> · <a href="https://github.com/mitunmanav/build-android-apps/discussions">Discussions</a> · <a href="CHANGELOG.md">Changelog</a> · <a href="SPEC.md">Spec</a></sub></p>
