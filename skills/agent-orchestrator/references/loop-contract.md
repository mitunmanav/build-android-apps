# Loop Reference — Workspace, Ledger, Resume, Journeys

## 1. Workspace layout

Per-plan scratch dir: `.build-android/tasks/`. Self-gitignored (write
`*` into `.build-android/tasks/.gitignore` on creation). State.json is NOT
in here — it is the durable record; this dir is disposable.

```
.build-android/
  tasks/
    .gitignore                # contains: *
    task-1-brief.md
    task-1-report.md
    review-abc1234..def5678.diff   # named per range — re-reviews get fresh files
    task-2-brief.md ...
  evidence/
    task-1/before.png  after.png  layout.json  build-tail.txt
    final/journey-result.json
  resume.md
  state.json                  # the only durable truth
```

Cleanup: after a clean final review + qa-user report, delete briefs/reports/
diffs (ledger + git history are the record). Evidence dir stays until
publish or `/reset`.

## 2. Ledger line formats (store via `python -m state ledger`)

```
Task <N>: complete (commits <a7>..<b7>, review clean)
Task <N>: complete (commits <a7>..<b7>, review clean, <K> parked)
Task <N>: fix round <R>/5 (<X> addressed, <Y> open — <one-liners>; commits <a7>..<b7>)
Task <N>: minor (deferred): <one-liner>
Task <N>: parked — <finding> — Ruling: <why it stands>
Ruling: <what you decided> — <why> — <what it costs if wrong>
```

Rules: every decision gets a line; silent discard is forbidden. Any ledger
append resets the staleness counter (the CLI does this automatically).
Resume = first task without a `complete` line; a task whose last line is a
fix round resumes at the next round.

## 3. resume.md template (write at loop start, update at every stop)

```markdown
# Resume — build-android-apps loop

state: <project>/.build-android/state.json (trust ledger + git log over memory)
mode: <guided|autopilot>   status: <running|stopped|awaiting_user>
device: <serial>           branch: <name>

## Where we are
<one plain-English sentence: task N of M, what just happened>

## Next step
<exact next action: "resume task-3 fix round 2" | "task-4 brief" | "final review">

## Waiting on
<user question(s), or "nothing">

## Last 3 ledger lines
<copied from state.json ledger>
```

If resume.md is missing, rebuild it from the ledger tail + `git log --oneline -10`
before continuing. After a staleness STOP, the failure reason goes here.

## 4. Journey schema (qa-user, per Google android-cli journeys)

The journey is an XML action list; the journey is the source of truth — if
the app disagrees, the app has failed:

```xml
<journey name="Habit tracker first run">
  <description>Open app, add first habit, see it on the list</description>
  <actions>
    <action> Tap the "+" button bottom-right </action>
    <action> Type "Morning run" into the name field </action>
    <action> Tap "Save" </action>
    <action> Verify "Morning run" appears in the list </action>
  </actions>
</journey>
```

Result written to `.build-android/evidence/final/journey-result.json`:

```json
{
  "journey": "Habit tracker first run",
  "results": [
    {
      "action": "Tap the \"+\" button bottom-right",
      "status": "PASSED",
      "commands": ["adb shell input tap 990 2100"],
      "comment": ""
    }
  ]
}
```

`status` is `PASSED` | `FAILED` (could not evaluate) | `SKIPPED` (journey
ended early after a failure). If the app exits, crashes, or freezes,
evaluation stops and the journey fails. Execution order per step: layout
dump (use `--diff` to keep context small) → screenshot (visually examine
the PNG FIRST) → `adb shell input` via element center/bounds.

## 5. Device-evidence gate (default ladder, per UI/logic task)

| Task type | Minimum evidence |
|---|---|
| Logic (ViewModel, Room, data) | build ladder + unit test RED→GREEN output in report |
| UI (Compose screens, theming) | build ladder + install + launch + screenshot BEFORE & AFTER + layout diff |
| Manifest/permission change | build ladder + install + launch + runtime permission behavior check |
| Any change | no `gradlew clean` — never, as verification |

A Google skill's own gates (e.g. edge-to-edge checklist, agp-9 sync + help +
dry-run) REPLACE the matching ladder steps when one is loaded — record which
in the brief's verification section.
