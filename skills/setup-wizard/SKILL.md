---
name: setup-wizard
description: >
  First-run setup wizard for build-android-app-plugin. Detects missing
  prerequisites (JDK, Android SDK, adb, AVD), walks the user through Google
  Play Console signup and service-account setup, generates an upload keystore.
  Idempotent: skips steps that already pass. Use this only on first run, or
  when the user explicitly says /setup. Do not use to refresh credentials or
  to add new devices — those have their own flows.
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [setup, onboarding, cold-start, sdk, jdk, avd, keystore, service-account]
---

# Setup Wizard

> [!NOTE]
> 10 steps, ~30 minutes total. Each step shows a progress bar and one sentence.

## Prerequisites

- A POSIX shell (bash/zsh) or PowerShell 7+
- Internet access for downloads + Google API calls
- ~2 GB free disk space for Android SDK

## Workflow

### Step 1: Detect OS

Use `uname -a` (POSIX) or `$env:OS` (Windows). Pick install instructions accordingly.

### Step 2: JDK

Check `java -version` for >=17. If missing or older:

- **macOS**: `brew install openjdk@17`
- **Linux**: `sudo apt install openjdk-17-jdk` or use `sdkman`
- **Windows**: `winget install Microsoft.OpenJDK.17`

Set `JAVA_HOME` and add `$JAVA_HOME/bin` to PATH. Verify with `java -version`.

### Step 3: Android SDK

Check `$ANDROID_HOME` or `$ANDROID_SDK_ROOT`.

If missing:
1. Download `commandlinetools-mac/latest` (or `-linux`, `-win`) from `https://developer.android.com/studio`.
2. Extract to `~/Android/sdk/cmdline-tools/latest/`.
3. Set `ANDROID_HOME=~/Android/sdk`.
4. Add `$ANDROID_HOME/platform-tools` and `$ANDROID_HOME/cmdline-tools/latest/bin` to PATH.

### Step 4: SDK packages

Use `mcp__plugin_build_android_app_plugin_gradlew__manage_sdk` with:

```
args: { "action": "install", "packages": ["platform-tools", "platforms;android-35", "build-tools;35.0.0"] }
```

### Step 5: adb

Confirm `adb version` returns. If not, restart shell or re-check PATH.

### Step 6: Device or emulator

Run `adb devices`. If empty, offer to create an AVD:

```
$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager create avd -n Pixel_API_34 -k "system-images;android-34;google_apis;x86_64" -d pixel_6
```

Then start it: `emulator -avd Pixel_API_34 &`.

### Step 7: Play Console account

Walk the user through:

1. Visit https://play.google.com/console and pay the $25 fee.
2. Complete the account identity verification (requires government ID).
3. Set up a developer profile (name + email visible on the store listing).

> The $25 fee is paid once per Google account. You cannot get it back if you delete the account.

### Step 8: Google Cloud project + service account

1. Visit https://console.cloud.google.com/ → create project (e.g. "play-publisher-<your-app>").
2. Enable **Google Play Android Developer API**.
3. IAM & Admin → Service Accounts → Create service account (name: "play-publisher").
4. Grant role: **Service Account User**.
5. Done → click the service account → Keys → Add Key → Create new → JSON.
6. Download and save to `<project>/.build-android/service-account.json`.
7. In Play Console → Setup → API access → link the Cloud project → grant the service account **Release manager** + **Store listing editor** permissions.

### Step 9: Verify API access

Use `mcp__plugin_build_android_app_plugin_play_store__auth` (when Phase 13 lands) or run a quick check via curl:

```bash
curl -H "Authorization: Bearer $(cat .build-android/sa-token.json | jq -r .access_token)" \
  https://androidpublisher.googleapis.com/androidpublisher/v3/applications
```

If the call returns 200, the API is wired. If 403, the role in Play Console wasn't granted correctly.

### Step 10: Upload keystore

Generate the upload keystore:

```
tool: mcp__plugin_build_android_app_plugin_gradlew__generate_keystore
args: { "password": "<from user>", "key_password": "<from user>" }
```

Save the password to a password manager and copy the keystore to:
- Google Drive (or other cloud)
- USB drive
- Anywhere outside this laptop

If you lose the keystore, you cannot update the app on Play Store. Ever.

## Anti-patterns

- **DO NOT** skip the keystore backup. Users who lose their keystore must publish a new app under a new package name and lose all reviews/ratings.
- **DO NOT** share the service account JSON file in chat. Treat it as a secret.
- **DO NOT** skip the Google identity verification step — Play Console requires it before any app can be published.
- **DO NOT** ask the user to grant the service account "Owner" — "Release manager" + "Store listing editor" is the minimum.

## Pairing

- `/setup` slash command — sole entry point
- `keystore-mcp.generate_keystore` — for Step 10 (Phase 13)
- `play-store-mcp.auth` — for Step 9 (Phase 13)

## References

- See [references/platform-notes.md](references/platform-notes.md) for
  per-OS install commands and known issues.
