# Loop Reference — Dispatch Templates & Report Contracts

Verbatim structures for every dispatch the controller makes. Do not improvise
around these shapes — they are what keeps controller context small and
subagent outputs mergeable.

---

## 1. Implementer dispatch (per task)

```
<one line: where this task fits in the project>

Read <workspace>/task-<N>-brief.md first — it is your requirements, with the
exact values to use verbatim.

Interfaces and decisions from earlier tasks the brief cannot know:
<exact names/types, or "none">

Resolution of any ambiguity you may notice in the brief:
<rulings, or "none — ask via NEEDS_CONTEXT if you find one I missed">

Write your full report (TDD RED/GREEN evidence, files touched, build/device
verification output) to <workspace>/task-<N>-report.md. Your reply here must
be at most 15 lines:
Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
Commits: <list of short hashes>
Tests: <one line — what passed>
Evidence: <screenshot/layout paths if UI task>
Report: <path>

model: <explicit — see tiering in SKILL.md>
```

## 2. Implementer brief file (controller writes)

```markdown
# Task N: <title>

## Acceptance criteria
- <measurable, from the plan item>

## Files
- Create: <path>
- Modify: <path> (lines <range if known>)
- Test: <path>

## Interfaces
- Consumes: <exact function/class names + param + return types>
- Produces: <same — neighboring tasks learn your names from this block>

## Constraints (verbatim from spec — every one applies to this task)
<state.json constraints[], copied verbatim>

## Google-skill handoff
If a matching skill is installed (check `.skills/`, `android skills list`) —
e.g. edge-to-edge, navigation-3, agp-9-upgrade — load it and follow its
gates; its verification steps REPLACE the default evidence ladder.

## Verification ladder (skip only if a Google skill replaced it)
1. gradlew-mcp run_help → 2. run_build_dry → 3. run_task (assembleDebug)
4. Install + launch (adb-mcp) 5. UI task: layout dump + screenshot BEFORE
and AFTER changes to `.build-android/evidence/task-<N>/`

## Containment
Write only inside the project. Never edit .build-android/state.json (the
controller owns it). No keystore, publish, or network calls beyond gradle
dependency resolution. adb shell only within this app's scope. A violation
is a Critical review finding by definition.

## No placeholders
TBD, TODO, "add appropriate error handling", "similar to task N" — all
forbidden. If you cannot finish a step, return BLOCKED with the reason.
```

## 3. Spec-reviewer dispatch (read-only)

```
You review a diff for SPEC COMPLIANCE only — not code quality.

Files (read in this order):
1. Brief: <workspace>/task-<N>-brief.md   (the requirements)
2. Diff:  <workspace>/review-<base>..<head>.diff   (the only view of the work)
3. Constraints: <same verbatim block as the brief>

Rules:
- The diff file is your only view of the work. Read-only; do not re-run
  suites the implementer ran.
- Do NOT read the implementer's report. Rationales are claims too —
  "Do Not Trust the Report".
- Do not pre-judge: do not write "do not flag X" instructions to yourself.
- If a requirement cannot be verified from this diff alone (it lives in
  unchanged code or spans tasks), report it as a ⚠️ item — do not broaden
  your search.

Verdict (exactly):
Spec Compliance: ✅ Spec compliant | ❌ Issues found | ⚠️ items: <list>
Issues: Critical (Must Fix) / Important (Should Fix) / Minor (Nice to Have)
Assessment: Task quality: Approved | Needs fixes
```

## 4. Quality-reviewer dispatch (read-only, frozen rubric)

Same file list and rules as spec-reviewer, but the lens is the frozen
anti-slop + Kotlin-idioms rubric at `skills/agent-orchestrator/references/quality-rubric.md`
(copied into the dispatch; the reviewer may NOT invent new criteria — a
finding outside the rubric is out of scope and ledgered as a deferred minor).

Verdict identical to spec-reviewer.

## 5. Re-review dispatch (fix rounds)

```
A prior implementer attempted this task N time(s). Verify the FIX only:
files: brief, original diff, fix diff <review-<a7>..<b7>.diff>
For each finding: verdict ADDRESSED | NOT ADDRESSED ("Attempted" is not
addressed). Check the fix diff for NEW breakage only. Out-of-scope
observations → report as deferred minors, never as blockers.
```

## 6. Final whole-plan review

Dispatch on the most capable model. Inputs: `git diff <merge-base>..HEAD`
packaged to a file, the plan's Global Constraints, and the ledger's
deferred/parked lines. Findings → ONE fix dispatch + one scoped re-review.
No second wave.

## 7. qa-user dispatch

Give it: APK/AAB path, device serial, the user's original one-sentence
request. It builds a journey (XML action list), executes it via adb, and
writes `.build-android/evidence/final/journey-result.json` in the schema in
[loop-contract.md](loop-contract.md). It never modifies code.
