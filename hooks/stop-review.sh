#!/usr/bin/env bash
# Stop hook: emit a non-blocking review summary at the end of an agent turn.
# Shows recent git diff stats so the user has a summary of what changed.
# Intentionally simple — does NOT spawn an LLM call (keeps it cheap).

set -u

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

DIFF=$(git diff --stat HEAD 2>/dev/null | tail -10 || true)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -5 || true)

SUMMARY=""
if [ -n "$DIFF" ]; then
    SUMMARY="Modified files (last 10):
$DIFF"
fi

if [ -n "$UNTRACKED" ]; then
    SUMMARY="$SUMMARY

Untracked files (first 5):
$UNTRACKED"
fi

if [ -z "$SUMMARY" ]; then
    SUMMARY="No uncommitted changes."
fi

cat <<EOF
{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"[build-android-app-plugin] Review summary:\n$SUMMARY"}}
EOF

exit 0
