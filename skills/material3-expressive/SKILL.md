---
name: material3-expressive
description: >
  Apply Material 3 Expressive design system to Android Compose UI. Use shape
  morphing, motion choreography, expressive color tokens, and the new component
  patterns (FABs, buttons, lists, sheets). Use this skill when the user asks for
  "expressive UI", "Material 3 Expressive", "morph the corner radius", "add
  motion", "shape morph", or wants their Compose UI to follow current Material
  design. Do not use for structural refactors (use compose-view-refactor) or for
  recomposition performance (use compose-performance-audit). No MCP server required.
license: Apache-2.0
compatibility: >
  Requires Compose BOM 2024.10.00+ (Material 3 1.3+). For animation: Compose 1.7+.
  No MCP server required.
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [android, jetpack-compose, material3, material-design, motion, shape, expressive, m3]
  platform: android
  version: 0.1.0
---

# Material 3 Expressive

## Prerequisites

- Compose BOM 2024.10.00 or newer (Material 3 1.3+)
- `androidx.compose.material3:material3` and `material3-window-size-class`
- For motion choreography: Compose 1.7+ (`animate*AsState`, `Animatable`)
- Familiarity with Material 3 color tokens (`primary`, `surface`, `onSurface`, etc.)

## Workflow

### Step 1: Identify the expressive opportunity

Material 3 Expressive is about *deliberate emotion*, not decoration. Ask:

- Is this UI moment about feedback, delight, or guidance? → motion
- Does the surface change role across states (collapsed → expanded)? → shape morph
- Is the brand color the emotional anchor? → color tokens + tonal palette
- Is the interaction a long-press, drag, or hover preview? → scale + spring physics

If the answer is "none", skip Expressive and use plain Material 3. Expressive without intent is noise.

### Step 2: Apply the right element

#### Shape morphing

Use `Shape` with `RoundedCornerShape` that animates between corner radii:

```kotlin
val shape by animateDpAsState(
    targetValue = if (expanded) 28.dp else 12.dp,
    animationSpec = tween(durationMillis = 400, easing = FastOutSlowInEasing),
    label = "card-shape"
)
Card(shape = RoundedCornerShape(shape)) { ... }
```

Use it on:

- Cards that expand into sheets
- FABs that morph into toolbars
- Bottom navigation transitioning to expanded dock

#### Motion choreography

For multi-element orchestration, use `AnimatedVisibility` with `EnterTransition` chains:

```kotlin
AnimatedVisibility(
    visible = showDetails,
    enter = fadeIn(tween(300)) + slideInVertically(tween(400)) { it / 2 },
    exit = fadeOut(tween(200)) + slideOutVertically(tween(300)) { it / 2 },
) {
    DetailContent()
}
```

For staggered lists, use `LazyColumn` with `Modifier.animateItemPlacement`:

```kotlin
LazyColumn {
    items(items, key = { it.id }) { item ->
        Row(modifier = Modifier.animateItemPlacement(tween(300))) {
            Text(item.label)
        }
    }
}
```

#### Color tokens

Use Material 3's tonal palette, not raw hex:

```kotlin
MaterialTheme(
    colorScheme = dynamicColorScheme(LocalContext.current)  // Material You
        ?: lightColorScheme()  // fallback
) { ... }
```

For brand color overrides, derive from a single seed:

```kotlin
val cs = ColorScheme.fromSeed(
    seedColor = BrandSeed,
    isDark = isSystemInDarkTheme()
)
```

Avoid:

- Hardcoded `Color(0xFF...)` in screens
- Mixing `colorScheme.primary` and a custom brand `Color` in the same component

#### Component patterns

| Component | Material 3 Expressive guidance |
|---|---|
| FAB | Use `ExtendedFloatingActionButton` for prominent actions. Morph between `SmallFloatingActionButton` and full FAB on scroll. |
| Button | `Filled`, `Tonal`, `Outlined`, `Text`, `Elevated` — pick by hierarchy. Default `Text` is rarely right. |
| List | `LazyColumn` with `key` for stable identities. Animate insertion/removal. |
| Sheet | `ModalBottomSheet` with `rememberModalBottomSheetState(skipPartiallyExpanded = true)` for committed flows. |
| TopAppBar | `TopAppBar` + `BottomAppBar` pair. Animate elevation on scroll. |

### Step 3: Validate accessibility

Expressive UI must remain accessible:

- All motion respects `LocalConfiguration.current.animatorDurationScale`. If `0`, motion should still convey state changes (instant shape snap is OK; silently appearing content is not).
- Color contrast meets WCAG 2.1 AA — use `Color.primary` on `Color.surface` and validate with `Color.contrastAgainst`.
- Touch targets ≥ 48dp regardless of shape.
- No essential content conveyed by motion alone — provide a non-motion equivalent.

### Step 4: Verify on device

Material 3 Expressive relies on visual feedback. Always verify:

1. Run `/build` to install.
2. Use `android-emulator-browser` skill to capture the screen.
3. Trigger the state change (tap, scroll).
4. Capture again. Compare visually.

If the motion feels janky or off-beat, switch to `compose-performance-audit`.

## Anti-patterns

- Do NOT animate everything. Static UI with one well-placed motion reads as intentional; busy UI reads as anxious.
- Do NOT use `tween(1000)` for micro-interactions — anything > 300ms feels broken.
- Do NOT override `colorScheme` to inject brand colors without testing all 30+ roles.
- Do NOT skip the contrast check on tonal variants — `surfaceContainer` can fail contrast against `onSurface` in some palettes.
- Do NOT use `Modifier.graphicsLayer { translationY = ... }` for entrance animations — use `AnimatedVisibility` so skipped frames can be optimized.

## Pairing

- `compose-ui-patterns` — for the broader Compose idiom set beyond Material 3.
- `compose-performance-audit` — when motion triggers recomposition storms.
- `material3-expressive` should be invoked alongside new screen creation, not retroactively.
