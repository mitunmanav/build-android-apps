#!/usr/bin/env bash
# PostToolUse hook: run ktlint on edited .kt files (best-effort).
# Skips silently if ktlint isn't installed.

set -u

INPUT="$(cat)"

# Extract file path from Edit/Write/MultiEdit (Claude Code) or apply_patch (Codex) tool input
FILE="$(printf '%s' "$INPUT" | python3 -c "
import json, sys, re
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', {})
    f = inp.get('file_path', inp.get('filepath', ''))
    if not f and 'command' in inp:
        # Codex apply_patch: parse '*** Begin Patch' or '*** Update File: <path>'
        m = re.search(r'\*\*\* (?:Begin Patch|Update File):\s*(\S+)', inp.get('command',''))
        if m:
            f = m.group(1)
    print(f)
except Exception:
    print('')
")"

if [ -z "$FILE" ]; then
    exit 0
fi

# Only Kotlin files
case "$FILE" in
    *.kt|*.kts) ;;
    *) exit 0 ;;
esac

# Skip if file doesn't exist (could have been deleted)
if [ ! -f "$FILE" ]; then
    exit 0
fi

# Find ktlint
KTLINT=""
if command -v ktlint >/dev/null 2>&1; then
    KTLINT="$(command -v ktlint)"
elif [ -x "./gradlew" ]; then
    # Use gradle wrapper if available
    KTLINT="./gradlew ktlintCheck"
fi

if [ -z "$KTLINT" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[info] ktlint not installed; skipping lint check for %s. Install: brew install ktlint or add ktlint gradle plugin."}}\n' "$FILE" >&2
    exit 0
fi

# Run ktlint on the single file
if [ "$KTLINT" = "./gradlew ktlintCheck" ]; then
    OUT=$(./gradlew ktlintCheck --quiet 2>&1 || true)
else
    OUT=$("$KTLINT" "$FILE" 2>&1 || true)
fi

if [ -n "$OUT" ] && echo "$OUT" | grep -qiE 'error|warning'; then
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[warning] ktlint findings for %s:\n%s"}}\n' "$FILE" "$OUT" >&2
fi

exit 0
