# Hooks Reference

This plugin uses 6 hook handlers across 4 events to provide safety, automation, gating, and end-of-turn summaries.

## Hook events

| Event | Matcher | Script | Purpose |
|---|---|---|---|
| `SessionStart` | `startup\|resume\|clear\|compact` | `session-start.sh` | Detect SDK / adb / devices; state.json phase report; frontdoor reminder |
| `PreToolUse` | `Bash` | `block-destructive.sh` | Block destructive shell commands before they run |
| `PreToolUse` | `mcp__plugin_build_android_apps_play_store__submit_for_review\|upload_aab` | `release-check.sh` | Gate Play Store submissions (keystore/listing/screenshots) |
| `PostToolUse` | `Edit\|Write\|MultiEdit\|apply_patch` | `lint-kotlin.sh` | Run ktlint on edited Kotlin files |
| `PostToolUse` | `Edit\|Write\|MultiEdit\|apply_patch` | `slop-gate.sh` | Block AI-slop residue in Kotlin (verbose comments, emoji, placeholder) |
| `Stop` | (none — Stop event) | `stop-review.sh` | Print git diff stat at end of turn |

## Configuration

All hooks are registered in `hooks/hooks.json`. Each hook uses `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` (Codex canonical + Claude compat) so paths resolve regardless of host.

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
3. Use `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` in paths.
4. Test by editing the script and triggering the event manually.

## Hook scripts

| Script | Lines | Blocks? |
|---|---|---|
| `session-start.sh` | ~115 | No — emits info context (frontdoor + state) |
| `block-destructive.sh` | ~58 | Yes — denies destructive patterns |
| `release-check.sh` | ~66 | Yes — denies submit if keystore/listing missing (via PreToolUse) |
| `lint-kotlin.sh` | ~75 | No — emits ktlint findings |
| `slop-gate.sh` | ~79 | Yes — denies slop residue (via PostToolUse) |
| `stop-review.sh` | ~35 | No — emits git diff stat |

## Patterns blocked by `block-destructive.sh`

| Pattern | Reason |
|---|---|
| `./gradlew clean` | Destructive; use `/clean` for confirmation flow |
| `rm -rf /` or `~` | Irreversible; narrow the path |
| `adb pm uninstall` without package | Easy to uninstall the wrong app |
| `adb shell pm clear` | Wipes app data; prefer the MCP tool |
| `fastboot erase/format/wipe` | Irreversible; needs explicit user confirmation |
