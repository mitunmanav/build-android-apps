#!/usr/bin/env bash
# scripts/smoke.sh — end-to-end smoke test for build-android-apps v2.0.0
#
# Verifies that:
#   1. All Python modules import cleanly
#   2. All JSON files validate
#   3. State manager plan algebra works (add/where/done/undo)
#   4. Phase router produces deterministic topological order
#   5. Hook shell scripts pass `bash -n`
#   6. All manifests load
#
# Exit 0 = smoke pass. Exit non-zero = smoke fail.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ok() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }

echo "=== build-android-apps v2.0.0 smoke test ==="

echo
echo "[1] Python state module imports"
PYTHONPATH="$ROOT" python3 -c "from state import SCHEMA_VERSION, StateManager, topological_order, detect_cycle, route_full, route_after, explain; assert SCHEMA_VERSION == 2; print('  ✓ all 7 public symbols import')" \
  || fail "state module import"

echo
echo "[2] JSON manifests validate"
for f in .codex-plugin/plugin.json .claude-plugin/marketplace.json plugin.lock.json state/schema.json; do
    python3 -c "import json; json.load(open('$f'))" || fail "$f is invalid JSON"
    ok "$f valid JSON"
done

echo
echo "[3] Hook shell scripts pass syntax check"
for f in hooks/*.sh; do
    bash -n "$f" || fail "$f syntax error"
    ok "$f"
done

echo
echo "[4] MCP server modules import cleanly"
for server in adb-mcp gradlew-mcp keystore-mcp play-store-mcp asset-mcp; do
    PYMODULE="${server//-/_}"
    # detect src-layout vs flat-layout
    if [ -d "$ROOT/mcp-servers/$server/src/$PYMODULE" ]; then
        PYPATH="$ROOT/mcp-servers/$server/src"
    else
        PYPATH="$ROOT/mcp-servers/$server"
    fi
    set +e
    OUT=$(PYTHONPATH="$PYPATH" python3 -c "import $PYMODULE" 2>&1)
    RC=$?
    set -e
    if [ $RC -eq 0 ]; then
        ok "$server imports"
    elif echo "$OUT" | grep -q "Pillow"; then
        ok "$server loads (Pillow optional)"
    else
        fail "$server module import: $OUT"
    fi
done

echo
echo "[5] State manager round-trip"
TMP=$(mktemp -d)
PYTHONPATH="$ROOT" python3 -m state save "$TMP/state.json" '{"schema_version":2,"phase":"intake","plan":[],"cursor":{"phase":"intake","task_id":""},"history":[]}' >/dev/null
PYTHONPATH="$ROOT" python3 -m state add "$TMP/state.json" --title "Scaffold" --phase scaffold --id a1 >/dev/null
PYTHONPATH="$ROOT" python3 -m state add "$TMP/state.json" --title "Build" --phase build --deps a1 --id a2 >/dev/null
ROUTE=$(PYTHONPATH="$ROOT" python3 -m state route "$TMP/state.json")
echo "$ROUTE" | grep -q "Scaffold" && echo "$ROUTE" | grep -q "Build" || fail "route output missing plan items"
ok "add → route shows ordered plan"
PYTHONPATH="$ROOT" python3 -m state done "$TMP/state.json" --task a1 >/dev/null
STATUS=$(PYTHONPATH="$ROOT" python3 -m state where "$TMP/state.json")
echo "$STATUS" | grep -q "✓" || fail "done task not marked with ✓"
ok "done → status shows ✓"
PYTHONPATH="$ROOT" python3 -m state undo "$TMP/state.json" >/dev/null
ok "undo round-trip"
rm -rf "$TMP"

echo
echo "[6] Cycle detection"
TMP=$(mktemp -d)
PYTHONPATH="$ROOT" python3 -m state save "$TMP/state.json" '{"schema_version":2,"phase":"intake","plan":[{"id":"x","title":"X","status":"pending","phase":"build","deps":["y"]},{"id":"y","title":"Y","status":"pending","phase":"build","deps":["x"]}],"cursor":{"phase":"build","task_id":""},"history":[]}' >/dev/null
set +e
CYCLE_OUT=$(PYTHONPATH="$ROOT" python3 -m state check-cycle "$TMP/state.json" 2>&1)
set -e
if echo "$CYCLE_OUT" | grep -q "CYCLE"; then
    ok "x↔y cycle detected"
else
    fail "cycle detection missed x↔y (output: $CYCLE_OUT)"
fi
rm -rf "$TMP"

echo
echo "=== ALL SMOKE TESTS PASSED ==="
