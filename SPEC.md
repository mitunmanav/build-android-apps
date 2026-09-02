# Build Android Apps — Specification

**Version**: 2.0.0
**Status**: Active (v1.0.0 → v2.0.0 — renames plugin to `build-android-apps`, adds frontdoor router)
**Author**: Mitun
**License**: Apache-2.0

## 1. Goals

A single plugin that lets a **non-technical person** ship an Android app to Google Play
Store by typing plain English. The agent handles every Android-specific step
(SDK, Gradle, Kotlin, Compose, signing, AAB, Play Store API, store listing, updates).
The user only handles Google-side paperwork: Play Console account ($25), ID
verification, and banking setup.

### 1.1 What this plugin does

- **29 skills** (1 frontdoor `build-android-apps` + 28 specialists) covering full lifecycle intake → ship → update; progressive disclosure keeps startup under 8k token budget ([see references/codex-docs-audit.md](references/codex-docs-audit.md))
- **32 slash commands** in plain English (`/make-app`, `/add`, `/change`, `/publish`, `/update`, `/status`, `/run-plan`, `/slop`) — all delegate to frontdoor
- **8 subagents**: 4 loop agents (implementer, spec-reviewer, quality-reviewer, qa-user) + 4 validation agents (intake-clarifier, build-validator, release-auditor, apk-inspector)
- **5 MCP servers** (Python, stdio): `adb-mcp`, `gradlew-mcp`, `play-store-mcp`, `keystore-mcp`, `asset-mcp`
- **6 hook handlers** across 4 events (SessionStart, PreToolUse×2, PostToolUse×2 incl. slop-gate, Stop) — no `PreSubmit` (invalid per `codex/hooks` docs; use `PreToolUse` with tool matcher)
- **Per-project state.json (schema v2)** with deterministic resume from any phase (Kahn router, no LLM) plus orchestration-loop sections (`orchestration{}`, `ledger[]`, `agents[]`, `constraints[]`)
- **Multi-host packaging**: Codex CLI, Claude Code CLI, `.agents` standard hosts
- **Pairing** with Google's `android/skills` (via `android skills add --all`)

### 1.2 What this plugin does NOT do

- Not iOS, Wear, TV, Auto, or XR (those are platform-specific sibling plugins)
- Not custom backend hosting (Firebase + Supabase templates only; raw backend v1.1+)
- Not multi-user collaboration (single-user per project state.json)
- Not AGP 9.x (AGP 8.7 stable for v1.0; AGP 9 in v1.1)
- Not a vibe-coder wrapper UI (plugin lives in Codex/Claude/.agents CLI hosts)
- Not state schema v2+ migrations (only v1)

## 2. Differentiation

