# Changelog

All notable changes to this plugin are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-09-01

### Added
- **Frontdoor skill `build-android-apps`** — one skill routes to 27 specialists via state-aware intent table (`references/routing-table.md`). Progressive disclosure: only frontdoor description at startup (under Codex 2%/8k budget), specialists lazy-load — efficiency without losing smartness. Specialists now `allow_implicit_invocation:false`, frontdoor `true`.
- **28 skills total** (was 22): adds `android-debugger-agent`, `android-emulator-browser`, `android-profiler`, `android-leak-analyzer`, `android-app-functions`, `compose-performance-audit`, `compose-ui-patterns`, `compose-view-refactor`, `material3-expressive`, `android-importer` to lock (all were present on disk, now pinned).
- **Renamed plugin `build-android-app-plugin` → `build-android-apps`** (`pluginId` `com.mitun.build-android-apps`, repo `github.com/mitunmanav/build-android-apps`, tool prefix `mcp__plugin_build_android_apps_*`). Per-project runtime dir stays `.build-android/` with shim for `.build-android-apps/`.
- **Verified against official Codex docs** (`developers.openai.com/codex/*` + `agentskills.io/specification`) — see `references/codex-docs-audit.md`.

### Changed
- **Version 2.0.0** (breaking: `pluginId` and tool prefix change per semver; migrate: `codex plugin remove build-android-app-plugin && codex plugin install github.com/mitunmanav/build-android-apps`).
- `.codex-plugin/plugin.json` version 2.0.0, `interface.defaultPrompt` now frontdoor.
- `plugin.lock.json`: 28 skills / 30 commands / 4 subagents / 5 hooks (was 17/13/4/5).
- `hooks/hooks.json`: `PreSubmit` → `PreToolUse` with tool matcher (Codex has no `PreSubmit` event); `CLAUDE_PLUGIN_ROOT` → `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` compat.
- `hooks/release-check.sh`: now denies via `permissionDecision: deny` (was `additionalContext` + exit 2).
- `hooks/session-start.sh`: 5s adb devices cache + frontdoor reminder.
- `skills/*/SKILL.md` `allowed-tools` list → space-separated string (per `agentskills.io` spec); all `agents/openai.yaml` set correctly.
- `mcp-servers/*/pyproject.toml`: `asset-mcp`/`keystore-mcp`/`play-store-mcp` now full `build-system` + classifiers (was minimal); `README.md` added.
- `spec` bumped to 2.0.0, `skills` 22→28, `commands` 21→22, `subagents` 6→4 (canonical 4 on disk), `hooks` 6→5 handlers/4 events.
- Docs `ARCHITECTURE.md`/`HOOKS.md`/`MCP.md`/`SKILLS-CATALOG.md` updated from stale 9/2/4 counts to 28/5/5.
- CI `.github/workflows/test-mcp-servers.yml` matrix now covers all 5 servers (was 2).

### Fixed
- `play-store-mcp/server.py` duplicate `shutil_which_path` definition; `keystore-mcp/server.py` `_fingerprint_of` `None` guard; `asset-mcp/server.py` `LANCZOS` Pillow 10 compat (`_RESAMPLE` helper).
- `scripts/verify-install.py` counts 9→28/22/4 and PreToolUse 2 handlers.
- `mcp-servers/asset-mcp` `Pillow` now `mcp>=2.0` + `pydantic>=2.0` to match siblings.

### How to migrate from 1.0.0
```bash
codex plugin remove build-android-app-plugin  # if installed via marketplace
codex plugin install github.com/mitunmanav/build-android-apps
# or: claude plugin update / .agents hosts: git clone to new path
```
No state.json migration needed if you keep `.build-android/` (recommended). If you use `.build-android-apps/`, move: `mv .build-android .build-android-apps`.

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

[1.0.0]: https://github.com/mitunmanav/build-android-apps/releases/tag/v1.0.0
[0.1.0]: https://github.com/mitunmanav/build-android-apps/releases/tag/v0.1.0
