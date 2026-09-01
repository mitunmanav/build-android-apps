# Edge-to-edge: right vs wrong (android-edge-to-edge)

8 pairs of common edge-to-edge mistakes. Adopt the Right; reject the Wrong.

## Pair 1: enableEdgeToEdge()

**Right**:
```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    enableEdgeToEdge()
    super.onCreate(savedInstanceState)
    setContent { ... }
}
```

**Wrong**:
```kotlin
WindowCompat.setDecorFitsSystemWindows(window, false)  // missing enableEdgeToEdge
super.onCreate(savedInstanceState)
setContent { ... }
```

## Pair 2: Scaffold with bars

**Right**:
```kotlin
Scaffold(topBar = { TopAppBar(...) }, bottomBar = { NavigationBar(...) }) { padding ->
    LazyColumn(contentPadding = padding) { /* items */ }
}
```

**Wrong**:
```kotlin
Column {
    TopAppBar(...)
    LazyColumn(modifier = Modifier.weight(1f).padding(WindowInsets.systemBars.asPaddingValues())) { /* ... */ }
    NavigationBar(...)
}
```

The Wrong version reimplements what Scaffold does for free.

## Pair 3: status bar icon contrast

**Right** (per-screen, recomposes with theme):
```kotlin
val view = LocalView.current
SideEffect {
    val window = (view.context as Activity).window
    WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !isDarkTheme
}
```

**Wrong** (manifest-only):
```xml
<item name="android:windowLightStatusBar">true</item>
```

## Pair 4: IME padding

**Right** (let Scaffold handle it):
```kotlin
Scaffold(bottomBar = { TextField(...) }) { padding -> ... }
```

**Wrong** (manual imePadding in addition):
```kotlin
Column(modifier = Modifier.imePadding()) { ... }
```

## Pair 5: full-screen dialogs

**Right**:
```kotlin
Dialog(onDismissRequest = ..., properties = DialogProperties(usePlatformDefaultWidth = false)) { ... }
```

**Wrong**:
```kotlin
Dialog(...) { Column(modifier = Modifier.fillMaxSize()) { ... } }
```

## Pair 6: nav-bar gesture handling

**Right** (let Compose handle via Scaffold):
```kotlin
Scaffold { padding -> ... }  // nav-bar inset baked in
```

**Wrong** (overlay a Box on top):
```kotlin
Box(modifier = Modifier.fillMaxSize()) {
    Content()
    Spacer(modifier = Modifier.windowInsetsBottomHeight(WindowInsets.navigationBars))
}
```

## Pair 7: large-screen / foldable

**Right** (use WindowSizeClass):
```kotlin
val windowSizeClass = calculateWindowSizeClass(activity)
when (windowSizeClass.widthSizeClass) {
    WindowWidthSizeClass.Compact -> { /* single-pane */ }
    else -> { /* two-pane */ }
}
```

**Wrong** (hardcoded breakpoint):
```kotlin
if (LocalConfiguration.current.screenWidthDp > 600) { /* ... */ }
```

## Pair 8: testing

**Right** (screenshot test across screen sizes):
```kotlin
@Test fun home_compact() = takeScreenshot("Home", config = 400.dp x 800.dp)
@Test fun home_medium() = takeScreenshot("Home", config = 610.dp x 800.dp)
@Test fun home_expanded() = takeScreenshot("Home", config = 900.dp x 1000.dp)
```

**Wrong** (only test on emulator):
```kotlin
@Test fun home() = takeScreenshot("Home")  // single device
```
