# Examples — utterance → routing

| User utterance | Intent | Specialist | State before/after |
|---|---|---|---|
| "make a habit tracker with streaks" | make-app | `app-intake` → writes `.build-android/spec.md` | idle → plan |
| "add dark mode after the home screen" | add | `state add --title "Dark mode" --phase build --deps <home-id>` | plan mutated, re-routed via Kahn |
| "where are we?" | where | `state where` (no specialist) | read-only |
| "build it" | build | `gradlew-mcp run_task assembleDebug` | build |
| "preview on my phone" | preview | `android-run` | device screenshot |
| "it crashes on launch, here's logcat" | debug | `android-debug-fix` | fix loop, 3 strikes |
| "it's slow when scrolling" | perf | `android-profiler` then `compose-performance-audit` | trace → stability report |
| "add Google sign-in" | auth | `android-auth` (Credential Manager) | auth wired |
| "I need to ship to Play Store" | publish | `android-store-listing` → `android-publish-update` (gated) | Play draft |
| "why was it rejected?" | why-rejected | `release-auditor` + `apk-inspector` | diagnosis + fix |
