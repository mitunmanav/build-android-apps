# Build Android App Plugin

Agentic Android development: build, run, debug, profile, and ship Android apps from your AI assistant.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](CHANGELOG.md)

## What it does

This plugin teaches your AI assistant the Android build loop and gives it typed tools to run it:

| Component | Count | Purpose |
|---|---|---|
| **Skills** | 9 | Domain knowledge: Compose, Material 3, debugger, profiler, leaks, AppFunctions |
| **Slash commands** | 9 | `/build`, `/run`, `/debug`, `/crash`, `/log`, `/device`, `/lint`, `/test`, `/clean` |
| **Subagents** | 3 | Parallel validators: build-validator, release-auditor, apk-inspector |
| **Hooks** | 4 | SessionStart, PreToolUse, PostToolUse, Stop |
| **MCP servers** | 2 | Python: `adb-mcp` and `gradlew-mcp` |

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

### Claude Code

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

## Prerequisites

- **Android SDK** with `ANDROID_HOME` set
- **JDK 17+** with `JAVA_HOME` set
- **`adb`** on `PATH` (usually `${ANDROID_HOME}/platform-tools/adb`)
- **Python 3.10+** for MCP servers
- An **Android device or emulator** for runtime verification

The plugin's `SessionStart` hook will detect missing prerequisites and warn.

## Quick start

```text
> /device
# picks from your connected emulators/devices

> /build
# runs `./gradlew assembleDebug`

> /run
# installs and launches the app

> /debug
# attaches a debugger + opens logcat
```

Or use the skills directly:

```text
> $android-debugger-agent
> Use Perfetto to capture a 5s trace of the main activity cold start.
```

## The 9 skills

| Skill | Purpose | MCP deps |
|---|---|---|
| `android-debugger-agent` | Connect device, attach debugger, step through code | `adb-mcp` |
| `android-emulator-browser` | Launch AVD, screencap, UI inspect | `adb-mcp` |
| `android-profiler` | Perfetto traces + jank/memory/CPU analysis | `adb-mcp`, `gradlew-mcp` |
| `android-leak-analyzer` | LeakCanary + heap dump triage | `adb-mcp` |
| `android-appActions` | AppFunctions API + Shortcuts integration | (none) |
| `material3-expressive` | Material 3 Expressive design + anti-patterns | (none) |
| `compose-performance-audit` | Recomposition, stability, baseline profiles | (none) |
| `compose-ui-patterns` | Pattern catalog | (none) |
| `compose-view-refactor` | Refactor methodology | (none) |

## Slash commands

| Command | Purpose | MCP tools |
|---|---|---|
| `/build` | Run Gradle task | `gradlew.run_task` |
| `/run` | Install + launch app | `adb.install_apk`, `adb.start_activity` |
| `/debug` | Attach debugger + logcat | `adb.attach_debugger`, `adb.logcat_dump` |
| `/crash` | Analyze crash report | `adb.pull_file`, `adb.unzip` |
| `/log` | Filter logcat | `adb.logcat_filter` |
| `/device` | Pick device (with elicitation) | `adb.list_devices`, `adb.select_device` |
| `/lint` | Run lint, summarize | `gradlew.run_lint` |
| `/test` | Run tests, report failures | `gradlew.run_tests` |
| `/clean` | `gradlew clean` (with confirmation) | `gradlew.run_task` |

## MCP servers

Both servers are Python (`mcp` SDK + Pydantic v2) and communicate over stdio:

### `adb-mcp`

`list_devices`, `select_device`, `install_apk`, `uninstall_app`, `clear_app_data`, `start_activity`, `stop_app`, `shell_command`, `logcat_dump`, `logcat_clear`, `logcat_filter` (subscribable resource), `screencap`, `pull_file`, `push_file`, `getprop`, `setprop`, `wait_for_device`.

### `gradlew-mcp`

`list_tasks`, `run_task` (Task), `parse_dependencies`, `find_duplicate_classes`, `run_lint` (Task), `run_tests` (Task), `clean` (elicitation), `stop_build`, `get_build_status`, `verify_keystore`, `generate_keystore` (elicitation).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                AI Host (Codex / Claude / .agents)        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Plugin manifest                                        │
│  .codex-plugin/plugin.json  (Codex)                     │
│  .claude-plugin/marketplace.json  (Claude Code)          │
│  .agents/plugins/marketplace.json  (open-standard)       │
└──────────┬───────────────┬─────────────────┬─────────────┘
           │               │                 │
           ▼               ▼                 ▼
       Skills          Commands         MCP servers
       (9 prose)       (9 slash)        (2 Python)
                              │
                              ▼
                          Hooks (4)
                      SessionStart, Pre,
                      PostToolUse, Stop
```

See [SPEC.md](SPEC.md) for the full design.

## Plugin layout

```
build-android-app-plugin/
├── .codex-plugin/plugin.json        # Codex manifest
├── .claude-plugin/marketplace.json  # Claude Code manifest
├── .agents/plugins/marketplace.json # open-standard manifest
├── .mcp.json                        # MCP server config (adb + gradlew)
├── skills/                          # 9 skills (prose-only)
├── commands/                        # 9 slash commands
├── agents/                          # 3 subagents
├── hooks/                           # 4 hooks + hooks.json
├── mcp-servers/                     # Python sources
├── assets/                          # icons + logos
├── docs/                            # ARCHITECTURE, HOOKS, MCP, SKILLS-CATALOG
├── .github/workflows/               # CI
└── SPEC.md                          # design spec
```

## License

Apache-2.0. See [LICENSE](LICENSE).

## Contributing

PRs welcome. Each slice should:

1. Pass `skills-ref validate skills/<name>` (for skill changes)
2. Pass `pytest` (for MCP server changes)
3. Pass `python -m <server>` smoke test (for MCP server changes)
4. Update the per-component docs

## Author

Mitun — single maintainer.
