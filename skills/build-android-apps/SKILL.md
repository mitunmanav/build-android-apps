---
name: build-android-apps
description: >
  Build, run, debug, and ship Android apps from plain English. Use this
  whenever the user wants to make an app, add a feature, fix a crash,
  preview on device, or publish to Play Store — or when they ask for help,
  don't know what to do next, or want to know what this plugin can do.
  This frontdoor classifies intent and delegates to the right specialist
  skill (intake, scaffold, run, debug, backend, auth, store-listing,
  publish, etc.). Do not use specialist skills directly — this frontdoor
  routes to them.
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

### Step 0: Wake-up check (bootstrap fired you)

The SessionStart hook injects a bootstrap that routes plain English here. On any
Android-related utterance, you are already in the right skill — do not ask
permission to use it. Handle these three shapes before anything else:

- **Resume** ("go", "continue", or any utterance with existing state.json): run
  Step 1 first, then say in plain English: "You're at phase X, task Y" and
  continue from there. Never re-ask what the state already knows.
- **Complaint** ("it crashed", "not working", "stuck on X"): route to
  `android-debug-fix` directly — a complaint is a debug intent even without the
  word "debug".
- **Idea** ("make me an app that…"): route to `app-intake` — spec first, ONE
  approval, then the build loop runs hands-free.

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

Triage (size the response): vague idea → full intake (architectural); single small change (`/change`, dark mode) → in-chat design, no new plan doc (bounded); feasibility question (`can we…`) → answer first, no code kept (spike). Never over-spec a small task.

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

- **DO NOT** load all 28 specialists at once — one at a time only.
- **DO NOT** re-classify mid-task — finish delegate, then re-route.
- **DO NOT** skip state check — resumability depends on it.
- **DO NOT** invent tool results — wait for MCP output.

## Pairing

- `app-intake` — first-run idea → spec
- `app-planner` — spec → Kahn-routed plan
- `agent-orchestrator` — executes the plan task-by-task via subagents (fresh implementer → device evidence → two reviews → fix loop), with a resumable ledger in state.json
- `android-scaffold` — Gradle/Compose project
- `android-run` — install + launch + screenshot
- `android-debug-fix` — logcat → fix loop
- `android-backend` / `android-auth` / `android-ops` / `android-media` — domain slices
- `android-icons-assets` / `android-store-listing` / `android-publish-update` — ship
- See [references/routing-table.md](references/routing-table.md) for full 28.

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
