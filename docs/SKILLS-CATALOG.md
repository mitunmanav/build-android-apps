# Skills Catalog

Nine skills teach your AI assistant how to do specific Android jobs. Each skill is **prose-only** (no scripts) — the heavy lifting is done by the MCP servers (`adb-mcp`, `gradlew-mcp`) for typed tool calls, and the slash commands for fast invocation.

## All 9 skills

### 1. `android-debugger-agent`

Connect a device, attach the JDWP debugger, capture crash context, localize the failing call site.

**Use when**: user reports a crash, asks to "debug this", or wants to set breakpoints.

**Pairs with**: `/debug`, `/crash`, `/log`, `adb-mcp`.

### 2. `android-emulator-browser`

Launch and control an emulator (or physical device), drive UI by tapping/swiping, dump the view hierarchy, capture screenshots.

**Use when**: user wants to "see what's on screen", drive the app, verify a visual change.

**Pairs with**: `/device`, `/run`, `adb-mcp`.

### 3. `android-profiler`

Capture Perfetto system traces and macrobenchmark output. Diagnose jank, dropped frames, slow startup, high memory, excessive wakeups.

**Use when**: user reports "it's slow", scroll jank, slow startup.

**Pairs with**: `adb-mcp`, `gradlew-mcp`. After capturing, often switch to `compose-performance-audit`.

### 4. `android-leak-analyzer`

Detect, triage, and fix memory leaks using LeakCanary or heap dumps.

**Use when**: user reports memory growth, OOM crash, or "Activity destroyed but still held".

**Pairs with**: `adb-mcp`.

### 5. `android-app-functions`

Expose app functionality through the AppFunctions API (Android 16+) and App Shortcuts.

**Use when**: user asks to expose a feature to Assistant, add a launcher shortcut, let an agent trigger an action.

**Pairs with**: code-only, no MCP server.

### 6. `material3-expressive`

Apply Material 3 Expressive design: shape morphing, motion choreography, expressive color tokens, M3 component patterns.

**Use when**: user asks for "expressive UI", Material 3 Expressive, motion design, shape morphing.

**Pairs with**: `compose-ui-patterns`, `compose-performance-audit` (motion can trigger recomposition storms).

### 7. `compose-performance-audit`

Audit Compose UI for recomposition, stability, deferred reads, baseline profiles.

**Use when**: user asks to "review Compose performance", "why is this recomposing", or after observing jank.

**Pairs with**: `android-profiler` (capture first, then audit).

### 8. `compose-ui-patterns`

Pattern catalog for Compose UI: lists, navigation, forms, state hoisting, side effects, theming, accessibility, interop.

**Use when**: user asks "what's the right way to do X in Compose", is building a screen from scratch.

**Pairs with**: `material3-expressive`, `compose-performance-audit`.

### 9. `compose-view-refactor`

Refactor a large monolithic Composable into smaller, testable, state-hoisted pieces.

**Use when**: user asks to "refactor this composable", "split up this screen", or the file is > 200 lines.

**Pairs with**: `compose-performance-audit` (post-refactor audit), `compose-ui-patterns`.

## Composition patterns

Skills are designed to **compose**. Common combinations:

```
[android-profiler] captures trace
        ↓
[compose-performance-audit] reviews the offending recomposition
        ↓
[material3-expressive] applies an expressive fix
        ↓
[/build] rebuilds
        ↓
[/run] installs and launches
        ↓
[android-debugger-agent] confirms the fix
```

```
[android-debugger-agent] sees a leak
        ↓
[android-leak-analyzer] triages with LeakCanary
        ↓
[compose-view-refactor] splits the ViewModel
        ↓
[/test] confirms regression-free
```

## Skill loading

Skills are loaded **on-demand** when the agent sees `$skill-name` in the conversation, or when the slash command frontmatter triggers them. The skill body is read into context — keep it under 500 lines per the agentskills.io spec.

## Adding a new skill

1. Create `skills/<kebab-case-name>/`.
2. Write `SKILL.md` with the open-standard frontmatter (name, description ≤1024 chars, license, compatibility, allowed-tools, metadata).
3. Add `agents/openai.yaml` with display name + description for the Codex UI.
4. Validate: `python3 scripts/validate-skills.py .`
5. The skill is automatically discoverable by all 3 hosts.

Validators and structure are in `scripts/validate-skills.py`.
