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
| "expose search via Assistant" | app-functions | `android-app-functions` | surfaces wired |
| "tap through onboarding and show me" | drive | `android-emulator-browser` | device driven |
| "what's the right way to do lists?" | pattern | `compose-ui-patterns` | pattern applied |
| "make it expressive with motion" | expressive | `material3-expressive` | theme wired |
| "why is this recomposing so much?" | recompose | `compose-performance-audit` | perf report |
| "split this 800-line screen" | refactor | `compose-view-refactor` | refactored |
| "attach debugger at breakpoint" | JDWP | `android-debugger-agent` | debug session |
| "sequence the approved spec" | plan | `app-planner` | plan sequenced |
| "run lint and tests" | lint/test | `gradlew-mcp run_lint` / `run_tests` | reports |
| "audit ship gaps" | audit | `/audit` | gaps listed |
| "clean slop from this file" | slop | `/slop` | slop clean |
| "show logcat for tag X" | log | `adb-mcp logcat_dump` | logs shown |
| "which devices are connected?" | device | `adb-mcp list_devices` | device selected |
| "capture Play screenshots" | screenshots | `android-icons-assets` | screenshots |
| "draft privacy policy" | privacy | `android-store-listing` | policy drafted |
| "back up the keystore" | backup | `keystore-mcp backup` | keystore safe |
| "how are downloads doing?" | status | `/status` | dashboard |
| "finish and submit internal" | finish | `/finish` | Play draft |
