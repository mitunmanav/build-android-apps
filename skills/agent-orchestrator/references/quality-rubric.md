# Frozen Quality Rubric — Android/Kotlin

Version: 1 (2026-09-02). **Frozen**: reviewers and gates may flag ONLY these
items. New items require editing this file (and re-running evals), never
inventing criteria mid-review. Ordered by how fast each hurts in production.

## Critical (blocks the task)

| ID | Pattern | Evidence to look for |
|---|---|---|
| C1 | Swallowed error | `catch (e: Exception) { }`, empty catch, catch that only logs then proceeds as if nothing happened on a path that needed to fail |
| C2 | Placeholder / stub | `TODO`, `FIXME`, `todo!`-style stubs, dummy return values in executable paths |
| C3 | Confident hallucination | API call, SDK method, enum value, or config key not verifiable against the project's dependency versions — must be checked, not assumed |
| C4 | Security non-check | Auth/permission logic with wrong boolean logic, trust of client-supplied identity, exported component without cause, missing `FLAG_IMMUTABLE` |
| C5 | Containment violation | Writes outside the project, edits to `.build-android/state.json`, keystore/publish access, network beyond gradle resolution |
| C6 | Fake test | Test asserts against its own mocks such that it would pass if the real code were deleted; coverage theater |

## Important (should fix before the task is trusted)

| ID | Pattern | Evidence to look for |
|---|---|---|
| I1 | Deferral language | "for now", "temporary", "quick fix", "later" in comments or naming |
| I2 | Hedging | "should work", "hopefully", "assumes" — uncertainty shipped instead of resolved |
| I3 | Duplicate logic | New helper that reimplements an existing project utility or dependency (grep before judging) |
| I4 | Over-abstraction | Interface/abstract class with exactly one implementation and no polymorphism reason; factory/strategy where a function does |
| I5 | Race-blind shared state | read-modify-write on shared state without atomicity/confinement consideration |
| I6 | Compose instability | unstable lambda/collection params in hot recomposition paths, state hoisted wrong, work in composition |
| I7 | Wrong-era code | blocking IO on main dispatcher, deprecated API, pattern the surrounding file's era abandoned |

## Minor (note, never block)

| ID | Pattern | Evidence to look for |
|---|---|---|
| M1 | Narrative comment | Comment restates what the code obviously does; comment-to-logic ratio padding |
| M2 | Magic number | Unexplained literal that carries meaning (timeouts, thresholds) not lifted to a named constant |
| M3 | Generic naming | `data`, `result`, `temp`, `handleX`, `Manager`/`Helper`/`Util` without domain meaning in public surface |
| M4 | Config cargo cult | Constant promoted to env/flag/config with no realistic second value |
| M5 | Import chaos | Unused imports, imports inside functions, deprecated module paths |

## Context exceptions (these are NOT slop)

- `i`, `x`, `acc` in 3-line scopes; verbose names in public APIs
- Defensive checks in public-facing APIs handling user input
- Detailed KDoc on public library surface
- Deliberate fakes in test sourcesets (fakes over mocks is doctrine)

## Scoring

- Any Critical → quality verdict `Needs fixes`, loop enters fix round.
- ≥2 Important → `Needs fixes` recommended; 1 Important → orchestrator's
  judgment (ledger the call).
- Minors and deferred items → ledger only.
