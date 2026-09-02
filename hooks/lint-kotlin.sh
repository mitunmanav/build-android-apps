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
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[info] ktlint not installed; skipping lint check for %s. Install: brew install ktlint or add ktlint gradle plugin."}}\n' "$FILE"
    exit 0
fi

# Run ktlint on the single file (token-cheap: never full project scan)
if [ "$KTLINT" = "./gradlew ktlintCheck" ]; then
    # Prefer single-file ktlint if installed, else fallback to quiet single-file check via ktlint binary search
    if command -v ktlint >/dev/null 2>&1; then
        OUT=$(ktlint "$FILE" 2>&1 || true)
    else
        # Full project scan is expensive — skip and hint
        printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[info] ktlint binary not found for single-file lint; skipping full ./gradlew ktlintCheck to save tokens for %s"}}\n' "$FILE"
        exit 0
    fi
else
    OUT=$("$KTLINT" "$FILE" 2>&1 || true)
fi

if [ -n "$OUT" ] && echo "$OUT" | grep -qiE 'error|warning'; then
    ESC_OUT=$(printf '%s' "$OUT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read())[1:-1])' 2>/dev/null || printf '%s' "$OUT")
    ESC_FILE=$(printf '%s' "$FILE" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read())[1:-1])' 2>/dev/null || printf '%s' "$FILE")
    printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[warning] ktlint findings for %s:\n%s"}}\n' "$ESC_FILE" "$ESC_OUT"
fi

exit 0
