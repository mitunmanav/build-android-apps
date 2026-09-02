---
name: agent-orchestrator
description: >
  Execute a project plan autonomously through subagents: a fresh implementer
  per task, device-evidence verification (build + install + launch + screenshot),
  two-stage review (spec compliance then code quality), a bounded fix loop,
  and a resumable ledger in state.json. Use when the user says "go", "continue",
  "run the plan", "do it all", after /make-app produces a plan, or whenever a
  plan exists with pending tasks. Do not use for single quick questions, for
  /where status checks, or when no plan exists (route to app-intake first).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-02'
  keywords: orchestrator, subagents, loop, autonomous, plan execution, android
---

# Agent Orchestrator — The Loop

> [!NOTE]
> Fresh subagent per task + device evidence + two-stage review + resumable ledger.
> The controller coordinates; it never implements, never reads diffs, never fixes code.

## Prerequisites

- A plan with pending tasks in state.json (`python -m state where` to confirm)
- `python3` on PATH; MCP servers wired (`.mcp.json`)
- A device or emulator (the pre-flight step handles this)

## Workflow

### Step 1: Pre-flight (all three, or no loop)

1. **Clean tree**: run `git status --porcelain`. Uncommitted changes outside
   `.build-android/` → stop, ask the user to commit or stash. Autonomous
   per-task commits must not absorb unrelated work.
2. **Device**: `adb-mcp.list_devices`. None → start the default emulator
   (`emulator -avd <name>` or ask the user). Record serial in state.
3. **Daemon warm**: `gradlew-mcp.run_help` (lightweight gate, no clean).
4. Load state: mode (`guided`/`autopilot`), `constraints[]`, ledger tail.
5. Write `.build-android/resume.md` (template in
   [references/loop-contract.md](references/loop-contract.md)) — the wake-up
   file that lets any future session resume mid-loop.

### Step 2: Controller rules (non-negotiable)

- **Narrate at most one short line between tool calls.** The ledger and tool
  results carry the record.
- **Never fix findings yourself.** Controller fixes skip review and pollute
  coordination context.
- **Hand artifacts over as files.** A dispatch prompt describes one task —
  never paste accumulated history or the whole plan.
- **Read-only inputs**: briefs you wrote, `Status:` reply lines, verdict
  blocks, ledger, state.json. Diffs and reports belong to reviewers.
- **Always specify the model explicitly** when dispatching. Omitted model =
  inherits the (expensive) session model.

### Step 3: Per-task loop

For each task from `python -m state route` (Kahn order):

1. **Brief**: write `.build-android/tasks/task-<N>-brief.md` — task title,
   acceptance criteria, `Files:` (create/modify), `Interfaces:` (exact names
   and types neighboring tasks use), `Constraints:` (verbatim from
   state.json), and the Google-skill line from Phase 3. Batch rule: several
   small same-shape edits → ONE brief listing every file.
2. **Dispatch implementer** (template: [references/prompt-templates.md](references/prompt-templates.md))
   with exactly 5 items: (1) one line where this task fits, (2) brief path
   ("read this first — it is your requirements"), (3) interfaces/decisions
   from earlier tasks the brief cannot know, (4) your resolution of any
   ambiguity, (5) report path + report contract. Log via
   `python -m state agent-log implementer <task_id> <model> dispatched`.
3. **Handle the status**:
   - `DONE` / `DONE_WITH_CONCERNS` → review
   - `NEEDS_CONTEXT` → provide it, re-dispatch (never force an unchanged retry)
   - `BLOCKED` → 4-branch tree: context problem → more context; needs more
     reasoning → stronger model; too large → split the task; plan wrong →
     rule on the correction, ledger the Ruling, re-dispatch with the ruling.
     Genuinely independent-blocked → park the task, run the next one.
4. **Review fan-out — one turn, both reviewers, read-only**: spec-reviewer
   (brief vs diff) and quality-reviewer (frozen rubric vs diff). Each returns
   `✅ Spec compliant | ❌ Issues found | ⚠️ Cannot verify from diff`,
   severity `Critical / Important / Minor`, and `Task quality: Approved |
   Needs fixes`. A `⚠️` item → YOU resolve it (device check via MCP, paste
   result); if real, it enters the fix loop.
