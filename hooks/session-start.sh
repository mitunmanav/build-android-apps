#!/usr/bin/env bash
# SessionStart hook for build-android-apps
# Detects Android SDK, adb, and connected devices. Warns if missing.

set -u

emit() {
    local level="$1"; shift
    printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[%s] %s"}}\n' "$level" "$*" >&2
}

# 1. ANDROID_HOME
if [ -z "${ANDROID_HOME:-}" ]; then
    emit "warning" "ANDROID_HOME is not set. adb / build-tools / emulator will not resolve. Set it to your Android SDK root, e.g. ~/Android/Sdk"
elif [ ! -d "$ANDROID_HOME" ]; then
    emit "warning" "ANDROID_HOME=$ANDROID_HOME does not exist as a directory"
fi

# 2. adb on PATH (or via ANDROID_HOME)
ADB=""
if [ -n "${ANDROID_HOME:-}" ] && [ -x "$ANDROID_HOME/platform-tools/adb" ]; then
    ADB="$ANDROID_HOME/platform-tools/adb"
elif command -v adb >/dev/null 2>&1; then
    ADB="$(command -v adb)"
else
    emit "warning" "adb not found. Install via Android SDK platform-tools or 'brew install android-platform-tools'"
fi

# 3. java + JAVA_HOME
if [ -z "${JAVA_HOME:-}" ]; then
    emit "warning" "JAVA_HOME is not set. Gradle builds may fail or pick the wrong JDK"
elif [ ! -x "$JAVA_HOME/bin/java" ]; then
    emit "warning" "JAVA_HOME=$JAVA_HOME but $JAVA_HOME/bin/java is not executable"
fi

# 4. Connected devices (best-effort, 5s cache for efficiency)
if [ -n "$ADB" ]; then
    CACHE="/tmp/build-android-apps-adb-cache.json"
    NOW=$(date +%s)
    USE_CACHE=false
    if [ -f "$CACHE" ]; then
        AGE=$((NOW - $(stat -c %Y "$CACHE" 2>/dev/null || stat -f %m "$CACHE" 2>/dev/null || echo 0)))
        if [ "$AGE" -lt 5 ]; then USE_CACHE=true; fi
    fi
    if [ "$USE_CACHE" = true ]; then
        DEVICES=$(cat "$CACHE")
    else
        DEVICES=$("$ADB" devices 2>/dev/null | tail -n +2 | grep -v '^$' | head -10 || true)
        printf '%s' "$DEVICES" > "$CACHE" 2>/dev/null || true
    fi
    if [ -z "$DEVICES" ]; then
        emit "info" "No Android devices/emulators connected. Run 'emulator -avd <name>' or plug in a device with USB debugging enabled"
    else
        COUNT=$(echo "$DEVICES" | wc -l | tr -d ' ')
        emit "info" "$ADB sees $COUNT device(s). First: $(echo "$DEVICES" | head -1)"
    fi
fi

# 5. Plugin reminder — frontdoor is $build-android-apps; 27 specialists lazy-loaded
emit "info" "build-android-apps loaded. Frontdoor: \$build-android-apps (one skill routes to 27 specialists). Try /build, /run, /debug, /device, /lint. Progressive disclosure: only frontdoor description at startup, specialists load on demand."

# 6. Per-project state.json (Phase 1: load + report)
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_DIR="$PROJECT_ROOT/.build-android"
STATE_FILE="$STATE_DIR/state.json"

PLUGIN_ROOT="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"

if [ -f "$PLUGIN_ROOT/state/__init__.py" ] && command -v python3 >/dev/null 2>&1; then
    STATE_JSON="$(PYTHONPATH="$PLUGIN_ROOT" python3 -m state load "$STATE_FILE" 2>/dev/null || true)"
    if [ -n "$STATE_JSON" ]; then
        PHASE="$(printf '%s' "$STATE_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("phase","idle"))' 2>/dev/null || echo idle)"
        CURSOR_TID="$(printf '%s' "$STATE_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("cursor",{}).get("task_id",""))' 2>/dev/null || echo "")"
        emit "info" "state.json: phase=$PHASE cursor.task_id=$CURSOR_TID"
    else
        emit "info" "no per-project state.json yet. Run /make-app to bootstrap."
    fi
else
    emit "info" "no per-project state.json yet. Run /make-app to bootstrap."
fi

exit 0
