---
name: android-app-functions
description: >
  Expose Android app functionality through the AppFunctions API (Android 16+) and the
  legacy App Shortcuts / App Intents framework. Create system-level entry points for
  AI agents, voice assistants, and the system shortcut UI. Use this skill when the
  user asks to "expose this to Assistant", "add an App Shortcut", "let the agent trigger
  this action", or wants system-wide surfaces for app capabilities. Do not use for
  in-app deep links (use Navigation3 patterns) or for FCM push actions. Requires no
  MCP server — pure code authoring.
license: Apache-2.0
compatibility: >
  Requires Android API 33+ (App Shortcuts) or API 36+ for AppFunctions preview. The
  legacy App Intents framework is supported on API 22+. No MCP server required.
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [android, app-functions, app-intents, app-shortcuts, assistant, agent, system-surface]
  platform: android
  version: 0.1.0
---

# Android App Functions (AppFunctions API + App Shortcuts)

## Prerequisites

- App targets the appropriate API level for the surface:
  - AppFunctions: Android 16 (API 36) preview, requires opt-in flag
  - App Shortcuts: API 25+
  - App Intents (legacy): API 22+ baseline, full feature set on API 31+
- For AppFunctions: declare `<uses-permission android:name="android.permission.appfunctions.RUN_APP_FUNCTIONS" />` if needed for cross-app invocation
- The action's underlying operation should be idempotent or safely re-runnable — AI agents may invoke it multiple times

## Choose the right surface

| Surface | Use when | Visibility |
|---|---|---|
| **AppFunctions** (Android 16+) | Expose to other apps, system agents, Gemini | Cross-app, requires `<appfunctions>` manifest entry |
| **App Shortcuts** | Static launcher shortcuts, long-press app icon | Launcher only |
| **App Intents** | Legacy Siri-style voice actions, Assistant | System-wide, deprecated in favor of AppFunctions |
| **In-app deeplink** | Direct app-internal navigation | App-internal only |

Default to **AppFunctions** for new work targeting Android 16+. Default to **App Shortcuts** for launcher integration. Use App Intents only for legacy compatibility.

## Workflow

### Step 1: Identify the capability

Ask the user (or extract from the codebase) what user-visible capability they want to expose. Good candidates:

- "Send a message to <contact>"
- "Create a note with title X"
- "Play <playlist>"
- "Add <item> to cart"

A capability must be:

- Idempotent or safely re-runnable
- Parameterizable (inputs are simple types or supported entities)
- Visible to the user (not a hidden admin action)

### Step 2: AppFunctions (Android 16+)

Create an `@AppFunction` annotated function:

```kotlin
@AndroidEntryPoint
class SendMessageFunction {
    @AppFunction(name = "sendMessage")
    suspend fun sendMessage(
        @AppFunctionParameter(description = "Recipient name") recipient: String,
        @AppFunctionParameter(description = "Message body") body: String,
    ): String {
        // Validate, then perform the action
        return "Sent to $recipient"
    }
}
```

Register in the manifest:

```xml
<service
    android:name="androidx.appfunctions.service.AppFunctionService"
    android:exported="true"
    android:permission="android.permission.BIND_APP_FUNCTION_SERVICE">
    <intent-filter>
        <action android:name="android.app.appfunctions.AppFunctionService" />
    </intent-filter>
</service>
```

Add the runtime dependency:

```kotlin
// build.gradle.kts (module level)
dependencies {
    implementation("androidx.appfunctions:appfunctions:1.0.0-alpha01")
}
```

### Step 3: App Shortcuts (still required for launcher)

Even with AppFunctions, launcher shortcuts remain useful. Define static shortcuts in `res/xml/shortcuts.xml`:

```xml
<shortcuts xmlns:android="http://schemas.android.com/apk/res/android">
    <shortcut
        android:shortcutId="new_message"
        android:enabled="true"
        android:icon="@drawable/ic_shortcut_message"
        android:shortcutShortLabel="@string/shortcut_new_message_short"
        android:shortcutLongLabel="@string/shortcut_new_message_long">
        <intent
            android:action="android.intent.action.VIEW"
            android:targetPackage="<package>"
            android:targetClass="<activity>" />
        <categories android:name="android.shortcut.conversation" />
    </shortcut>
</shortcuts>
```

Reference from manifest:

```xml
<activity android:name=".MainActivity">
    <meta-data
        android:name="android.app.shortcuts"
        android:resource="@xml/shortcuts" />
</activity>
```

For dynamic shortcuts (created at runtime, e.g. pinned contacts):

```kotlin
val shortcut = ShortcutInfo.Builder(context, "msg_alice")
    .setShortLabel("Message Alice")
    .setLongLabel("Send Alice a quick message")
    .setIntent(Intent(/* deeplink to message composer with prefilled recipient */))
    .build()
ShortcutManagerCompat.pushDynamicShortcut(context, shortcut)
```

### Step 4: Validate the surface

After building:

1. Run `/build` to assemble.
2. Install on a device.
3. For AppFunctions: `adb shell cmd appfunctions list` should show your function.
4. For App Shortcuts: long-press the app icon to see static shortcuts appear.
5. For dynamic shortcuts: verify they appear in `ShortcutManager.getDynamicShortcuts()`.

### Step 5: Document for the agent

When the agent needs to invoke these capabilities, expose them through the plugin's slash commands (e.g. add a `/message` command that calls the same intent), or document the AppFunction name in the skill body so other skills can reference it.

## Anti-patterns

- Do NOT expose a destructive action (delete, send money, overwrite) through AppFunctions without confirmation parameters.
- Do NOT leak the user's data through function return values — return only the minimal success/error result.
- Do NOT register more than ~10 dynamic shortcuts — Android caps them and may drop silently.
- Do NOT use App Intents for new work targeting Android 16+ — prefer AppFunctions.
- Do NOT forget the `BIND_APP_FUNCTION_SERVICE` permission on the service declaration — the manifest entry silently no-ops without it.

## Pairing

- `material3-expressive` — for the shortcut icon design.
- `compose-ui-patterns` — when the capability opens a Compose UI, follow the surface preview pattern.
- `android-debugger-agent` — for testing the invocation end-to-end.
