# Routing Table — frontdoor intent → specialist

State-aware. Match longest keyword first. If no match, ask user to clarify.

| # | User says (keywords, case-insensitive) | Current phase | Specialist to load | Next state |
|---|----------------------------------------|---------------|--------------------|-----------|
| 1 | `make an app`, `create an app`, `new app`, idea in quotes | idle / no state.json | `app-intake` → `app-planner` → `android-scaffold` | plan → scaffold→build |
| 2 | `add`, `add a feature`, `add screen` | any | `python -m state add --title ... --phase ...` + Kahn re-route (`state router`) | plan mutated |
| 3 | `change`, `modify`, `update this` | any | `python -m state change --task ...` | plan mutated |
| 4 | `remove`, `delete`, `drop` | any | `python -m state remove --task ...` | plan mutated |
| 5 | `where`, `where are we`, `status` | any | `python -m state where` (no specialist) | read-only |
| 6 | `continue`, `go`, `next` | any with pending | `python -m state continue` → next specialist via router | advances cursor |
| 7 | `undo` | any | `python -m state undo` | history replay |
| 8 | `build`, `assemble`, `compile` | scaffold/build | `gradlew-mcp run_task assembleDebug` (no specialist skill needed, or `android-run` if install) | build |
| 9 | `run`, `preview`, `install`, `launch`, `see it` | build/test | `android-run` (adb-mcp) | device |
| 10 | `debug`, `crash`, `exception`, `logcat`, `why is this crashing` | any with device | `android-debug-fix` (+ `android-debugger-agent` if JDWP) | fix loop |
| 11 | `jank`, `slow`, `profile`, `trace`, `perf` | any | `android-profiler` → `compose-performance-audit` | perf |
| 12 | `leak`, `memory`, `OOM`, `heap` | any | `android-leak-analyzer` | leak triage |
| 13 | `auth`, `sign in`, `login`, `Google sign-in`, `passkey` | build | `android-auth` | auth wired |
| 14 | `backend`, `database`, `Room`, `DataStore`, `Supabase`, `Firebase` | build | `android-backend` | data layer |
| 15 | `push`, `FCM`, `analytics`, `WorkManager`, `Crashlytics` | build | `android-ops` | ops wired |
| 16 | `camera`, `video`, `media`, `ExoPlayer` | build | `android-media` | media wired |
| 17 | `restore`, `multi-device`, `across devices` | build | `android-restore-credentials` | restore keys |
| 18 | `verify email`, `passwordless`, `magic link`, `SD-JWT` | build | `android-verified-email` | verified email |
| 19 | `edge-to-edge`, `status bar`, `insets`, `SDK 35` | build | `android-edge-to-edge` | edge wired |
| 20 | `icon`, `adaptive`, `feature graphic`, `screenshots` | any | `android-icons-assets` (asset-mcp) | assets |
| 21 | `listing`, `store listing`, `privacy`, `data safety` | publish | `android-store-listing` | listing |
| 22 | `publish`, `ship`, `upload to Play`, `internal track` | publish | `android-store-listing` → `android-publish-update` (gated by release-check) | Play draft |
| 23 | `update`, `new version`, `changelog` | update | `android-publish-update` | version bump |
| 24 | `why rejected`, `rejection`, `Play rejected` | publish | `release-auditor` + `apk-inspector` subagents | diagnosis |
| 25 | `r8`, `APK size`, `shrink`, `keep rules` | build/publish | `android-r8-analyzer` | size report |
| 26 | `import`, `take over`, `Lovable`, `Bolt`, `v0` | idle with existing project | `android-importer` | snapshot + audit |
| 27 | `setup`, `first run`, `cold start`, `SDK missing` | idle no SDK | `setup-wizard` | env ready |
| 28 | Composition: `leak` → `android-debugger-agent` → `android-leak-analyzer` → `compose-view-refactor` → `test` | any | chain (one at a time) | — |

**Notes:**
- `continue` uses `StateManager.continue_loop()` + `router.route_full` to pick next pending whose deps are done.
- `add`/`change`/`remove` are **first-class** and never restart the loop (SPEC §4.1 R2).
- `publish` is gated by `release-check.sh` via `PreToolUse` on `play_store` tools — must pass before upload.
