# Build Android App Plugin — Specification

**Version**: 0.1.0
**Status**: Draft for approval (Phase 0)
**Author**: Mitun
**License**: Apache-2.0

## 1. Goals

Build a plugin that gives AI agents hands-on capability for Android development. The plugin teaches the agent Android conventions and exposes typed tools for the build loop (connect device → write code → build → install → run → debug → iterate).

### What this plugin does

- Provides 9 focused skills covering the daily Android build loop (debugger, profiler, leaks, AppActions, Material 3, Compose patterns, refactor, emulator, build)
- Provides 9 slash commands for fast invocation (`/build`, `/run`, `/debug`, `/crash`, `/log`, `/device`, `/lint`, `/test`, `/clean`)
- Provides 3 subagents that run parallel validation (`build-validator`, `release-auditor`, `apk-inspector`)
- Provides 4 event hooks for safety + automation (block destructive ops, lint on edit, SDK detection at session start, background review on stop)
- Bundles 2 MCP servers written in Python: `adb-mcp` and `gradlew-mcp`
- Ships to Codex, Claude Code, and `.agents` open-standard hosts

### What this plugin does NOT do

- Not a comprehensive Android reference (Google's `android/skills` covers 22 domains; we focus on the build loop)
- Not a marketplace product (v0.1 installs from a Git URL; submission is a v0.2+ task)
- Not an iOS port (iOS plugin was a structural reference for skill organization; iOS and Android are different platforms)
- Not a Kotlin Multiplatform or Compose-for-Web plugin

## 2. Differentiation

Why build this when Google's [`android/skills`](https://github.com/android/skills) already exists?

| | Google's `android/skills` | **This plugin** |
|---|---|---|
| Shipping format | Markdown skills only (open standard) | Skills + commands + subagents + hooks + MCP tools |
| Tool surface | Agent uses `adb` via shell | Typed MCP tools: `adb install`, `adb logcat`, etc. |
| Slash commands | None | 9 (`/build`, `/run`, `/debug`, ...) |
| Subagents | None | 3 parallel validators |
| Event hooks | None | 4 (block destructive, lint on edit, SDK detect, async review) |
| Structured user prompts | None | MCP elicitation (device picker, variant picker) |
| Multi-host | 3 hosts | 3 hosts |
| Skills count | 22 (broad coverage) | 9 (focused on build loop) |

This plugin complements Google's by being a **focused, opinionated, hands-on toolkit** for the build loop. Users can have both installed.

## 3. Target Users

### Primary

- Codex users working on Android apps (the AI has the plugin loaded; the user types `/build`, `/run`, `/debug`, etc.)

### Secondary

- Claude Code users (same experience, different host)
- `.agents` open-standard host users (developers using VS Code Copilot, Cursor, etc.)

### Author

- Mitun — single maintainer, single brand, no co-authors

## 4. Architecture

This section consolidates the design decisions from:
- [Codex Plugins docs](https://developers.openai.com/codex/plugins/)
- [Codex Build Skills](https://developers.openai.com/codex/build-skills/)
- [Claude Code Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [Claude Code Hooks](https://docs.claude.com/en/docs/claude-code/hooks)
- [Claude Code MCP](https://docs.claude.com/en/docs/claude-code/mcp)
- [Anthropic: Equipping agents with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [agentskills.io spec](https://agentskills.io/specification)
- [MCP spec 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/)

### Directory layout

```
build-android-app-plugin/
├── SPEC.md                            # this file
├── LICENSE                            # Apache-2.0
├── README.md                          # install + usage
├── CHANGELOG.md                       # release history
├── .gitignore
├── .codex-plugin/
│   └── plugin.json                    # Codex: rich interface + skills + mcpServers
├── .claude-plugin/
│   └── marketplace.json               # Claude: minimal manifest
├── .agents/plugins/
│   └── marketplace.json               # open-standard manifest
├── .mcp.json                          # adb-mcp + gradlew-mcp
├── skills/                            # 9 skills (prose-only)
│   ├── android-debugger-agent/
│   │   ├── SKILL.md
│   │   └── agents/openai.yaml
│   ├── android-emulator-browser/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/                # if SKILL.md > 500 lines
│   ├── android-profiler/
│   ├── android-leak-analyzer/
│   ├── android-appActions/
│   ├── material3-expressive/
│   ├── compose-performance-audit/
│   ├── compose-ui-patterns/            # references/ subfolder split
│   └── compose-view-refactor/
├── commands/                          # 9 slash commands (commands-as-skills)
│   ├── build.md
│   ├── run.md
│   ├── debug.md
│   ├── crash.md
│   ├── log.md
│   ├── device.md
│   ├── lint.md
│   ├── test.md
│   └── clean.md
├── agents/                            # 3 subagents
│   ├── build-validator.md
│   ├── release-auditor.md
│   └── apk-inspector.md
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh
│   ├── block-destructive.sh
│   ├── lint-kotlin.sh
│   └── stop-review.sh
├── mcp-servers/                       # 2 Python MCP servers (stdio)
│   ├── adb-mcp/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/adb_mcp/
│   │       ├── __init__.py
│   │       ├── server.py
│   │       ├── tools/
│   │       ├── resources/
│   │       └── prompts/
│   │   └── tests/
│   └── gradlew-mcp/
│       ├── pyproject.toml
│       ├── README.md
│       └── src/gradlew_mcp/
│           ├── __init__.py
│           ├── server.py
│           ├── tools/
│           ├── resources/
│           └── prompts/
│       └── tests/
├── assets/
│   ├── composer-icon.svg
│   ├── logo.svg
│   └── skill-android-debugger.svg
├── docs/
│   ├── ARCHITECTURE.md                # component diagram (mermaid)
│   ├── HOOKS.md                       # hook reference
│   ├── MCP.md                         # MCP server reference
│   └── SKILLS-CATALOG.md              # 9-skill guide
└── .github/workflows/
    ├── validate-skills.yml            # skills-ref validate
    ├── validate-manifests.yml         # JSON schema for 3 manifests
    └── test-mcp-servers.yml           # pytest
```

### Plugin manifest (Codex: `.codex-plugin/plugin.json`)

```json
{
  "$schema": "https://json.schemastore.org/codex-plugin.json",
  "name": "build-android-app-plugin",
  "version": "0.1.0",
  "description": "Agentic Android development: build, run, debug, profile via slash commands and MCP-driven adb/gradlew servers.",
  "author": {
    "name": "Mitun",
    "email": "[email protected]",
    "url": "https://github.com/mitun"
  },
  "homepage": "https://github.com/mitun/build-android-app-plugin",
  "repository": "https://github.com/mitun/build-android-app-plugin",
  "license": "Apache-2.0",
  "keywords": ["android", "kotlin", "jetpack-compose", "gradle", "adb"],
  "interface": {
    "displayName": "Build Android App",
    "shortDescription": "Agentic Android development",
    "longDescription": "Plugin for building, running, debugging, profiling, and shipping Android apps. Provides slash commands, subagents, MCP servers, and 9 domain skills.",
    "developerName": "Mitun",
    "category": "development",
    "capabilities": ["Skills", "Interactive", "Read", "Write"],
    "defaultPrompt": [
      "Use $android-debugger-agent to debug my Android app",
      "Use /build to assemble the debug variant",
      "Run /device to pick an emulator"
    ],
    "websiteURL": "https://github.com/mitun/build-android-app-plugin",
    "brandColor": "#3DDC84"
  },
  "skills": "./skills/",
  "mcpServers": "./.mcp.json"
}
```

> **Note**: GitHub-specific values (`email`, `url`) above are placeholders. Fill in before tagging v0.1.0.

### Multi-host manifests

Three directories ship manifests for three hosts:

| Directory | File | Format | Hosts |
|---|---|---|---|
| `.codex-plugin/` | `plugin.json` | Codex-rich with `interface.*` | Codex (CLI, desktop app, IDE, web) |
| `.claude-plugin/` | `marketplace.json` | Claude minimal | Claude Code |
| `.agents/plugins/` | `marketplace.json` | Open-standard | `.agents` standard hosts (VS Code, Cursor, Gemini CLI, etc.) |

All three reference the same `./skills/`, `./agents/`, `./commands/`, `./hooks/`, `.mcp.json`. Host-level features (Codex interface block, Claude-Code-only frontmatter fields) live only in their respective manifests.

## 5. Skills (9)

All skills follow the [agentskills.io open-standard format](https://agentskills.io/specification). Per-skill UI metadata (Codex-only) lives in `agents/openai.yaml`; other hosts ignore it.

### Frontmatter (open-standard, multi-host safe)

```yaml
---
name: <skill-name>
description: >
  <Multi-sentence trigger phrase. State when to use AND when not to use.
  Under 1024 chars (agentskills.io spec limit).>
license: Apache-2.0
compatibility: <Required MCP servers, env vars, system packages. Max 500 chars.>
allowed-tools: <Space-separated pre-approved tool names. Experimental.>
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [android, ...]
  platform: android
  version: 0.1.0
---
```

**Hard constraints** (enforced by `skills-ref validate`):
- `name`: 1-64 chars; `^[a-z0-9]+(-[a-z0-9]+)*$`; no leading/trailing hyphen; no `--`
- `description`: 1-1024 chars
- SKILL.md body: under 500 lines (move detail to `references/`)
- Reference paths: relative, one level deep

### Body template

```markdown
# <Skill Name>

## Prerequisites
- Dep 1 (versions, packages)
- Dep 2

## Workflow

### Step 1: ...
### Step 2: ...
### Step 3: ...

## Anti-patterns

- ❌ Don't do X
- ❌ Don't do Y

## Pairing

- `<other-skill>` — when to call this
- `<mcp-tool>` — how to use it

## References

- See [references/setup.md](references/setup.md)
- External: https://developer.android.com/...
```

### Per-skill agents/openai.yaml (Codex-only)

```yaml
interface:
  display_name: "Android Debugger Agent"
  short_description: "Debug Android apps on a device"
  icon_small: "../../assets/skill-android-debugger.svg"
  brand_color: "#3DDC84"
  default_prompt: "Use $android-debugger-agent to debug my Android app"
policy:
  allow_implicit_invocation: true
dependencies:
  tools:
    - type: "mcp"
      value: "adb-mcp"
      transport: "stdio"
```

### 9 skills lineup

| # | Skill | Purpose | MCP deps |
|---|---|---|---|
| 1 | `android-debugger-agent` | Connect device, attach debugger, set breakpoints, step through code | `adb-mcp` |
| 2 | `android-emulator-browser` | Launch AVD, screencap, UI inspect, drive emulator | `adb-mcp` |
| 3 | `android-profiler` | Record Perfetto trace, analyze jank/memory/CPU | `adb-mcp`, `gradlew-mcp` |
| 4 | `android-leak-analyzer` | LeakCanary + heap dump triage | `adb-mcp` |
| 5 | `android-app-functions` | AppFunctions API + Shortcuts integration | (none) |
| 6 | `material3-expressive` | Material 3 Expressive design + anti-patterns | (none) |
| 7 | `compose-performance-audit` | Recomposition, stability, deferral, baseline profiles | (none) |
| 8 | `compose-ui-patterns` | Pattern catalog (split to `references/` when >500 lines) | (none) |
| 9 | `compose-view-refactor` | Refactor methodology, MV separation | (none) |

### Decision: prose-only, no scripts/

Per [Anthropic's engineering blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), skills can include code "for Claude to execute as tools at its discretion." However:

1. The iOS plugin used scripts in 3/9 skills (~1,700 lines) for binary parsing and template generation
2. **We have MCP servers** — parsing logic moves to Python servers with typed outputs
3. Scripts in `scripts/` only work in Codex CLI's exec environment; **MCP tools work in all 3 hosts**

Decision: **All 9 skills are prose-only. Zero `scripts/` folders per skill.** Parsing/generation logic lives in MCP servers.

## 6. Slash Commands (9)

Commands implemented as skill files (Claude Code pattern: `commands/` and `skills/` are merged). For Codex, these become invokable as `/cmd` or `$cmd`.

### Frontmatter pattern

```markdown
---
description: Build the app with Gradle
allowed-tools:
  - mcp__plugin_android_gradlew__run_task
  - mcp__plugin_android_gradlew__list_tasks
  - mcp__plugin_android_adb__list_devices
  - Read
  - Grep
---

## Context

- Working directory: !`pwd`
- Project tasks: !`./gradlew tasks --all 2>/dev/null | head -30`
- Recent commits: !`git log --oneline -5`

## Your task

$ARGUMENTS

### Step 1: Determine target task
...

## Anti-patterns
- ❌ Don't `gradlew clean` unless explicitly asked
- ❌ Don't pipe Gradle to `grep` (use MCP's structured output)
```

### 9 commands

| # | Command | MCP tools pre-allowed | Purpose |
|---|---|---|---|
| 1 | `/build` | `gradlew.run_task`, `gradlew.list_tasks`, `gradlew.parse_dependencies`, `adb.list_devices` | Run a Gradle build |
| 2 | `/run` | `gradlew.run_task`, `gradlew.list_tasks`, `adb.list_devices`, `adb.select_device`, `adb.install_apk`, `adb.start_activity`, `adb.wait_for_device` | Build + install + launch |
| 3 | `/debug` | `adb.list_devices`, `adb.select_device`, `adb.shell_command`, `adb.logcat_dump`, `adb.getprop`, `adb.start_activity` | Set up JDWP debug session |
| 4 | `/crash` | `adb.logcat_dump`, `adb.shell_command`, `adb.pull_file`, `adb.push_file`, `adb.unzip` | Analyze crash report |
| 5 | `/log` | `adb.list_devices`, `adb.select_device`, `adb.logcat_dump`, `adb.logcat_clear`, `adb.shell_command` | Filter/stream logcat |
| 6 | `/device` | `adb.list_devices`, `adb.select_device`, `adb.shell_command`, `adb.getprop`, `adb.wait_for_device` | List/pick device, launch AVD |
| 7 | `/lint` | `gradlew.run_lint`, `gradlew.run_task`, `gradlew.list_tasks` | Run lint, summarize |
| 8 | `/test` | `gradlew.run_tests`, `gradlew.run_task`, `gradlew.list_tasks` | Run tests, report failures |
| 9 | `/clean` | `gradlew.clean`, `gradlew.run_task` | `gradlew clean` (destructive, with elicitation) |

**MCP tool name format**: `<server>.<tool>` where `<server>` is the key in `.mcp.json` (`adb` or `gradlew`). When exposed by Codex, the fully-qualified tool name in `allowed-tools:` follows the pattern `mcp__plugin_<plugin_name_underscored>_<server>__<tool>`. For this plugin: `mcp__plugin_build_android_app_plugin_<adb|gradlew>__<tool>`.

## 7. Subagents (3)

Each is a `.md` file with frontmatter (name, description with `<example>` block, tools, model) and system-prompt body.

### Pattern

```markdown
---
name: build-validator
description: |
  Use when user asks to "validate the build", "pre-flight check", "is the build healthy?".
  Runs lint + tests + dependency check + R8 in parallel.

  <example>
  Context: User just merged a PR and wants to verify nothing broke.
  user: "Validate the build after my PR"
  assistant: "I'll use the build-validator agent."
  </example>

tools: [mcp__plugin_android_gradlew__run_task, Read]
model: sonnet
---

You are a build validation specialist...

1. Determine affected modules from recent git diff
2. Run in parallel: lint, tests, deps, R8
3. Aggregate results into status report
4. Suggest fix if RED
```

### 3 subagents

| Agent | Purpose | Parallelism |
|---|---|---|
| `build-validator` | Pre-flight: lint + tests + dep check + R8 | 4-way parallel |
| `release-auditor` | Pre-release: keystore + version + changelog + R8 + lint | 5-way parallel |
| `apk-inspector` | Deep APK analysis: manifest + dex + resources + signing | Sequential (deep) |

## 8. Hooks (4 events)

Per [Claude Code Hooks docs](https://docs.claude.com/en/docs/claude-code/hooks), 28 events supported. We use 4.

| Event | Handler | Matcher | Purpose |
|---|---|---|---|
| `SessionStart` | `session-start.sh` | (all) | Detect `$ANDROID_HOME`, adb in PATH, connected devices; warn if missing |
| `PreToolUse` | `block-destructive.sh` | `Bash` | Block `gradlew clean` and `rm -rf` unless explicitly confirmed |
| `PostToolUse` | `lint-kotlin.sh` | `Edit|Write` | Run ktlint on edited `.kt` files |
| `Stop` | `stop-review.sh` | (all) | Background LLM review of git diff (asyncRewake pattern from Claude Code) |

### hooks.json

```json
{
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

## 9. MCP Servers (2)

### adb-mcp

| Tool | Annotations | Purpose |
|---|---|---|
| `list_devices` | readOnly | List `adb devices` |
| `select_device` | (with elicitation) | Pick from multi-device list |
| `install_apk` | (with elicitation) | `adb install -r` |
| `uninstall_app` | destructive | `adb uninstall` |
| `clear_app_data` | destructive | `pm clear` |
| `start_activity` | idempotent | `am start` |
| `stop_app` | destructive | `am force-stop` |
| `shell_command` | (with elicitation) | `adb shell` with confirm |
| `logcat_dump` | readOnly | `adb logcat -d` |
| `logcat_clear` | destructive | `adb logcat -c` |
| `logcat_filter` | (subscribable resource) | Filtered logcat |
| `screencap` | readOnly | PNG capture |
| `pull_file` | readOnly | `adb pull` |
| `push_file` | destructive | `adb push` |
| `getprop` | readOnly | `adb shell getprop` |
| `setprop` | destructive | `adb shell setprop` |
| `wait_for_device` | (Task) | `adb wait-for-device` |

Plus:
- Resource: `adb://logcat/{device}/{buffer}` (subscribable)
- Prompt: `diagnose-app-crash`
- Elicitation: device picker, variant picker

### gradlew-mcp

| Tool | Annotations | Purpose |
|---|---|---|
| `list_tasks` | readOnly | `./gradlew tasks --all` |
| `run_task` | (Task) | `./gradlew <task>` with progress |
| `parse_dependencies` | readOnly | `./gradlew :app:dependencies` |
| `find_duplicate_classes` | readOnly | Find duplicate class deps |
| `run_lint` | (Task) | `./gradlew lint` |
| `run_tests` | (Task) | `./gradlew test` |
| `clean` | destructive (elicitation) | `./gradlew clean` |
| `stop_build` | (Task control) | Cancel running build |
| `get_build_status` | readOnly | Task status |
| `verify_keystore` | readOnly | Validate signing config |
| `generate_keystore` | (elicitation) | Generate keystore with masked password input |

Plus:
- Resource: `gradle://project/info`
- Resource: `gradle://build/{id}/report`
- Resource: `gradle://build/{id}/errors`
- Prompt: `explain-error`

### Transport: stdio only

Both servers use stdio transport (per Codex + Claude Code docs). No HTTP, SSE, or WebSocket.

### Python dependencies

- `mcp` (official SDK, async support)
- `pydantic` v2 (schema validation, matches TypeScript Zod)
- No other deps; `adb` and `gradle` invoked via `subprocess.run`

## 10. Multi-host Packaging

### Per-host rules

| Host | Manifest path | Format | Special fields |
|---|---|---|---|
| Codex | `.codex-plugin/plugin.json` | Codex-rich with `interface.*` | `interface`, `capabilities`, `defaultPrompt`, `brandColor` |
| Claude Code | `.claude-plugin/marketplace.json` | Claude minimal | `$schema`, `category` per plugin |
| `.agents` standard | `.agents/plugins/marketplace.json` | Open-standard | Strict spec compliance |

### Plugin-level naming

- Codex: `build-android-app-plugin` (no prefix needed)
- Claude Code: skills auto-namespaced as `/build-android-app-plugin:<skill-name>`
- `.agents`: depends on host (typically uses `name` from manifest)

## 11. Versioning

- **Semver**: `0.1.0` → `0.2.0` → `1.0.0`
- `0.x` = pre-1.0; breaking changes allowed in minor
- `1.0.0+` = stable; breaking changes bump major
- Bump per release, commit message + CHANGELOG.md entry required

## 12. License

Apache-2.0 for the entire plugin. MCP servers, skills, scripts, hooks, docs — all Apache-2.0.

## 13. Distribution

- **v0.1.0**: Public GitHub repo + README install. No marketplace gate.
- **v0.2.0+**: Submit to Codex marketplace + Claude Code community marketplace (deferred).

### Install instructions (README)

```bash
# Codex CLI
codex plugin install github.com/mitun/build-android-app-plugin

# Or for development
git clone https://github.com/mitun/build-android-app-plugin
codex --plugin-dir ./build-android-app-plugin

# Claude Code
claude plugin marketplace add mitun/mitun
claude plugin install build-android-app-plugin@mitun

# .agents host
git clone https://github.com/mitun/build-android-app-plugin ~/.agents/plugins/build-android-app-plugin
```

## 14. Out of Scope (v0.1)

Explicit non-goals to keep v0.1 focused:

- iOS port or iOS-comparison sections in docs (per user decision)
- Skill `scripts/` folders (per user decision — moved to MCP)
- Multiple MCP transports (stdio only)
- Kotlin Multiplatform support
- Compose-for-Web
- Plugin marketplace submission (deferred to v0.2)
- Per-skill UI screenshots
- Per-skill test framework beyond `skills-ref validate`
- GitHub Actions for MCP server tests (deferred to v0.2)
- Custom plugin icons beyond the basic Android-themed asset

## 15. Verification

Per-skill acceptance criteria:

- [ ] `skills-ref validate skills/<name>` passes
- [ ] Description ≤ 1024 chars
- [ ] Frontmatter uses only open-standard spec fields
- [ ] Body ≤ 500 lines (split to `references/` otherwise)
- [ ] `agents/openai.yaml` present for Codex UI
- [ ] Tested in Codex: `$<skill-name>` resolves

Per-MCP-server acceptance criteria:

- [ ] `python -m <server>` starts cleanly via stdio
- [ ] All tools listed via MCP `tools/list`
- [ ] Happy-path + error-path tested for each tool
- [ ] Elicitation triggers on multi-device scenarios
- [ ] Resources subscribable where applicable

Per-hook acceptance criteria:

- [ ] Fires on correct event
- [ ] `matcher` regex matches intended tool calls
- [ ] `if` field narrows further
- [ ] Script exits cleanly (or returns JSON `permissionDecision: deny`)

Plugin-level acceptance:

- [ ] All 3 manifests valid JSON
- [ ] `codex --plugin-dir ./build-android-app-plugin` loads all 9 skills + 9 commands + 3 agents + 4 hooks + 2 MCP servers
- [ ] `claude --plugin-dir ./build-android-app-plugin` loads in Claude Code
- [ ] `.agents` host loads the open-standard manifest
- [ ] CI green: `skills-ref validate`, JSON schema, pytest
- [ ] GitHub repo created, tag `v0.1.0`, release notes

## 16. Implementation Order

| # | Phase | Files | Effort | Verification |
|---|---|---|---|---|
| 0 | SPEC.md (this file) | 1 | 1h | User approval |
| 1 | Scaffold + 3 manifests + LICENSE + README | ~7 | 2h | JSON valid; hosts discover plugin |
| 2a | `adb-mcp` skeleton + `list_devices` + `install_apk` | ~6 | 2h | MCP connects; tool callable |
| 2b | `gradlew-mcp` skeleton + `list_tasks` + `run_task` | ~6 | 2h | MCP connects; tool callable |
| 3 | 9 skills (one per slice) | 18 | 8h | `skills-ref validate` passes for all |
| 4 | 9 slash commands | 9 | 5h | Each `/cmd` invokes correct MCP tool |
| 5 | 3 subagents | 3 | 3h | Each runs its parallel work |
| 6 | 4 hooks | 5 | 3h | Each fires on correct event |
| 7 | Brand assets + docs | 7 | 2h | SVG validates; docs render |
| 8 | CI workflows | 3 | 1h | All green on test commit |
| 9 | Verify install in 3 hosts | 0 | 2h | All hosts load plugin |
| 10 | GitHub repo + tag v0.1.0 + release notes | 0 | 1h | Public repo at github.com/mitun/build-android-app-plugin |
| **TOTAL** | | **~67 files** | **~32h** | |

At 4h/day = ~8 working days.

## 17. Open questions (deferred)

These are flagged for later, not blocking v0.1:

1. **Author email + URL**: placeholder `[email protected]` needs Mitun's real email + URL
2. **Brand assets**: composer-icon.svg and logo.svg are placeholders; final designs in Phase 7
3. **Skill-specific reference content**: Phase 3 will determine if `references/` is needed per skill
4. **MCP server test framework**: pytest scaffolds in v0.1; full coverage in v0.2
5. **Marketplace submission criteria**: Codex marketplace + Claude Code community marketplace in v0.2+

## 18. Approval

This SPEC requires Mitun's approval before Phase 1 begins.

---

## Appendix A: Sources cited

| Source | URL | Used for |
|---|---|---|
| Codex Plugins | https://developers.openai.com/codex/plugins/ | Plugin model |
| Codex Build Skills | https://developers.openai.com/codex/build-skills/ | SKILL.md format, agents/openai.yaml |
| Codex Build Plugins | https://developers.openai.com/codex/build-plugins | Plugin packaging |
| Codex Subagents | https://developers.openai.com/codex/agent-configuration/subagents | Subagent config |
| Codex Hooks | https://developers.openai.com/codex/hooks | Hook events |
| Codex MCP | https://developers.openai.com/codex/extend/mcp | MCP wiring |
| Claude Code Plugins | https://docs.claude.com/en/docs/claude-code/plugins | 5-component structure |
| Claude Code Skills | https://docs.claude.com/en/docs/claude-code/skills | Frontmatter reference |
| Claude Code Hooks | https://docs.claude.com/en/docs/claude-code/hooks | Event reference |
| Claude Code MCP | https://docs.claude.com/en/docs/claude-code/mcp | MCP integration |
| Claude Code Sub-agents | https://docs.claude.com/en/docs/claude-code/sub-agents | Subagent definition |
| Anthropic Skills blog | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | Scripts vs instructions |
| agentskills.io spec | https://agentskills.io/specification | Open-standard format |
| MCP spec | https://modelcontextprotocol.io/specification/2025-06-18/ | Tools, Resources, Prompts, Sampling, Elicitation, Tasks |
| OpenAI Tools | https://platform.openai.com/docs/guides/tools | Tool types |

## Appendix B: Prior research

This SPEC builds on three prior research outputs:

- [`../build-ios-apps/`](../build-ios-apps/) — structural template for the 9-skill lineup (iOS plugin was a reference, not a platform comparison)
- [`../android-skills/`](../android-skills/) — format reference (Google's open-standard adoption)
- [`../advanced-improved/`](../advanced-improved/) — research on advanced plugin features (slash commands, subagents, hooks, full MCP surface) from Claude Code + MCP spec + agentskills.io deep dives
