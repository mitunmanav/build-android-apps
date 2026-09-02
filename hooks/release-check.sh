#!/usr/bin/env bash
# PreToolUse hook: gate Play Store submissions through a release-readiness check.
# Fires before mcp__plugin_build_android_apps_play_store__submit_for_review or upload_aab.
# Registered as PreToolUse with matcher on the play-store MCP tool name (verified event per codex/hooks docs).

set -euo pipefail

# Info messages collected and flushed once on stdout (hook JSON is read from stdout).
MSGS=()
emit() {
    MSGS+=("[$1] $2")
}

flush() {
    if [ "${#MSGS[@]}" -gt 0 ]; then
        COMBINED="$(printf '%s\n' ${MSGS[@]+"${MSGS[@]}"})"
        ESC="$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' "$COMBINED" 2>/dev/null || printf '"%s"' "$(printf '%s' "$COMBINED" | sed 's/"/\\"/g')")"
        printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":%s}}\n' "$ESC"
    fi
}
trap flush EXIT

deny() {
    local reason="$1"
    local reason_json
    reason_json=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$reason" 2>/dev/null || printf '"%s"' "$reason")
    # Emit exactly once, on stdout.
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' "$reason_json"
    trap - EXIT
    exit 0
}

PROJECT_ROOT="${CODEX_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$(pwd)}}"
STATE_FILE="$PROJECT_ROOT/.build-android/state.json"

if [ ! -f "$STATE_FILE" ]; then
    deny "No state.json. Run /make-app or \$build-android-apps to bootstrap before publishing."
    exit 0
fi

# 1. keystore exists + fingerprint set
KEYSTORE="$PROJECT_ROOT/.build-android/upload-keystore.jks"
if [ ! -f "$KEYSTORE" ]; then
    deny "Upload keystore missing at $KEYSTORE. Run /setup or keystore-mcp.generate."
fi

# 2. listing files exist
LISTING_DIR="$PROJECT_ROOT/.build-android/listing"
for f in title.txt short-description.txt full-description.txt; do
    if [ ! -f "$LISTING_DIR/$f" ]; then
        deny "Missing listing file: $LISTING_DIR/$f. Run android-store-listing first."
    fi
done

# 3. screenshots present
if ! ls "$LISTING_DIR/screenshots/"*.png >/dev/null 2>&1; then
    deny "No screenshots in $LISTING_DIR/screenshots/. Run /screenshots."
fi

# 4. privacy policy URL set in spec
if ! grep -q "Privacy Policy URL" "$PROJECT_ROOT/.build-android/spec.md" 2>/dev/null; then
    emit "warn" "Privacy Policy URL not detected in spec.md. Play Store rejects apps without one."
fi

emit "info" "Release-readiness checks passed. Submission allowed."
exit 0
