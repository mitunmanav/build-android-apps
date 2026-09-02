# AGENTS.md — Build Android Apps

Use `$build-android-apps` for any build, run, debug, or ship task.

- **Bootstrap:** `hooks/bootstrap.md` is injected at SessionStart (startup/resume/clear/compact). It routes plain English to the frontdoor automatically — commands are optional, not required.

- **Frontdoor:** `skills/build-android-apps/SKILL.md` — classifies plain English and delegates to 1 of 28 specialists. Only frontdoor loads at startup (under 8k budget); specialists lazy-load.
- **Commands:** `commands/` — 31 plain-English aliases (`/make-app`, `/preview`, `/publish`, `/run-plan`, …) all delegate to frontdoor.
- **Loop:** `skills/agent-orchestrator/SKILL.md` — autonomous plan execution: fresh implementer per task → device evidence → two read-only reviews → bounded fix loop, resumable via state.json v2 (`orchestration{}`, `ledger[]`).
- **State:** `<project>/.build-android/state.json` — single source of truth. `/where` shows phase; Kahn router is deterministic.
- **MCP:** `.mcp.json` — 5 stdio servers (`adb`, `gradlew`, `play-store`, `keystore`, `asset`). Host wrappers generated via `scripts/generate-host-wrappers.py`.

See `SPEC.md` for lifecycle and `docs/ARCHITECTURE.md` for request flow.
