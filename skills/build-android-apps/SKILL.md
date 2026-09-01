---
name: build-android-apps
description: >
  Build, run, debug, and ship Android apps from plain English. Use this
  whenever the user wants to make an app, add a feature, fix a crash,
  preview on device, or publish to Play Store. This frontdoor classifies
  intent and delegates to the right specialist skill (intake, scaffold,
  run, debug, backend, auth, store-listing, publish, etc.). Do not use
  specialist skills directly — this frontdoor routes to them.
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: build-android, frontdoor, router, android, ship
---

# Build Android Apps — Frontdoor

> [!NOTE]
> **One skill to rule them all.** Say plain English; this skill routes to the right specialist.
> Progressive disclosure: only this description loads at startup. Specialists load lazily on delegation.

## Prerequisites

- None — this skill checks project state itself (`python -m state where`).

## Workflow

### Step 1: Load state + server budget check

1. Run `python -m state where .build-android/state.json` (one call — no separate `cat`).
2. If missing: cold start → delegate to `setup-wizard` then `app-intake`.
3. Note: keep this `SKILL.md` under 500 lines; specialists stay in `references/` until needed.

### Step 2: Classify intent (deterministic, no LLM)

Use the routing table in [references/routing-table.md](references/routing-table.md). Keyword + state-aware:

- If user text contains only keywords, match longest first.
- If no keyword matches, ask: "Did you mean: make an app / add a feature / debug / publish?"
- Never guess silently.

Common intents: `make-app` → `app-intake`, `add/change/remove` → `state add/change/remove`, `where` → `state where`, `build/run/preview` → `android-run`, `debug/crash/log` → `android-debug-fix`, `publish/ship` → `android-store-listing` → `android-publish-update`.

### Step 3: Delegate — load ONE specialist

1. Read **one** `skills/<specialist>/SKILL.md` into context.
2. Follow its `Workflow` steps verbatim.
3. Do NOT load two specialists at once (keeps tokens cheap).

See [references/delegation.md](references/delegation.md) for the load protocol.

### Step 4: Update state + report (plain English)

1. After specialist finishes, run `python -m state where` or `python -m state route`.
2. Summarize in one sentence what changed and what is next: "Done: <specialist>. Next: <phase> <task>. Say 'go' or run /continue."
3. If a strict-output-limit specialist was used, point to `.scratch/<skill>-<uuid>/` for full report.

## Anti-patterns

- **DO NOT** load all 27 specialists at once — one at a time only.
- **DO NOT** re-classify mid-task — finish delegate, then re-route.
- **DO NOT** skip state check — resumability depends on it.
- **DO NOT** invent tool results — wait for MCP output.

## Pairing

- `app-intake` — first-run idea → spec
- `app-planner` — spec → Kahn-routed plan
- `android-scaffold` — Gradle/Compose project
- `android-run` — install + launch + screenshot
- `android-debug-fix` — logcat → fix loop
- `android-backend` / `android-auth` / `android-ops` / `android-media` — domain slices
- `android-icons-assets` / `android-store-listing` / `android-publish-update` — ship
- See [references/routing-table.md](references/routing-table.md) for full 27.

## References

- See [references/routing-table.md](references/routing-table.md) — full intent → specialist map
- See [references/delegation.md](references/delegation.md) — how to delegate without context bloat
- See [references/examples.md](references/examples.md) — 10 utterances → routing decisions

## Final Checklist

- [ ] State loaded (`where` ran)
- [ ] Intent classified via table (or clarified with user)
- [ ] One specialist `SKILL.md` loaded and executed
- [ ] State flushed + summarized in plain English
- [ ] If truncated, full report saved to `.scratch/`
