# Hooks Reference

This plugin uses 4 hook events to provide safety, automation, and end-of-turn summaries.

## Hook events

| Event | Matcher | Script | Purpose |
|---|---|---|---|
| `SessionStart` | `.*` | `session-start.sh` | Detect SDK / adb / connected devices; emit plugin reminder |
| `PreToolUse` | `Bash` | `block-destructive.sh` | Block destructive shell commands before they run |
| `PostToolUse` | `Edit\|Write\|MultiEdit` | `lint-kotlin.sh` | Run ktlint on edited Kotlin files |
| `Stop` | `.*` | `stop-review.sh` | Print git diff stat at end of turn |

## Configuration

All hooks are registered in `hooks/hooks.json`. Each hook uses the `${CLAUDE_PLUGIN_ROOT}` env var so paths resolve correctly regardless of install location.

## Output format

Hooks emit JSON to stderr (Codex / Claude Code convention). The output format is:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

For non-blocking hooks (SessionStart, PostToolUse), use `additionalContext` instead of `permissionDecision`:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "[info] adb sees 1 device(s)..."
  }
}
```

## Adding new hooks

1. Add the script to `hooks/`.
2. Register it in `hooks/hooks.json` under the relevant event.
3. Use `${CLAUDE_PLUGIN_ROOT}` in paths.
4. Test by editing the script and triggering the event manually.

## Hook scripts

| Script | Lines | Blocks? |
|---|---|---|
| `session-start.sh` | 50 | No — emits info context |
| `block-destructive.sh` | 60 | Yes — denies 5 destructive patterns |
| `lint-kotlin.sh` | 50 | No — emits ktlint findings |
| `stop-review.sh` | 30 | No — emits git diff stat |

## Patterns blocked by `block-destructive.sh`

| Pattern | Reason |
|---|---|
| `./gradlew clean` | Destructive; use `/clean` for confirmation flow |
| `rm -rf /` or `~` | Irreversible; narrow the path |
| `adb pm uninstall` without package | Easy to uninstall the wrong app |
| `adb shell pm clear` | Wipes app data; prefer the MCP tool |
| `fastboot erase/format/wipe` | Irreversible; needs explicit user confirmation |
