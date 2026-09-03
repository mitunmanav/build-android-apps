#!/usr/bin/env bash
set -euo pipefail
STAGE="$(mktemp -d)/build-android-apps"
mkdir -p "$STAGE"
cp -r skills agents commands hooks ANTIGRAVITY.md .antigravity-plugin "$STAGE/"
agy plugin install "$STAGE"
