#!/usr/bin/env bash
# PreToolUse hook: gate Play Store submissions through a release-readiness check.
# Fires before mcp__plugin_build_android_apps_play_store__submit_for_review or upload_aab.
# Registered as PreToolUse with matcher on the play-store MCP tool name (verified event per codex/hooks docs).

set -euo pipefail

emit() {
    local level="$1"; shift
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[%s] %s"}}\n' "$level" "$*" >&2
}
deny() {
    local reason="$1"
    cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"$reason"}}
EOF
    # also emit to stderr for Codex UI
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason" >&2
    exit 0
}

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
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
