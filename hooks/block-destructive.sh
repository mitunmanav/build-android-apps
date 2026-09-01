#!/usr/bin/env bash
# PreToolUse hook: block destructive Bash commands.
# Reads the tool input from stdin (JSON) and decides whether to allow.

set -u

INPUT="$(cat)"

# Extract the command string from various shapes
CMD="$(printf '%s' "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    # Claude Code: { tool_name, tool_input: { command: '...' } }
    print(d.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
")"

if [ -z "$CMD" ]; then
    exit 0  # nothing to check
fi

# Destructive patterns. Each pattern is paired with a human-readable reason.
deny() {
    local reason="$1"
    cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"$reason"}}
EOF
    exit 0
}

# 1. gradlew clean (without explicit --rerun-tasks or other safe args)
if echo "$CMD" | grep -qE '(\./gradlew|gradle)\s+(\S+\s+)*clean\b'; then
    deny "Refused: ./gradlew clean is destructive. Use /clean (which prompts for confirmation) or pass --rerun-tasks to refresh only the affected module."
fi

# 2. rm -rf against broad paths
if echo "$CMD" | grep -qE 'rm\s+(-[rRfF]+\s+)*(/\$|~|/\s*$|/\*|~/\*)'; then
    deny "Refused: 'rm -rf' against home, root, or glob. Narrow the path or use a safer alternative."
fi

# 3. adb uninstall without package context
if echo "$CMD" | grep -qE '\badb\s+(shell\s+)?pm\s+uninstall\b' && ! echo "$CMD" | grep -qE '\b(com\.[a-z0-9_.]+|android\.[a-z0-9_.]+)\b'; then
    deny "Refused: 'adb pm uninstall' without a fully-qualified package name. Confirm the package first."
fi

# 4. adb shell pm clear (clears app data)
if echo "$CMD" | grep -qE '\badb\s+(shell\s+)?pm\s+clear\b'; then
    deny "Refused: 'pm clear' wipes app data. Use mcp__plugin_build_android_app_plugin_adb__clear_app_data via the adb-mcp server (it prompts) or run /crash to see if a clear is even needed."
fi

# 5. wipe data via fastboot (locked devices)
if echo "$CMD" | grep -qE '\bfastboot\s+(erase|format|wipe)\b'; then
    deny "Refused: fastboot erase/format/wipe is irreversible. Confirm the target partition and user data loss with the user first."
fi

exit 0
