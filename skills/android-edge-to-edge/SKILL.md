---
name: android-edge-to-edge
description: >
  Migrate an Android app to edge-to-edge layout (status + nav bars transparent,
  content draws under them). Mandatory for SDK 35+. Use this when targeting
  Android 15+ or when the user asks to "draw under the status bar". Do not use
  for non-SDK-35 apps, or for theming (use material3-expressive).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [edge-to-edge, status-bar, navigation-bar, insets, sdk-35]
---

# Android Edge-to-Edge

> [!NOTE]
> Mandatory for SDK 35+. Adopt the Right patterns; reject the Wrong ones.

## Prerequisites

- An app targeting SDK 35+
- `androidx.activity:activity-compose:1.9.0+`

## Workflow

### Step 1: Enable edge-to-edge in MainActivity

**Right**:
```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()  // call BEFORE setContent
        super.onCreate(savedInstanceState)
        setContent { AppTheme { HomeScreen() } }
    }
}
```

**Wrong**:
```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)  // missing enableEdgeToEdge()
        setContent { ... }
    }
}
```

`enableEdgeToEdge()` is the canonical helper. It handles both status and nav bars, including default contrast.

### Step 2: Apply insets in Compose

**Right** (use Scaffold + WindowInsets):
```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen() {
    Scaffold(
        topBar = { TopAppBar(title = { Text("Home") }) },
        bottomBar = { NavigationBar { /* items */ } },
    ) { padding ->
        LazyColumn(contentPadding = padding) { /* items */ }
    }
}
```

Scaffold applies `WindowInsets.systemBars` to the bars, and `padding` includes the inset of both bars + content.

**Wrong** (hardcoded paddings):
```kotlin
LazyColumn(modifier = Modifier.padding(top = 24.dp, bottom = 48.dp)) { /* ... */ }
```

This breaks on devices with notches, gesture nav, or different screen ratios.

### Step 3: Make status bar icons legible

For light backgrounds, you want dark icons. For dark backgrounds, light icons.

**Right** (per-screen):
```kotlin
Scaffold { padding ->
    val view = LocalView.current
    SideEffect {
        val window = (view.context as Activity).window
        WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !isDarkTheme
    }
    /* content */
}
```

**Wrong** (manifest theme attribute that you can't override per-screen):
```xml
<item name="android:windowLightStatusBar">true</item>  <!-- applies globally -->
```

### Step 4: IME insets

For screens with a `TextField` near the bottom (chat, search):

**Right**:
```kotlin
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen() {
    Scaffold(
        bottomBar = { TextField(...) },
    ) { padding ->
        // `padding` includes IME insets automatically
        LazyColumn(contentPadding = padding) { /* messages */ }
    }
}
```

**Wrong** (manual `imePadding`):
```kotlin
LazyColumn(modifier = Modifier.padding(WindowInsets.ime.asPaddingValues())) { /* ... */ }
```

`imePadding()` works but is redundant when Scaffold already handles it.

### Step 5: Test on multiple devices

Use the `compose-ui-patterns` skill + `adb-mcp.screencap` to verify on:
- Pixel 6 (standard)
- Pixel 8 Pro (with notch)
- Samsung S24 (with curved edges)

## Anti-patterns

- **DO NOT** use `Modifier.statusBarsPadding()` everywhere. It breaks layout assumptions.
- **DO NOT** set `android:fitsSystemWindows="true"` in XML. Compose-only.
- **DO NOT** ship an SDK 35 app without `enableEdgeToEdge()`. Play Store will reject.

## Pairing

- `android-ui-patterns` — for general Scaffold + TopAppBar usage
- `material3-expressive` — for theming choices

## References

- See [references/right-wrong-pairs.md](references/right-wrong-pairs.md)
  for 8 pairs of common edge-to-edge mistakes and the correct fix.
