# Changelog

All notable changes to this plugin are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- Initial plugin release
- 9 skills: `android-debugger-agent`, `android-emulator-browser`, `android-profiler`, `android-leak-analyzer`, `android-appActions`, `material3-expressive`, `compose-performance-audit`, `compose-ui-patterns`, `compose-view-refactor`
- 9 slash commands: `/build`, `/run`, `/debug`, `/crash`, `/log`, `/device`, `/lint`, `/test`, `/clean`
- 3 subagents: `build-validator`, `release-auditor`, `apk-inspector`
- 4 hooks: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`
- 2 Python MCP servers: `adb-mcp`, `gradlew-mcp`
- Multi-host packaging: `.codex-plugin/`, `.claude-plugin/`, `.agents/plugins/`

[0.1.0]: https://github.com/mitunmanav/build-android-app-plugin/releases/tag/v0.1.0
