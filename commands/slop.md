---
description: Scan changed Kotlin files for AI-slop residue and hand back a narrow repair prompt.
allowed-tools:
  - Bash
  - Read
  - Grep
---

# /slop

Run the residue gate: tests → lint → slop scan (in that order — a slop scan
on broken code is noise). The gate uses the frozen rubric at
`skills/agent-orchestrator/references/quality-rubric.md`; findings are
advisory until the release-auditor consumes the score.

## Context

- Working directory: !`pwd`
- Changed Kotlin files: !`git diff --name-only HEAD 2>/dev/null | grep -E '\.kt$|\.kts$' || echo "(none uncommitted)"`
- Last build: !`python3 -c "import json;print(json.load(open('.build-android/state.json')).get('build',{}).get('last_assemble','unknown'))" 2>/dev/null || echo unknown`

## Your task

### Step 1: Behavior gate first

If the changed files have failing tests or don't compile, STOP — fix
behavior first. Slop findings on non-compiling code are noise.

### Step 2: Scan

1. Run the deterministic hook subset per changed file
   (`hooks/slop-gate.sh` rules): empty/swallowed catch, TODO stubs,
   deferral language, hedging, narrative comments.
2. Then apply the full rubric by reading the diffs (C1–C6, I1–I7, M1–M5),
   including what the hook cannot see (C3 hallucinated APIs — verify against
   the project's dependency versions; C6 fake tests; I3 duplication).

### Step 3: Report

For each finding: `[severity] rubric-id — file:line — one-line evidence`.
If none: "Clean — no rubric findings" and stop.

### Step 4: Narrow repair (only for Critical/Important)

Hand the fixer EXACTLY this contract:

```
Fix only the findings listed below.
Rules:
- Preserve behavior. Do not rewrite unrelated code.
- Do not rename public APIs unless a finding requires it.
- Prefer existing project helpers over new ones.
- For each fix report: finding removed / file changed / why safer or clearer /
  the test-lint-build command proving behavior still works.
- If a finding is a false positive, leave the code unchanged and say why.
```

## Anti-patterns

- **DO NOT** let cleanup become a refactor — if it grows, stop and split.
- **DO NOT** delete a catch without understanding what it swallowed.
- **DO NOT** block on Minor findings — ledger or note them only.

## Final Checklist

- [ ] Behavior gate ran before the scan
- [ ] Findings cite rubric IDs with file:line evidence
- [ ] Repairs used the narrow contract; proof re-run after fixes