5. **Fix loop — max 5 rounds**: rounds 1–3 resume the original implementer
   with findings verbatim; rounds 4–5 dispatch a fresh implementer one model
   tier up ("a prior implementer attempted this task N times; you own it
   now"). One fix dispatch + one scoped re-review per round; re-reviewer
   verdicts each finding `ADDRESSED | NOT ADDRESSED` ("Attempted is not
   addressed"). Minor findings never enter the loop — ledger them deferred.
   At round 5, adjudicate every open finding into the ledger (parked /
   park-with-ruling / carry-forward). Silent discard is forbidden.
6. **Complete**: implementer's commits verified →
   `python -m state ledger <task_id> "Task <N>: complete (commits <a7>..<b7>, review clean[, <K> parked])"`
   → `python -m state record-done <task_id>` → next task.
   Metrics bookkeeping (`record-done --first-pass` when round count was 0).

### Step 4: Stop conditions (only these four)

An irreversible or destructive operation; a security-sensitive action; a side
effect outside the project (publish, push, keystore ops — the release-check
hook enforces publish); a plan so broken every path is a guess. Everything
else: Rulings, not stalls — decide from spec + constraints, ledger
`Ruling: <what> — <why> — <cost if wrong>`, continue.

### Step 5: Staleness cap

After each loop step with NO state advance, `python -m state stale`. At 3
consecutive stale steps: stop, set status `stopped`, write the failure to
`resume.md`, and tell the user in one plain-English sentence. Never argue
with yourself past the cap.

### Step 6: Finish

1. All tasks complete → dispatch the **final whole-plan review** (strongest
   model) over `git diff <merge-base>..HEAD`, pointed at deferred/parked
   ledger lines. Findings → ONE fix dispatch + one scoped re-review. No
   second wave.
2. Dispatch **qa-user** — runs the app on the device as a real user
   (journey JSON per [references/loop-contract.md](references/loop-contract.md)),
   per-action PASSED/FAILED evidence saved under
   `.build-android/evidence/final/`.
3. Plain-English report: what was built, evidence links, parked items,
   metrics (`tasks_done / first_pass_rate / fix rounds`). Then delete the
   workspace's brief/report files (the ledger + git history are the record).

### Resuming an interrupted run

`resume.md` + ledger first-lines are the recovery map — trust them over
conversation memory. Tasks with a `complete` ledger line are DONE (never
re-dispatch). A task whose last ledger line is a fix round resumes at the
next round. If `resume.md` is gone, rebuild it from the ledger + `git log`.

## Modes

| Mode | Human gates | Used by |
|---|---|---|
| `guided` | Spec approval (1, shown in chunks; hedged replies like "looks reasonable" are NOT approval) | `/make-app` |
| `autopilot` | None mid-run; every ruling ledgered; `/undo` reverts the last task's commit range | `/continue`, `/add`, `/change` |

Publish, destructive, and security actions are gated in BOTH modes (hook-enforced).

## Model tiering

Mechanical 1–2 file tasks with complete specs → cheap model. Integration /
multi-file → standard. Architecture and the final whole-plan review → most
capable. Fix rounds 4–5 → one tier above the stuck implementer. Turn count
beats token price; mid-tier is the floor for reviewers and prose implementers.

## Anti-patterns

- **DO NOT** dispatch implementers in parallel (shared working tree).
- **DO NOT** let reviewers see the implementer's report or reasoning — diff
  + brief + constraints only. Do not trust the report.
- **DO NOT** paste session history into a dispatch; a fresh subagent needs
  its task, interfaces, and constraints. Nothing else.
- **DO NOT** skip the device evidence gate because the build passed.
- **DO NOT** continue past 3 stale steps or 5 fix rounds.
- **DO NOT** edit state.json by hand — `python -m state` only.

## Anti-rationalizations

| If you catch yourself thinking… | The answer is |
|---|---|
| "The build passed, skip the device check" | Build-passing ≠ app-working. Evidence gate runs. |
| "One small task — no reviewers needed" | Controller fixes skip review. Dispatch both reviewers. |
| "Re-dispatch with the same prompt, maybe it works this time" | Never retry without changes — use the 4-branch tree. |
| "The fix is obvious, I'll just edit it myself" | Controller never fixes code. Dispatch the implementer. |
| "We're at round 6 but it's almost done" | Cap is 5. Adjudicate into the ledger and move on. |
| "Parking findings is quieter than asking the user" | Parked ≠ discarded — every parked item gets a ledger line and appears in the report. |

## Pairing

- `app-planner` — produces the plan this skill executes
- `android-debug-fix` — when the implementer status is BLOCKED by a runtime crash
- `release-auditor` + `apk-inspector` — pre-publish gates after the loop finishes
- Google's installed Android skills (`android skills list`) — loaded by
  implementers when a task matches (their gates replace the default ladder)

## References

- [references/prompt-templates.md](references/prompt-templates.md) — dispatch templates + report contracts + verdict vocab
- [references/loop-contract.md](references/loop-contract.md) — workspace layout, ledger line formats, resume.md template, journey JSON

## Final Checklist

- [ ] Pre-flight passed (clean tree, device, daemon warm) before task 1
- [ ] Every task: brief → implementer → 2 reviewers → fix loop ≤5 → ledger line
- [ ] Every UI task has before/after screenshot evidence in `.build-android/evidence/`
- [ ] All rulings and parked findings are in the ledger (no silent discards)
- [ ] Final whole-plan review + qa-user journey run and reported in plain English
- [ ] resume.md matches the ledger; workspace briefs/reports cleaned up
