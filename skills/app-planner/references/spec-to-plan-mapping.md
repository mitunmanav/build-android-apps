# Spec → Plan mapping

Used by `app-planner` to translate a 9-field spec into plan items.

## Default template (12 items)

1. scaffold — "Set up the project (Gradle + Compose + signing)"
2. build — "Add app icon + launcher entry" (deps: 1)
3. build — "Add first screen: <core action>" (deps: 1)
4. build — "Add navigation between screens" (deps: 1, 3)
5. build — "Set up data layer: <backend>" (deps: 1)
6. build — "Add sign-in flow: <accounts>" (deps: 1, 5)
7. build — "Add push notifications" (deps: 1)
8. build — "Add media support: <media>" (deps: 1, 3)
9. build — "Add payment support: <payment>" (deps: 1)
10. test — "Generate screenshots for all screens" (deps: 3, 4)
11. publish — "Write store listing (title/desc/short/long/screenshots)" (deps: 10)
12. publish — "Submit to internal test track" (deps: 1-10)

## Drop rules

For each spec field, drop the corresponding item if the user answered "No" / "None" / "Free" / "On-device only":

| Spec field | "drop" answer | Item to drop |
|---|---|---|
| accounts | "No accounts" | #6 |
| backend | "On-device only" | #5 (still keep #4 if accounts present) |
| payment | "Free" | #9 |
| notifications | "No" | #7 |
| media | "None" | #8 |

After dropping, renumber so deps stay consistent. If dropping creates a gap, the deps still reference the original item id, so re-check the routed plan.

## "You pick" defaults applied upstream

By the time the spec reaches `app-planner`, the user has either answered each field or selected "you pick". The defaults are baked into the spec, so `app-planner` doesn't need to know about them.
