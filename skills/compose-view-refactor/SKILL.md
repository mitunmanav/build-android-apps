---
name: compose-view-refactor
description: >
  Refactor a large, monolithic Jetpack Compose composable into smaller, testable,
  state-hoisted pieces. Extract sub-composables, separate stateless from stateful,
  move side effects to the right scope, and reduce parameter count. Use this skill
  when the user asks to "refactor this composable", "split up this screen", "make
  it testable", "this View is 800 lines", or to apply MV separation. Do not use for
  performance-only changes (use compose-performance-audit) or to introduce a new
  design system (use material3-expressive). No MCP server required.
license: Apache-2.0
compatibility: >
  Requires Compose 1.5+. No MCP server required.
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [android, jetpack-compose, refactor, mvvm, hoisting, single-responsibility, state, viewmodel]
  platform: android
  version: 0.1.0
---

# Compose View Refactor

## Prerequisites

- Read access to the file being refactored
- A test (UI test, screenshot test, or manual) that proves current behavior — refactors without tests are rewrites

## Workflow

### Step 1: Capture the baseline

Before touching the file:

1. Run `/build` and verify it compiles.
2. Run any existing UI tests. Record pass/fail.
3. Capture a screenshot of the current screen via `android-emulator-browser`.

If there are no tests, ask the user to confirm they want a refactor without regression coverage — and prefer to write a screenshot test first.

### Step 2: Identify the smells

Read the file end-to-end. Look for:

| Smell | Indicator | Refactor |
|---|---|---|
| God Composable | > 200 lines, > 6 parameters, multiple stateful concerns | Extract sub-composables; split by region |
| Business logic in Composable | `viewModel.something()` called directly from UI; `LaunchedEffect` does I/O | Move to ViewModel or use-case |
| Implicit state | `var counter by remember { mutableStateOf(0) }` inside stateless composable | Hoist to caller or ViewModel |
| Cross-cutting side effects | Multiple `LaunchedEffect` blocks doing unrelated work | Extract to a single `LaunchedEffect(Unit)` with named coroutines, or move to ViewModel |
| Parameter explosion | 6+ parameters, many of same type | Wrap in a data class `ScreenState` or `SectionState` |
| Hardcoded magic numbers | `padding(16.dp)`, `size(48.dp)` | Replace with theme tokens or named constants |
| Nested state | `var a by remember { mutableStateOf(...) }` reads `var b` | Use derived state or a single state object |
| Repeated widget trees | Same 5-line Row pattern copy-pasted 4+ times | Extract `ItemRow(item: Item, ...)` |

### Step 3: Decide the target structure

A well-refactored screen has:

```kotlin
@Composable
fun Screen(
    state: ScreenState,
    onAction: (ScreenAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    // Layout-only — no business logic, no side effects
    Scaffold(...) { padding ->
        Column(modifier = modifier.padding(padding)) {
            Header(state.header)
            Content(state.content, onAction = onAction)
        }
    }
}

@Composable
private fun Header(state: HeaderState) { /* ... */ }

@Composable
private fun Content(state: ContentState, onAction: (ScreenAction) -> Unit) { /* ... */ }
```

State shape:

```kotlin
data class ScreenState(
    val header: HeaderState,
    val content: ContentState,
    val isLoading: Boolean,
    val error: String?,
)

sealed interface ScreenAction {
    data class OnItemClick(val id: String) : ScreenAction
    data object OnRefresh : ScreenAction
}

@Stable
data class HeaderState(val title: String, val subtitle: String?)

@Stable
data class ContentState(val items: ImmutableList<Item>)
```

### Step 4: Extract sub-composables (incremental)

Do one extract at a time, verifying build + test after each:

1. Extract a `private fun` sub-composable for the first region.
2. Hoist its state to the parent (or a shared state object).
3. Move side effects up.
4. Run build. Fix compile errors.
5. Run tests. Confirm green.
6. Capture screenshot. Compare visually.

Repeat for the next region.

### Step 5: Move business logic to ViewModel

If side effects exist:

```kotlin
// BAD
@Composable
fun Screen() {
    val scope = rememberCoroutineScope()
    var items by remember { mutableStateOf(emptyList<Item>()) }
    LaunchedEffect(Unit) {
        items = api.fetchItems()
    }
}

// GOOD
@Composable
fun Screen(viewModel: ScreenViewModel = viewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    ScreenContent(state = state, onAction = viewModel::onAction)
}

class ScreenViewModel : ViewModel() {
    val state: StateFlow<ScreenState> = ...
    fun onAction(action: ScreenAction) { ... }
}
```

### Step 6: Verify

After all extracts:

1. Run all UI tests. Compare to baseline.
2. Run screenshot test if present. Compare.
3. Run `/build` and install on device.
4. Manually exercise the screen.
5. Run `compose-performance-audit` to confirm no regressions in recomposition counts.

### Step 7: Document the change

For any nontrivial refactor, leave a 3-5 line comment at the top of the file:

```kotlin
// Region-based split. State in ScreenState, actions in ScreenAction.
// Side effects owned by ScreenViewModel. Stateless sub-composables are private.
```

## Anti-patterns

- Do NOT refactor without tests. Refactor + behavior change in one PR is unreviewable.
- Do NOT extract sub-composables that take 6+ parameters — wrap state first.
- Do NOT move state into ViewModel for the sake of it. Local `remember` is fine for purely-UI state (e.g. "is this dropdown open").
- Do NOT add `kotlinx.coroutines.flow.combine` to "merge" states that should be one state object.
- Do NOT introduce a Hilt module for a 2-field ViewModel. Use plain ViewModel factory.

## Pairing

- `compose-performance-audit` — after the refactor, audit for stability and recomposition count.
- `compose-ui-patterns` — for the broader idiom set.
- `material3-expressive` — if the refactor surfaces an opportunity to apply design tokens.
