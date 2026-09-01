#!/usr/bin/env bash
# SessionStart hook for build-android-app-plugin
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

# 4. Connected devices (best-effort)
if [ -n "$ADB" ]; then
    DEVICES=$("$ADB" devices 2>/dev/null | tail -n +2 | grep -v '^$' | head -10 || true)
    if [ -z "$DEVICES" ]; then
        emit "info" "No Android devices/emulators connected. Run 'emulator -avd <name>' or plug in a device with USB debugging enabled"
    else
        COUNT=$(echo "$DEVICES" | wc -l | tr -d ' ')
        emit "info" "$ADB sees $COUNT device(s). First: $(echo "$DEVICES" | head -1)"
    fi
fi

# 5. Plugin reminder
emit "info" "build-android-app-plugin loaded. Try /build, /run, /debug, /device, or /lint. Skills: 9 (debugger, emulator, profiler, leak, app-functions, material3-expressive, compose-perf, compose-patterns, compose-refactor)"

exit 0