Why this plugin when Google's [`android/skills`](https://github.com/android/skills)
(7.1k stars), [`test-android-apps`](https://github.com/openai/plugins) (OpenAI official),
and [`ayush016/android-lead-agent-skills`](https://github.com/ayush016/android-lead-agent-skills)
exist?

| | `android/skills` (Google) | `test-android-apps` (OpenAI) | `ayush016` | **This plugin** |
|---|---|---|---|---|
| Coverage | 16 domain SKILLs (Compose, camera, media, security, system, etc.) | Testing only (QA, Perfetto, leaks) | Team standards (architecture, theming, performance) | **Full lifecycle: intake→ship→update** |
| Tooling | Skills only (no MCP, no commands) | Raw adb shell + 2 skills + scripts/ | Single SKILL + 17 references | 29 skills (1 frontdoor + 28) + 32 commands + 5 MCP + 6 hooks + agent-orchestrator loop |
| Shipping | No (knowledge only) | No | No | **Yes** (`/publish` → Play Store upload) |
| Resume | No | No | No | **Yes** (state.json + Kahn's phase-router) |
| Resume-aware | No | No | No | **Yes** (`/add` `/remove` `/change` mid-loop) |
| Target user | Any AI assistant | Test engineers | Android lead engineers | **Non-technical vibe coders** |
| Cold-start setup | No | No | No | **Yes** (`/setup` wizard) |

**This plugin complements, does not replace**:
- Install `android/skills` for domain knowledge (`android skills add --all`)
- Install `test-android-apps` for advanced profiling
- Reference `ayush016` for team standards (copy patterns into your project's `AGENTS.md`)

## 3. Target Users

### 3.1 Primary

Non-technical vibe coders. They:

- Type plain English, sometimes vague or bad
- Use Codex CLI / Claude Code CLI / `.agents` standard host
- Don't know what Android SDK, Gradle, Kotlin, Compose, AAB, or signing mean
- Handle only Google-side paperwork (Play Console account, ID, banking)
- Expect the agent to fix its own errors and explain what happened in plain English

### 3.2 Secondary

Technical "facilitators" who run the plugin on behalf of non-tech clients. They:

- Use the same hosts
- May have Android experience but want a faster loop
- Need to ship apps that other AI tools (Lovable, Bolt, v0, Cursor, Replit, ChatGPT) generated

### 3.3 Author

Mitun — single maintainer, single brand, no co-authors.

## 4. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                AI Host (Codex CLI / Claude Code CLI /
│                .agents standard host)
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Plugin manifests (.codex-plugin/, .claude-plugin/,
│  .agents/plugins/) + plugin.lock.json (sha256)
└──────────┬───────────────┬─────────────────┬─────────────┘
           │               │                 │
           ▼               ▼                 ▼
        Skills (28)   Commands (30)   MCP servers (5)
   (1 frontdoor + 27)  plain-English    adb, gradlew, play-store,
        references/   per skill          keystore, asset
               │                            │
               ▼                            ▼
           Subagents (4)              Hooks (5) handlers / 4 events
           intake-clarifier           SessionStart, PreToolUse×2,
           build-validator            PostToolUse, Stop
           release-auditor            (release-check via PreToolUse
           apk-inspector               matcher, no PreSubmit)
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  Per-project state.json (<project>/.build-android/)
│  schema_version, phase, plan[], cursor, build, device,
│  store, keystore, environment, crashlytics, rejections,
│  history[50] — gitignored, deterministic phase-router
└─────────────────────────────────────────────────────────┘
```

### 4.1 Resumable loop contract

Six rules that every subagent/skill MUST obey:

```
R1  Plan is single source of truth. User-approved = locked until edited.
R2  Add/remove/reorder plan items = first-class ops (no restart).
R3  Phase entry checks (phase, next_pending_id) → only runs next step.
R4  Re-entering same phase = idempotent (skip done tasks).
R5  STOP preserves partial state. Never delete partial files.
R6  SessionStart loads state.json → "you're at phase X step Y".
```

### 4.2 phase-router algorithm

Deterministic, no LLM call:

```
delta = new user request
for task in plan where task.status != done and (deps met OR delta forces):
    mark task.phases in [build_affected...] -> enqueue
return ordered phases from deps graph (Kahn's algorithm)
```

## 5. Skills (28)

All skills follow the [agentskills.io open-standard format](https://agentskills.io/specification).
Per-skill UI metadata (Codex-only) lives in `agents/openai.yaml`; other hosts ignore it.

### 5.1 Frontmatter (open-standard, multi-host safe)

```yaml
---
name: <skill-name>
description: >
  <Multi-sentence trigger phrase. State when to use AND when not to use.
  Under 1024 chars (agentskills.io spec limit).>
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: 'YYYY-MM-DD'
  keywords: [android, ...]
---
```

**Hard constraints** (enforced by `skills-ref validate`):

- `name`: 1-64 chars; `^[a-z0-9]+(-[a-z0-9]+)*$`; no leading/trailing hyphen; no `--`
- `description`: 1-1024 chars
- SKILL.md body: under 500 lines (move detail to `references/`)
- Reference paths: relative, one level deep

### 5.2 Body template

```markdown
# <Skill Name>

> [!NOTE]
> One-line description of what this skill does.

## Prerequisites

- Dep 1 (versions, packages)
- Dep 2

## Workflow

### Step 1: ...
### Step 2: ...
### Step 3: ...

## Anti-patterns

- **DO NOT** do X
- **DO NOT** do Y

## Pairing

- `<other-skill>` — when to call this
- `<mcp-tool>` — how to use it

## References

- See [references/setup.md](references/setup.md)
- External: https://developer.android.com/...

## Final Checklist

- [ ] Step 1 verified
- [ ] Step 2 verified
```

### 5.3 Per-skill agents/openai.yaml (Codex-only)

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
    - type: "cli"
      value: "adb"
      description: "Android Debug Bridge"
```

### 5.4 29-skill lineup (1 frontdoor + 28 specialists)

| # | Skill | Purpose | MCP deps |
|---|---|---|---|
| 0 | `build-android-apps` | **Frontdoor**: plain English → intent classify → delegate to one specialist (progressive disclosure, `allow_implicit_invocation:true`; specialists are `false`) | state |
| 1 | `app-intake` | Vague prompt → concrete plan; asks N clarifying questions in plain English | (state.json only) |
| 2 | `android-scaffold` | Bootstrap Gradle/Compose/signing project from spec | `gradlew-mcp` |
| 3 | `android-build` | assembleDebug/release, sane defaults, --no-daemon, lightweight verification | `gradlew-mcp` |
| 4 | `android-run` | Install + launch + screenshot | `adb-mcp` |
| 5 | `android-debug-fix` | Logcat + agent-driven fix loop | `adb-mcp` |
| 6 | `android-debugger-agent` | JDWP attach + breakpoint flow | `adb-mcp` |
| 7 | `android-emulator-browser` | Emulator UI automation (tap/swipe/layout dump) | `adb-mcp` |
| 8 | `android-profiler` | Perfetto / Simpleperf profiling | `adb-mcp` |
| 9 | `android-leak-analyzer` | Heap dump + leak analysis | `adb-mcp` |
| 10 | `android-app-functions` | App Functions exposure (Android 16+) | (none) |
| 11 | `compose-performance-audit` | Recomposition, stability, baseline profiles | `gradlew-mcp` |
| 12 | `compose-ui-patterns` | Lists, nav, forms, state hoisting | (none) |
| 13 | `compose-view-refactor` | View → Compose migration | (none) |
| 14 | `material3-expressive` | M3 expressive theming | (none) |
| 15 | `android-importer` | Detect + audit + finish apps built by other AI tools (Lovable, Bolt, v0, etc.); snapshot-on-import | `gradlew-mcp` |
| 16 | `android-backend` | Data layer (Room + DataStore) + Network (Retrofit/OkHttp); Supabase + Firebase templates | (none) |
| 17 | `android-auth` | Credential Manager + sign-in flow; integration-point discovery via search strings | (none) |
| 18 | `android-ops` | Push (FCM) + Analytics (Firebase) + Background (WorkManager) + Crashlytics auto-wire | (none) |
| 19 | `android-media` | CameraX + Media3 (ExoPlayer) | (none) |
| 20 | `android-restore-credentials` | Sign-in with restore keys (Credential Manager); SYSTEM DIRECTIVE pattern for backend fence | (none) |
| 21 | `android-verified-email` | OTP-less email verification (Credential Manager + SD-JWT) | (none) |
| 22 | `android-edge-to-edge` | SDK 35+ mandatory edge-to-edge; RIGHT/WRONG code pairs pattern | (none) |
| 23 | `android-icons-assets` | Launcher icon + adaptive layers + feature graphic; two-tier checklist (agent + user) | `asset-mcp` |
| 24 | `android-store-listing` | Play Store title/desc/short/long/screenshots/privacy URL; data safety form inference; content rating | (none) |
| 25 | `agent-orchestrator` | Autonomous plan-execution loop: fresh implementer per task → device evidence → two read-only reviews → bounded fix loop (≤5) → resumable ledger; modes guided/autopilot; staleness cap; see §7.2 | state |
| 26 | `android-publish-update` | Keystore + signed AAB + Play upload + version bump + changelog | `play-store-mcp`, `keystore-mcp` |
| 27 | `android-r8-analyzer` | APK size optimization; strict-output-limit pattern; report sections with "omit if no findings" | `gradlew-mcp` |
| 28 | `setup-wizard` | First-run setup: SDK install + Play Console signup + service account + ID verification + banking | `gradlew-mcp`, `play-store-mcp` |

### 5.5 references/ per skill

Every skill has `references/<topic>.md` for content >500 lines. SKILL.md body ≤100 lines.

Pattern (matching Google's `android/skills` and `ayush016/android-lead-agent-skills`):
- `references/setup.md` — installation, prerequisites
- `references/patterns.md` — code patterns with RIGHT/WRONG pairs
- `references/troubleshooting.md` — common errors + fixes
- `references/checklist.md` — agent self-check + user checklist
- `references/references.md` (optional) — external links, deeper reads

## 6. Slash Commands (30)

Commands are Claude Code (and Antigravity/Gemini) slash-command aliases to the frontdoor skill. Codex does not load plugin slash commands — there, invoke the frontdoor skill directly (`$build-android-apps` or `@build-android-apps`).

### 6.1 Frontmatter pattern

```markdown
---
description: Build the app with Gradle
allowed-tools:
  - mcp__plugin_build_android_apps_gradlew__run_task
  - mcp__plugin_build_android_apps_gradlew__list_tasks
  - mcp__plugin_build_android_apps_adb__list_devices
  - Read
  - Grep
---

## Context

- Working directory: !`pwd`
- State: !`cat .build-android/state.json 2>/dev/null || echo "no state yet"`
- Recent commits: !`git log --oneline -5`

## Reporting Action

> [!IMPORTANT]
> Before proceeding, immediately tell the user: "I will [action description]."

## Your task

$ARGUMENTS

### Step 1: Determine target task
...

## Anti-patterns

- **DO NOT** `gradlew clean` unless explicitly asked
- **DO NOT** pipe Gradle to `grep` (use MCP's structured output)

## Final Checklist

- [ ] Step 1 verified
- [ ] Step 2 verified
```

### 6.2 32 commands (all delegate to frontdoor)

| # | Command | MCP tools pre-allowed | Purpose |
|---|---|---|---|
| 1 | `/setup` | `gradlew.manage_sdk`, `play-store.auth` | First-run wizard: SDK + Play Console + service account |
| 2 | `/make-app` | `gradlew.run_task`, `adb.list_devices` | Full intake → spec → scaffold |
| 3 | `/add` | all | Add feature to plan without restart |
| 4 | `/change` | all | Modify existing plan item |
| 5 | `/remove` | all | Remove plan item + cleanup touched files |
| 6 | `/continue` | all | Resume from current phase |
| 7 | `/where` | (state.json only) | Show current phase + plan progress + blockers |
| 8 | `/status` | `play-store.get_stats`, `gradlew.run_task` | Post-publish dashboard (downloads, ratings, crashes) |
| 9 | `/publish` | `play-store.upload`, `keystore.use` | Store listing + submit to internal test track |
| 10 | `/update` | `play-store.upload`, `gradlew.run_task` | New version + changelog + resubmit |
| 11 | `/reset` | (destructive gate) | Reset project state (double-confirm) |
| 12 | `/backup-keystore` | `keystore.copy` | Copy keystore to safe place (Google Drive / USB) |
| 13 | `/why-rejected` | `play-store.get_review_status` | Parse Play rejection, auto-diagnose, fix-and-resubmit |
| 14 | `/import` | `gradlew.describe_project` | Detect existing Android project (Kotlin/Compose/XML/Java) |
| 15 | `/audit` | `gradlew.parse_dependencies`, `gradlew.find_duplicate_classes` | List gaps for Play Store ship |
| 16 | `/finish` | `keystore.generate_keystore`, `gradlew.run_task` | Auto-fill gaps + publish-to-internal-test-track |
| 17 | `/screenshots` | `adb.screencap`, `asset.generate` | Generate Play Store screenshots from running app |
| 18 | `/privacy-policy` | `gradlew.parse_dependencies` | Generate privacy policy + data safety section |
| 19 | `/help` | (none) | List of commands in plain English |
| 20 | `/debug` (dev alias) | `adb.shell_command`, `adb.logcat_dump` | Set up JDWP debug session |
| 21 | `/lint` (dev alias) | `gradlew.run_lint` | Run lint, summarize |

**MCP tool name format**: `<server>.<tool>` where `<server>` is the key in `.mcp.json`. When exposed by Codex, the fully-qualified tool name follows `mcp__plugin_<plugin_name_underscored>_<server>__<tool>`. For this plugin: `mcp__plugin_build_android_apps_<server>__<tool>`.

## 7. Subagents (8)

Each is a `.md` file with frontmatter (name, description with `<example>` block, tools, model) and system-prompt body.

### 7.1 Sub-agent prompt template (from Google's `play-policy-insights`)

All subagents use this pattern for context efficiency:

```
"Read your instructions from `<temp_dir>/prompt_<goal>.md` and execute.
 MANDATORY: You must use your file-writing capabilities to save your final
 findings directly to the file system at `<temp_dir>/worker_<goal>.json`.
 You are strictly forbidden from outputting the JSON in your chat response.
 To minimize context usage, your final response must be exactly 'SUCCESS'
 and nothing else."
```

**Containment Mandate**: All writes confined to `.scratch/<skill>-<uuid>/`.

**Concurrency limit**: Max 3 subagents simultaneously. Spawn batch, wait, spawn next.

### 7.2 8 subagents

| Agent | Purpose | Concurrency |
|---|---|---|
| `implementer` | Loop agent: implements ONE plan task from a brief file; TDD + device evidence; replies DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT ≤15 lines | 1 (serial — shared working tree) |
| `spec-reviewer` | Loop agent: read-only spec-compliance review of the task diff vs brief; "Do Not Trust the Report" | 2-way with quality-reviewer |
| `quality-reviewer` | Loop agent: read-only review against the FROZEN anti-slop rubric (`agent-orchestrator/references/quality-rubric.md`); may not invent criteria | (same turn) |
| `qa-user` | Loop agent: end-of-plan — uses the app as a real user via journeys; per-action PASSED/FAILED evidence | 1 |
| `intake-clarifier` | When prompt vague → returns N clarifying questions for user | 1 |
| `build-validator` | Pre-flight: lint + tests + dep check + R8 in parallel | 3-way parallel |
| `release-auditor` | Pre-publish: signing + listing + privacy + content rating + data safety; consumes slop score | 5-way parallel |
| `apk-inspector` | Deep APK inspection: manifest, DEX, resources, signing, per-component sizes | 1 |

Loop mechanics (dispatch templates, ledger line formats, resume, staleness
cap, model tiering, batching): see `skills/agent-orchestrator/` +
`references/prompt-templates.md` and `references/loop-contract.md`. The
`phase-router` remains deterministic Python (`state/router.py`), NOT an LLM
subagent. `rejection-parser` and `asset-generator` folded into
`release-auditor` + `asset-mcp` respectively (no separate agents).

## 8. Hooks (4 events, 6 handlers)

Per [Codex Hooks docs](https://developers.openai.com/codex/hooks) and [Claude Code Hooks docs](https://docs.claude.com/en/docs/claude-code/hooks). 4 events, 6 handlers (PreToolUse has 2, PostToolUse has 2).

| Event | Handler | Matcher | Purpose |
|---|---|---|---|
| `SessionStart` | `session-start.sh` | `startup\|resume\|clear\|compact` | Detect SDK/JDK/adb/devices; inject `hooks/bootstrap.md` meta-skill (routes plain English to the frontdoor, survives compaction); emit state.json phase |
| `PreToolUse` | `block-destructive.sh` | `Bash` | Block `gradlew clean`, `rm -rf`, `git reset --hard` unless confirmed |
| `PreToolUse` | `release-check.sh` | `mcp__plugin_build_android_apps_play_store__submit_for_review\|upload_aab` | Gate Play submissions (keystore/listing/screenshots) — PreToolUse is the verified event (no PreSubmit in Codex docs) |
| `PostToolUse` | `lint-kotlin.sh` | `Edit\|Write\|MultiEdit` | Run ktlint on edited `.kt` files |
| `PostToolUse` | `slop-gate.sh` | `Edit\|Write\|MultiEdit` | Advisory AI-slop scan on edited `.kt` files (deterministic subset of the frozen rubric: C1/C2/I1/I2/M1) — never blocks; enforcement lives in quality-reviewer |
| `Stop` | `stop-review.sh` | (all) | Plain-English session summary for user |

### 8.1 hooks.json (verified against `developers.openai.com/codex/hooks`)

```json
{
  "$schema": "https://json.schemastore.org/codex-hooks.json",
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

### 8.2 Plugin hook env vars

Codex sets `PLUGIN_ROOT` / `PLUGIN_DATA`; `CLAUDE_PLUGIN_ROOT` is compat alias. Hooks use `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` (see `references/codex-docs-audit.md`). `additionalContext` capped ~2,500 tokens (`additionalContextLimit`).

## 9. MCP Servers (5)

### 9.1 adb-mcp

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
| **`dump_layout`** | readOnly | **NEW** — JSON UI tree (matches Google's `android layout` shape: text/resourceId/contentDesc/interactions/state/bounds/center/off-screen) |

Plus:
- Resource: `adb://logcat/{device}/{buffer}` (subscribable)
- Prompt: `diagnose-app-crash`
- Elicitation: device picker, variant picker

### 9.2 gradlew-mcp

| Tool | Annotations | Purpose |
|---|---|---|
| `list_tasks` | readOnly | `./gradlew tasks --all` |
| `run_task` | (Task) | `./gradlew <task>` with progress; uses `--no-daemon` |
| `parse_dependencies` | readOnly | `./gradlew :app:dependencies` |
| `find_duplicate_classes` | readOnly | Find duplicate class deps |
| `run_lint` | (Task) | `./gradlew lint` |
| `run_tests` | (Task) | `./gradlew test` |
| `clean` | destructive (elicitation) | `./gradlew clean` |
| `stop_build` | (Task control) | Cancel running build |
| `get_build_status` | readOnly | Task status |
| `verify_keystore` | readOnly | Validate signing config |
| `generate_keystore` | (elicitation) | Generate keystore with masked password input |
| **`describe_project`** | readOnly | **NEW** — outputs JSON of build targets + APK paths (matches `android describe`) |
| **`manage_sdk`** | destructive | **NEW** — wrapper for `sdkmanager` (install/upgrade packages) |
| **`run_help`** | readOnly | **NEW** — lightweight verification gate (`./gradlew help`) |
| **`run_build_dry`** | readOnly | **NEW** — lightweight verification gate (`./gradlew build --dry-run`) |

Plus:
- Resource: `gradle://project/info`
- Resource: `gradle://build/{id}/report`
- Resource: `gradle://build/{id}/errors`
- Prompt: `explain-error`

### 9.3 play-store-mcp (NEW)

| Tool | Purpose |
|---|---|
| `auth` | OAuth + service account JSON upload |
| `upload_aab` | Upload AAB to internal test track |
| `upload_listing` | Upload localized store listing (title/desc/short/long) |
| `upload_screenshot` | Upload phone/tablet screenshots |
| `get_review_status` | Query Play review status |
| `list_rejections` | List past rejections with reasons |
| `submit_for_review` | Submit current draft for review |
| `rollout_staged` | Staged rollout (1% → 10% → 50% → 100%) |
| `get_stats` | Downloads, ratings, reviews, crash count |

### 9.4 keystore-mcp (NEW)

| Tool | Purpose |
|---|---|
| `generate_keystore` | Generate upload keystore with masked password elicitation |
| `verify_keystore` | Validate keystore + alias + passwords match |
| `rotate_keystore` | Rotate upload keystore (preserves app signing) |
| `backup` | Copy keystore to safe location with warning |
| `fingerprint` | SHA-256 fingerprint for verification |

### 9.5 asset-mcp (NEW)

| Tool | Purpose |
|---|---|
| `generate_icon` | Vector launcher icon + adaptive layers (foreground/background/monochrome) |
| `generate_feature_graphic` | 1024×500 feature graphic for Play Store |
| `generate_screenshot` | Compose running-app screenshot → 1080×1920 phone PNG |
| `compose_marketing` | Composite screenshots + text for promo |

### 9.6 Transport

All 5 servers use stdio transport. No HTTP, SSE, or WebSocket.

### 9.7 Python dependencies

- `mcp` (official SDK, async support)
- `pydantic` v2 (schema validation)
- `Pillow` (asset-mcp only)
- `cryptography` (keystore-mcp only)
- No other deps; `adb`, `gradle`, `sdkmanager` invoked via `subprocess.run`

## 10. Multi-host Packaging

### 10.1 Per-host rules

| Host | Manifest path | Format | Special fields |
|---|---|---|---|
| Codex CLI | `.codex-plugin/plugin.json` | Rich with `interface.*` | `interface`, `capabilities`, `defaultPrompt`, `brandColor` |
| Claude Code CLI | `.claude-plugin/marketplace.json` | Minimal | `$schema`, `category` per plugin |
| `.agents` standard | `.agents/plugins/marketplace.json` | Open-standard | Strict spec compliance |

### 10.2 plugin.lock.json (NEW — adopted from OpenAI `test-android-apps`)

```json
{
  "lockVersion": 1,
  "pluginId": "com.mitun.build-android-apps",
  "pluginVersion": "1.0.0",
  "generatedAt": "2026-09-01T00:00:00Z",
  "skills": [
    {
      "id": "app-intake",
      "vendoredPath": "skills/app-intake",
      "source": {
        "type": "github",
        "repo": "mitunmanav/build-android-apps",
        "path": "skills/app-intake",
        "ref": "<commit-sha>"
      },
      "integrity": "sha256-<digest>"
    }
  ]
}
```

Pin each of the 29 skills (1 frontdoor + 28 specialists) with sha256 for reproducible installs.

## 11. state.json Schema

Per-project file at `<project>/.build-android/state.json`. Gitignored.

### 11.1 Schema (v2)

v2 adds four orchestration-loop sections on top of v1; existing v1 files are
migrated transparently on first `StateManager` load (`state/migrate.py`).

```json
{
  "schema_version": 2,
  "constraints": [
    "<spec's global constraints, verbatim, one line each — injected into every task brief>"
  ],
  "orchestration": {
    "mode": "guided|autopilot",
    "status": "idle|running|stopped|awaiting_user",
    "fix_round": 0,
    "staleness": 0,
    "current_task_id": "<id>",
    "metrics": {
      "tasks_done": 0,
      "first_pass": 0,
      "fix_rounds_total": 0,
      "staleness_stops": 0,
      "ui_tasks_with_evidence": 0,
      "ui_tasks_total": 0
    }
  },
  "ledger": [
    { "at": "<iso8601>", "task_id": "<id>", "line": "Task N: complete (commits a..b, review clean)" }
  ],
  "agents": [
    { "at": "<iso8601>", "name": "implementer", "task_id": "<id>", "model": "sonnet", "status": "DONE" }
  ]
}
```

Ledger line formats: `Task N: complete (…)`, `Task N: fix round R/5 (…)`,
`Task N: minor (deferred): …`, `Task N: parked — … — Ruling: …`,
`Ruling: <what> — <why> — <cost if wrong>`. Ledger + agents are ring
buffers (200 / 100). Any ledger append resets `staleness`; 3 consecutive
stale steps → orchestrator stops and writes `resume.md`.

### 11.2 Field rules

- `history` is a ring buffer; last 50 entries only (`ledger` 200, `agents` 100)
- All mutations go through state-manager
- Snapshot to `.build-android/snapshot-<ts>/` on every /import
- Migration: `schema_version` 0→1→2 via `state/migrate.py`; StateManager upgrades transparently on load

## 12. Cold Start Wizard (`/setup`)

Non-tech user's first contact. 10 steps, ~30 min total.

```
Step 1:  Detect OS (Linux/macOS/Windows)
Step 2:  Check JDK → install if missing (sdkmanager + brew/apt)
Step 3:  Check Android SDK → install cmdline-tools + platform-tools
Step 4:  Check adb in PATH → add to PATH if missing
Step 5:  Detect connected device or emulator → install AVD if none
Step 6:  Prompt for Google account → create Play Console account ($25)
Step 7:  Walk through Google Cloud Console → create project + service account
Step 8:  Download service account JSON → save to .build-android/
Step 9:  Verify API access (test call to Play Developer API)
Step 10: Generate upload keystore → masked password → confirm backup
```

Each step shows a progress bar and a single sentence explaining what it does.

## 13. Versioning

- **Semver**: `0.1.0` → `1.0.0` → `1.1.0` → `2.0.0`
- `0.x` = pre-1.0; breaking changes allowed in minor
- `1.0.0+` = stable; breaking changes bump major
- Bump per release, commit message + CHANGELOG.md entry required

## 14. License

Apache-2.0 for the entire plugin. MCP servers, skills, scripts, hooks, docs — all Apache-2.0.

## 15. Distribution

- **v1.0.0**: Public GitHub repo + README install. No marketplace gate.
- **v1.1+**: Submit to:
  - [Anthropic Claude community marketplace](https://clau.de/plugin-directory-submission) (via claude.ai form)
  - Codex marketplace (when OpenAI opens public submissions)

### 15.1 Install instructions

```bash
# Codex CLI
codex plugin install github.com/mitunmanav/build-android-apps

# Claude Code CLI
claude plugin marketplace add mitun/mitun
claude plugin install build-android-apps@mitun

# .agents standard host
git clone https://github.com/mitunmanav/build-android-apps \
  ~/.agents/plugins/build-android-apps

# Pair with Google's android/skills
android skills add --all
```

## 16. Compatibility (pinned versions)

| Component | Version |
|---|---|
| Android Gradle Plugin | 8.7+ |
| Gradle | 8.9+ |
| Kotlin | 2.0.21 |
| Compose BOM | 2024.12.01 |
| min SDK | 26 (Android 8.0, ~98% device coverage) |
| target SDK | latest stable (default; ask during intake) |
| Material 3 | 1.3.x |
| Navigation Compose | 2.8.x |
| Credential Manager | 1.7.x |
| Hilt | 2.52 |
| Room | 2.6.x |
| DataStore | 1.1.x |
| CameraX | 1.4.x |
| Media3 | 1.4.x |

## 17. Pairs With

- **openai/plugins/test-android-apps** — advanced profiling (Perfetto, Simpleperf, heap dumps). Install in addition.
- **android/skills (Google)** — domain knowledge (Compose, camera, navigation, performance, security). Install via `android skills add --all`.
- **ayush016/android-lead-agent-skills** — team standards reference. Copy patterns into your project's `AGENTS.md`.

## 18. Limitations (out of scope v1.0)

- iOS, Wear, TV, Auto, XR — platform-specific sibling plugins (none exist yet)
- Custom backend hosting — Firebase + Supabase templates only; raw backend v1.1+
- Multi-user collaboration — single-user per project state.json
- Advanced IAP — basic consumable IAP template only; subscriptions v1.1+
- AGP 9.x — AGP 8.7 stable for v1.0; AGP 9 in v1.1
- State schema v2+ migrations — only v1 schema supported

## 19. Implementation Phases (14)

| # | Phase | Files | Verifies by |
|---|---|---|---|
| 0 | SPEC.md v1.0 (this file) | 1 | User approval |
| 1 | state.json schema v1 + migration stub + SessionStart loader | 3 | new project → `/where` works |
| 2 | state-manager + plan-mutator + `/where /continue /add /remove /change /undo` | 6 | mutate plan → state diff correct |
| 3 | phase-router (Kahn's deps, no LLM) | 1 | add screen at publish → re-runs build+test only |
| 4 | app-intake + app-planner + intake-clarifier subagent | 4 | vague prompt → plan in 2 turns, persists |
| 5 | android-scaffold + keystore-aware gradlew-mcp + Crashlytics silent-add | 4 | /make-app builds empty app with crash reporting |
| 6 | android-run + android-debug-fix + /preview + first-run /setup wizard | 5 | /make-app installs + screenshotted; cold start works |
| 7 | android-importer + /import /audit /finish + snapshot-on-import | 4 | /import on Lovable-built app detects + lists gaps + finishes |
| 8 | domain skills ×5 (backend, auth, ops, media, edge-to-edge) | 10 | typed feature works |
| 9 | restore-credentials + verified-email + r8-analyzer | 3 | sign-in + size optimization works |
| 10 | Supabase + Firebase template integration | 2 | app with backend works |
| 11 | android-icons-assets + asset-mcp | 2 | icon generated |
| 12 | android-store-listing + privacy/data-safety/content-rating generator | 1 | listing JSON validated |
| 13 | keystore-mcp + play-store-mcp + PreSubmit hook + /why-rejected + android-publish-update | 6 | /publish uploads draft; rejection loop works |
| 14 | README + 3-host smoke + cold-start E2E + import E2E + tag v1.0.0 | 5 | all hosts load |
| **TOTAL** | | **~57 files** | **~140h** |

At 6h/day = ~24 working days (~5 weeks).

## 20. Verification

### 20.1 Per-skill acceptance criteria

- [ ] `skills-ref validate skills/<name>` passes
- [ ] Description ≤ 1024 chars
- [ ] Frontmatter uses only open-standard spec fields (name, description, license, metadata)
- [ ] Body ≤ 500 lines (split to `references/` otherwise)
- [ ] `agents/openai.yaml` present for Codex UI
- [ ] `references/` subfolder present for skills >100 lines
- [ ] Final Checklist section present
- [ ] Tested in Codex: `$<skill-name>` resolves

### 20.2 Per-MCP-server acceptance criteria

- [ ] `python -m <server>` starts cleanly via stdio
- [ ] All tools listed via MCP `tools/list`
- [ ] Happy-path + error-path tested for each tool
- [ ] Elicitation triggers on multi-device scenarios
- [ ] Resources subscribable where applicable
- [ ] Containment Mandate: writes to `.scratch/` only
- [ ] Strict-output-limit pattern for report-producing tools

### 20.3 Per-hook acceptance criteria

- [ ] Fires on correct event
- [ ] `matcher` regex matches intended tool calls
- [ ] `if` field narrows further
- [ ] Script exits cleanly (or returns JSON `permissionDecision: deny`)

### 20.4 Plugin-level acceptance

- [ ] All 3 manifests valid JSON
- [ ] `plugin.lock.json` valid; sha256 matches for all 29 skills (regenerate via `scripts/update-lock.py`)
- [ ] `state.json` schema validator passes; migration v1→v2 stub works
- [ ] `codex --plugin-dir ./build-android-apps` loads all 29 skills + 32 commands + 8 agents + 6 hooks + 5 MCP servers
- [ ] `claude --plugin-dir ./build-android-apps` loads in Claude Code CLI
- [ ] `.agents` host loads the open-standard manifest
- [ ] Cold-start E2E: empty machine → /setup → published app on internal test track
- [ ] Import E2E: Lovable-built Compose app → /import → /audit → /finish → signed AAB on internal test track
- [ ] Rejection E2E: /publish → Google rejects → /why-rejected → fix → /publish again
- [ ] CI green: `skills-ref validate`, JSON schema, pytest
- [ ] GitHub repo created, tag `v1.0.0`, release notes

## 21. Approval

This SPEC requires Mitun's approval before Phase 1 begins.

---

## Appendix A: Sources cited

| Source | URL | Used for |
|---|---|---|
| Codex Plugins | https://developers.openai.com/codex/plugins/ | Plugin model |
| Codex Build Skills | https://developers.openai.com/codex/build-skills/ | SKILL.md format, agents/openai.yaml |
| Codex Hooks | https://developers.openai.com/codex/hooks | Hook events |
| Codex MCP | https://developers.openai.com/codex/extend/mcp | MCP wiring |
| Claude Code Plugins | https://docs.claude.com/en/docs/claude-code/plugins | 5-component structure |
| Claude Code Skills | https://docs.claude.com/en/docs/claude-code/skills | Frontmatter reference |
| Claude Code Hooks | https://docs.claude.com/en/docs/claude-code/hooks | Event reference |
| Claude Code MCP | https://docs.claude.com/en/docs/claude-code/mcp | MCP integration |
| Anthropic Skills blog | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | Scripts vs instructions |
| agentskills.io spec | https://agentskills.io/specification/ | Open-standard format |
| MCP spec | https://modelcontextprotocol.io/specification/2025-06-18/ | Tools, Resources, Prompts, Sampling, Elicitation, Tasks |
| Google android/skills | https://github.com/android/skills | Domain SKILLs (play, edge-to-edge, build-system, identity, testing, devtools, performance) |
| OpenAI plugins | https://github.com/openai/plugins | test-android-apps pattern; sibling plugin ecosystem |
| Anthropic community marketplace | https://github.com/anthropics/claude-plugins-community | Submission flow |
| ayush016/android-lead-agent-skills | https://github.com/ayush016/android-lead-agent-skills | Team standards reference; single-skill pattern |

## Appendix B: Patterns adopted from Google android/skills

| Pattern | Source skill | Adopted in our plugin |
|---|---|---|
| Sub-agent prompt template | `play-policy-insights` | `release-readiness`, `rejection-parser`, `asset-generator` subagents |
| Containment Mandate (`.scratch/<skill>-<uuid>/`) | `play-policy-insights` | All subagents |
| Strict-output-limit for reports | `r8-analyzer` | `apk-inspector` subagent (future), `/lint` command |
| Two-tier checklist (agent self-check + user checklist) | `engage-sdk-integration` | `android-icons-assets`, `android-store-listing`, `android-publish-update` |
| Reporting Action preamble | `play-billing-library-version-upgrade` | `/publish`, `/reset`, `/clean`, destructive commands |
| SYSTEM DIRECTIVE FOR AI AGENT | `restore-credentials` | `android-restore-credentials`, `android-verified-email` |
| Integration-point discovery via search strings | `verified-email` | `android-auth` |
| Diagnose → report → prescribe | `testing-setup` | `/device` command |
| Screenshot test grid (400/610/900 × 400/500/1000 dp) | `testing-setup` | `android-test` skill |
| Right/Wrong code pairs | `system/edge-to-edge` | `android-edge-to-edge`, `android-ui-patterns` |
| Numbered Steps headings | All | All skills |
| Final Checklist per skill | All | All skills |
| references/ at skill root, multi-level subdirs | All | All skills |
| Frontmatter slim (drop compatibility/allowed-tools/platform/version) | All | All skills |
| Fenced code blocks (kotlin/groovy/json/bash) | Most | All skills |
| Markdown alerts ([!NOTE], [!IMPORTANT], [!CAUTION]) | Most | All skills |
| "**DO NOT**" anti-pattern phrasing | Most | All skills |
| Mandatory prerequisites with version gates | Most | `android-edge-to-edge`, `android-restore-credentials`, `android-verified-email` |
| Lightweight verification gates (`./gradlew help`, `./gradlew build --dry-run`) | `build-system/agp/agp-9-upgrade` | `gradlew-mcp.run_help`, `gradlew-mcp.run_build_dry` |
| Anti-pattern: never `gradlew clean` for verification | `build-system/agp/agp-9-upgrade` | All skills, `lint-kotlin.sh` hook |
| Annotated screenshot pattern | `devtools/android-cli` | `/screenshots` command, `adb-mcp.screencap` |
| dump_layout JSON shape | `devtools/android-cli` | `adb-mcp.dump_layout` tool |
| describe_project JSON output | `devtools/android-cli` | `gradlew-mcp.describe_project` tool |
| manage_sdk wrapper | `devtools/android-cli` | `gradlew-mcp.manage_sdk` tool |