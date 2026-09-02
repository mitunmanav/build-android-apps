#!/usr/bin/env bash
# slop-gate.sh — PostToolUse (Edit|Write|MultiEdit|apply_patch) advisory scan.
# Deterministic subset of the frozen quality rubric (skills/agent-orchestrator/
# references/quality-rubric.md): C1 swallowed errors, C2 placeholders, I1
# deferral, I2 hedging, M1 narrative comments. ADVISORY ONLY — never blocks;
# enforcement lives in the quality-reviewer verdict, not this hook.

set -u
stdin="$(cat)"

# Claude Code PostToolUse payload: {"tool_input": {"file_path": "...", ...}}
FILE="$(printf '%s' "$stdin" | python3 -c 'import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("tool_input",{}).get("file_path",""))
except Exception:
    print("")' 2>/dev/null || true)"

[ -n "$FILE" ] || exit 0
case "$FILE" in
  *.kt|*.kts) ;;
  *) exit 0 ;;
esac
[ -f "$FILE" ] || exit 0
# skip build/generated dirs
case "$FILE" in
  *build/*|*.gradle.kts) ;;  # keep .kts checks; skip build outputs
esac
case "$FILE" in
  */build/*) exit 0 ;;
esac

FINDINGS=""
add() { FINDINGS="${FINDINGS:+$FINDINGS
}- $1"; }

# C1 — swallowed errors (multiline-aware: catch (...) { only blanks/comments })
if python3 - "$FILE" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
found = False
for m in re.finditer(r"catch\s*\([^)]*\)\s*\{([^{}]*)\}", src):
    body = m.group(1)
    lines = [l.strip() for l in body.splitlines()]
    if all(not l or l.startswith("//") for l in lines):
        found = True
        break
sys.exit(0 if found else 1)
PY
then
  add "C1 empty catch block (swallowed error)"
fi

# C2 — placeholders
if grep -nE '\b(TODO|FIXME|HACK|XXX)\b' "$FILE" >/dev/null 2>&1; then
  add "C2 TODO/FIXME placeholder comment"
fi

# I1 — deferral language
if grep -niE '\b(for now|temporary fix|quick fix|temporary workaround)\b' "$FILE" >/dev/null 2>&1; then
  add "I1 deferral language ('for now' / 'temporary fix')"
fi

# I2 — hedging
if grep -niE '\b(should work|hopefully|probably fine|assumes that)\b' "$FILE" >/dev/null 2>&1; then
  add "I2 hedging language ('should work' / 'hopefully')"
fi

# M1 — narrative comment (comment restates a trailing line; heuristic: '// <verb> the' style)
if grep -nE '^\s*// (Set|Get|Create|Update|Return|Loop|Check|Call|Initialize) ' "$FILE" | head -1 | grep -q .; then
  add "M1 narrative comment (restates code; keep intent comments only)"
fi

if [ -n "$FINDINGS" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[slop-gate] advisory findings in %s (rubric: skills/agent-orchestrator/references/quality-rubric.md):\\n%s"}}\n' \
    "$(printf '%s' "$FILE" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read())[1:-1])' 2>/dev/null || printf '%s' "$FILE")" \
    "$(printf '%s' "$FINDINGS" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')"
fi
exit 0
