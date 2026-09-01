---
name: compose-ui-patterns
description: >
  Compose UI pattern catalog for everyday Android screens: lists, navigation,
  forms, state hoisting, side effects, theming, accessibility, and interop. Use this
  skill when the user wants to know "what's the right way to do X in Compose", is
  building a screen from scratch, or wants a recommendation between competing
  approaches. Do not use for Material 3 design system choices (use
  material3-expressive) or for performance audits (use compose-performance-audit).
  No MCP server required.
license: Apache-2.0
compatibility: >
  Requires Compose 1.5+ for the patterns covered. Some patterns require Compose 1.7+.
  No MCP server required.
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [android, jetpack-compose, ui, patterns, hoisting, navigation, lazycolumn, state, forms]
  platform: android
  version: 0.1.0
---

# Compose UI Patterns

## Prerequisites

- Compose 1.5+ for the patterns covered
- Some patterns require Compose 1.7+ (e.g. `animateItem`, deferred lambda reads)
- Familiarity with `Composable`, `remember`, `LaunchedEffect`, `StateFlow`

## Workflow

### Step 1: Identify the pattern class

| Class | Patterns |
|---|---|
| Lists | LazyColumn, LazyRow, LazyVerticalGrid, paging, sticky headers |
| Navigation | Navigation3 scenes, deep links, conditional nav, dialogs/sheets |
| Forms | TextField validation, focus management, IME insets, error display |
| State | Hoisting, ViewModel+StateFlow, rememberSaveable, SavedStateHandle |
| Side effects | LaunchedEffect, DisposableEffect, SideEffect, produceState |
| Theming | MaterialTheme, dynamicColor, custom palettes, dark theme |
| Accessibility | semantics, contentDescription, role, focus order, edge-to-edge |
| Interop | Compose in Views (ComposeView), Views in Compose (AndroidView) |

### Step 2: Pick the right pattern

#### Lists

**LazyColumn with stable keys**:

```kotlin
@Composable
fun ItemList(items: List<Item>, onClick: (Item) -> Unit) {
    LazyColumn {
        items(items = items, key = { it.id }) { item ->
            ItemRow(item, onClick = { onClick(item) })
        }
    }
}
```

For paginated lists, use `androidx.paging.compose:paging-compose`:

```kotlin
val items = viewModel.pagedItems.collectAsLazyPagingItems()
LazyColumn {
    items(items.itemCount, key = items.itemKey { it.id }) { i ->
        ItemRow(items[i]!!)
    }
}
```

#### Navigation

Prefer **Navigation3** with scenes (compose 1.7+):

```kotlin
NavHost(navController) {
    sceneComposable<HomeRoute> { HomeScene(onItemClick = { id -> navController.navigate(DetailRoute(id)) }) }
    sceneComposable<DetailRoute> { it -> DetailScene(id = it.id) }
}
```

For dialogs and bottom sheets, use Navigation3 scenes (e.g. `DialogScene`, `BottomSheetScene`).

#### Forms

Validate on submit and as the user fixes errors:

```kotlin
@Composable
fun EmailField(state: FormState, modifier: Modifier = Modifier) {
    OutlinedTextField(
        value = state.email,
        onValueChange = { state.onEmailChange(it) },
        isError = state.emailError != null,
        supportingText = { state.emailError?.let { Text(it) } },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
        modifier = modifier,
    )
}
```

Use `Modifier.imePadding()` on the root to avoid IME overlap. For focus management, use `FocusRequester`:

```kotlin
val focusRequester = remember { FocusRequester() }
LaunchedEffect(Unit) { focusRequester.requestFocus() }
OutlinedTextField(modifier = modifier.focusRequester(focusRequester), ...)
```

#### State hoisting

The hoisting rule:

> Composable should not own state it doesn't display. Hoist state to the lowest common ancestor that needs to observe or modify it.

```kotlin
// Hoisted
@Composable
fun Counter(count: Int, onIncrement: () -> Unit) {
    Button(onClick = onIncrement) { Text("Count: $count") }
}

// Caller owns state
@Composable
fun Screen(viewModel: CounterViewModel = viewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    Counter(count = state.count, onIncrement = viewModel::onIncrement)
}
```

#### Side effects

| Effect | Use for |
|---|---|
| `LaunchedEffect(key)` | One-shot per key change (fetch data, animate to state) |
| `DisposableEffect(key)` | Setup + cleanup (register/unregister listener) |
| `SideEffect` | Publishing Compose state to non-Compose world (logging, analytics) |
| `produceState` | Bridging non-Compose state (Flow, callback) into Compose state |
| `rememberCoroutineScope` | Launching coroutines in response to user actions |

#### Theming

```kotlin
@Composable
fun AppTheme(content: @Composable () -> Unit) {
    val darkTheme = isSystemInDarkTheme()
    val colorScheme = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> dynamicColorScheme(LocalContext.current, darkTheme)
        darkTheme -> darkColorScheme()
        else -> lightColorScheme()
    }
    MaterialTheme(colorScheme = colorScheme, content = content)
}
```

For custom palettes, derive from a brand seed:

```kotlin
val cs = ColorScheme.fromSeed(seedColor = Color(0xFF3DDC84), isDark = isSystemInDarkTheme())
```

#### Accessibility

Every interactive element needs a `contentDescription` or `role`:

```kotlin
IconButton(onClick = onDelete) {
    Icon(Icons.Default.Delete, contentDescription = "Delete item")
}
```

For tests: use `Modifier.testTag("delete-button")`. For screen readers: use `Modifier.semantics { role = Role.Button }`.

For edge-to-edge, see the `edge-to-edge` skill.

#### Interop

**Compose in a View**:

```kotlin
class MyFragment : Fragment() {
    override fun onCreateView(...): View {
        return ComposeView(requireContext()).apply {
            setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
            setContent { MyComposeScreen() }
        }
    }
}
```

**A View in Compose**:

```kotlin
@Composable
fun MapView() {
    AndroidView(
        factory = { ctx -> MapView(ctx).apply { onCreate(null) } },
        update = { it.onResume() },
        onRelease = { it.onPause() },
    )
}
```

### Step 3: Validate accessibility

- Every `Image` has `contentDescription` (or `null` for decorative)
- All interactive elements have `Role.Button` / `Role.Switch` etc. via `Modifier.semantics`
- Touch targets ≥ 48dp
- Color contrast ≥ 4.5:1 for text

### Step 4: Verify on device

Use `android-emulator-browser` skill to drive the UI and capture screenshots.

## Anti-patterns

- Do NOT pass `List<T>` directly as a parameter — it's unstable. Use `ImmutableList<T>` or annotate.
- Do NOT read `State` inside lambdas you don't control — hoist the read.
- Do NOT use `runBlocking` in any Composable. Use `produceState` or a ViewModel.
- Do NOT skip `key` in `items()` — animations break and recompositions leak.
- Do NOT define a `@Composable` that takes 5+ parameters of the same type — wrap in a data class.

## Pairing

- `material3-expressive` — for the design system layer above these patterns.
- `compose-performance-audit` — for ensuring these patterns perform.
- `compose-view-refactor` — when restructuring a screen into smaller pieces.
