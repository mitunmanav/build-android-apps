#!/usr/bin/env bash
# PreSubmit hook: gate Play Store submissions through a release-readiness check.
# Fires before mcp__plugin_*_play_store__submit_for_review or upload_aab.

set -euo pipefail

emit() {
    local level="$1"; shift
    printf '{"hookSpecificOutput":{"hookEventName":"PreSubmit","additionalContext":"[%s] %s"}}\n' "$level" "$*" >&2
}

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_FILE="$PROJECT_ROOT/.build-android/state.json"

if [ ! -f "$STATE_FILE" ]; then
    emit "deny" "No state.json. Run /make-app first."
    exit 2
fi

# 1. keystore exists + fingerprint set
KEYSTORE="$PROJECT_ROOT/.build-android/upload-keystore.jks"
if [ ! -f "$KEYSTORE" ]; then
    emit "deny" "Upload keystore missing at $KEYSTORE. Run /setup or keystore-mcp.generate."
    exit 2
fi

# 2. listing files exist
LISTING_DIR="$PROJECT_ROOT/.build-android/listing"
for f in title.txt short-description.txt full-description.txt; do
    if [ ! -f "$LISTING_DIR/$f" ]; then
        emit "deny" "Missing listing file: $LISTING_DIR/$f. Run android-store-listing first."
        exit 2
    fi
done

# 3. screenshots present
if ! ls "$LISTING_DIR/screenshots/"*.png >/dev/null 2>&1; then
    emit "deny" "No screenshots in $LISTING_DIR/screenshots/. Run /screenshots."
    exit 2
fi

# 4. privacy policy URL set in spec
if ! grep -q "Privacy Policy URL" "$PROJECT_ROOT/.build-android/spec.md" 2>/dev/null; then
    emit "warn" "Privacy Policy URL not detected in spec.md. Play Store rejects apps without one."
fi

emit "info" "Release-readiness checks passed. Submission allowed."
exit 0
