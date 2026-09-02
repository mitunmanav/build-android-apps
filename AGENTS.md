# AGENTS.md — Build Android Apps

Use `$build-android-apps` for any build, run, debug, or ship task.

- **Frontdoor:** `skills/build-android-apps/SKILL.md` — classifies plain English and delegates to 1 of 27 specialists. Only frontdoor loads at startup (under 8k budget); specialists lazy-load.
- **Commands:** `commands/` — 30 plain-English aliases (`/make-app`, `/preview`, `/publish`, etc.) all delegate to frontdoor.
- **State:** `<project>/.build-android/state.json` — single source of truth. `/where` shows phase; Kahn router is deterministic.
- **MCP:** `.mcp.json` — 5 stdio servers (`adb`, `gradlew`, `play-store`, `keystore`, `asset`). Host wrappers generated via `scripts/generate-host-wrappers.py`.

See `SPEC.md` for lifecycle and `docs/ARCHITECTURE.md` for request flow.
