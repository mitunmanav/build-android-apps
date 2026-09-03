#!/usr/bin/env bash
set -u
fail=0
OUT=$(CURSOR_PLUGIN_ROOT=/x CLAUDE_PLUGIN_ROOT=/y bash hooks/session-start 2>/dev/null)
echo "$OUT" | grep -q '"additional_context"' || { echo "FAIL cursor shape"; fail=1; }
echo "$OUT" | grep -q 'hookSpecificOutput' && { echo "FAIL cursor double-inject"; fail=1; }
OUT2=$(CLAUDE_PLUGIN_ROOT=/y bash hooks/session-start 2>/dev/null)
echo "$OUT2" | grep -q 'hookSpecificOutput' || { echo "FAIL claude shape"; fail=1; }
OUT3=$(COPILOT_CLI=1 CLAUDE_PLUGIN_ROOT=/y bash hooks/session-start 2>/dev/null)
echo "$OUT3" | grep -q '"additionalContext"' || { echo "FAIL copilot shape"; fail=1; }
echo "$OUT3" | grep -q 'hookSpecificOutput' && { echo "FAIL copilot double-inject"; fail=1; }
[ "$fail" -eq 0 ] && echo HOOK-SHAPES-OK
exit "$fail"
