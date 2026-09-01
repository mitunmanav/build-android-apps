# Privacy Policy

This plugin (build-android-app-plugin) does not collect, transmit, or share user data.

## What the plugin does

The plugin is a set of skills, slash commands, subagents, and MCP servers that run locally on the developer's machine. It interacts with:

- **Android SDK / adb / Gradle** — local toolchain only; no telemetry.
- **Google Play Developer API** — only when the user explicitly runs `/publish` or `/update`. The user supplies their own service account JSON; the plugin never sees Play Store credentials beyond that one operation.
- **Firebase / Supabase** — only if the user's app uses these as the backend. The plugin generates template code; it does not contact Firebase/Supabase servers on its own.

## What the plugin does NOT do

- No analytics, telemetry, or crash reporting sent to any server we control.
- No collection of keystore passwords, Google account credentials, or device identifiers.
- No tracking of which skills/commands you use.

## Your data stays on your machine

- `state.json` lives at `<project>/.build-android/state.json` and is gitignored.
- The keystore lives at `<project>/.build-android/upload-keystore.jks`.
- The service account JSON lives at `<project>/.build-android/service-account.json`.
- All three are your responsibility to back up. The plugin does not back them up to any server.

## Contact

Open an issue at https://github.com/mitunmanav/build-android-app-plugin/issues for privacy questions.

Last updated: 2026-09-01.
