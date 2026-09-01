# Changelog

All notable changes to this plugin are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-01

### Added — full lifecycle

**22 skills** covering intake → ship → update:
- `app-intake`, `app-planner` (intake + planning)
- `android-scaffold`, `android-build`, `android-run`, `android-debug-fix` (build loop)
- `android-ui-patterns`, `android-performance`, `android-test`, `android-edge-to-edge` (Compose quality)
- `android-importer` (take ownership of existing projects)
- `android-backend`, `android-auth`, `android-ops`, `android-media` (data/auth/media)
- `android-restore-credentials`, `android-verified-email` (advanced auth)
- `android-icons-assets`, `android-store-listing`, `android-play`, `android-publish-update` (shipping)
- `android-r8-analyzer` (size optimization)
- `setup-wizard` (first-run)

**21 slash commands** in plain English:
- `/setup`, `/make-app`, `/add`, `/change`, `/remove`, `/continue`, `/where`, `/status`, `/publish`, `/update`, `/reset`, `/backup-keystore`, `/why-rejected`, `/import`, `/audit`, `/finish`, `/screenshots`, `/privacy-policy`, `/help`, `/preview`, `/debug`, `/lint`

**6 subagents**: `intake-clarifier`, `build-validator`, `release-readiness`, `rejection-parser`, `phase-router`, `asset-generator`

**5 MCP servers** (Python stdio):
- `adb-mcp` (17 tools, including new `dump_layout`)
- `gradlew-mcp` (12 tools, including new `describe_project`, `manage_sdk`, `run_help`, `run_build_dry`)
- `play-store-mcp` (9 tools, NEW)
- `keystore-mcp` (5 tools, NEW)
- `asset-mcp` (4 tools, NEW)

**6 hooks**: SessionStart, PreToolUse, PostToolUse, PreSubmit (release-readiness gate), Stop, monitors/

**Resumable build loop** via per-project `<project>/.build-android/state.json`:
- Schema v1 with 13 fields (plan, cursor, build, device, store, keystore, environment, crashlytics, rejections, history[50])
- Kahn's-algorithm phase router (no LLM)
- Plan algebra: `/add` `/remove` `/change` `/undo` mid-flight
- Snapshot on import

**Cold-start wizard** (`/setup`): 10-step guided setup (SDK, Play Console, service account, keystore)

### Added — patterns adopted from Google android/skills (Apache-2.0)

- Sub-agent prompt template + Containment Mandate (`.scratch/<skill>-<uuid>/`)
- Strict-output-limit pattern (chat <30 lines; details in scratch dir)
- Two-tier checklist (agent self-check + user checklist)
- Reporting Action preamble (`> [!IMPORTANT]`)
- SYSTEM DIRECTIVE FOR AI AGENT
- Integration-point discovery via search strings
- Diagnose → report → prescribe
- Screenshot test grid (400/610/900 × 400/500/1000 dp)
- RIGHT/WRONG code pairs
- Numbered Steps, Final Checklist per skill
- Markdown alerts ([!NOTE] [!IMPORTANT] [!CAUTION])
- "**DO NOT**" anti-pattern phrasing
- Lightweight verification gates (`./gradlew help`, `./gradlew build --dry-run`)
- Annotated screenshot pattern + dump_layout JSON shape
- describe_project JSON output + manage_sdk wrapper

### Changed

- README rewritten for v1.0.0 (full lifecycle overview)
- SPEC.md rewritten as v1.0.0 (~700 lines)
- All skills now use open-standard frontmatter (no `compatibility`, `allowed-tools`, `platform`, `version`)
- Hooks use `${CLAUDE_PLUGIN_ROOT}` consistently

## [0.1.0] - 2026-08-01

### Added

- Initial plugin release
- 9 skills: `android-debugger-agent`, `android-emulator-browser`, `android-profiler`, `android-leak-analyzer`, `android-appActions`, `material3-expressive`, `compose-performance-audit`, `compose-ui-patterns`, `compose-view-refactor`
- 9 slash commands: `/build`, `/run`, `/debug`, `/crash`, `/log`, `/device`, `/lint`, `/test`, `/clean`
- 3 subagents: `build-validator`, `release-auditor`, `apk-inspector`
- 4 hooks: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`
- 2 Python MCP servers: `adb-mcp`, `gradlew-mcp`
- Multi-host packaging: `.codex-plugin/`, `.claude-plugin/`, `.agents/plugins/`

[1.0.0]: https://github.com/mitunmanav/build-android-app-plugin/releases/tag/v1.0.0
[0.1.0]: https://github.com/mitunmanav/build-android-app-plugin/releases/tag/v0.1.0
