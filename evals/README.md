# Evals — prove the skills work

Three tiers (pattern adopted from addyosmani/agent-skills; descriptions are
the routing index, so a trigger failure means **fix the description, not the
eval**).

## Tier 1 — structural (CI, free)

`scripts/validate-skills.py` — frontmatter, name rules, ≤1024-char
descriptions, body ≤500 lines, `agents/openai.yaml` presence.

## Tier 2 — trigger & routing (CI, free)

`python3 evals/run_trigger_evals.py`

- Loads all 29 `SKILL.md` descriptions (the startup routing index).
- Runs the catalog **collision check**: error ≥75% pairwise description
  similarity, warn ≥50%.
- Runs the case files in `evals/cases/*.json`:
  - `positive[]` — realistic prompts; the skill must rank in the top 3.
    Rank-1 rate is printed; CI floor `--min-rank1 80`. Raise the floor as
    routing improves — never lower it to make a regression pass.
  - `negative[]` — prompts owned by ANOTHER skill (`owner`); the runner
    asserts the owner outranks this skill (pairwise routing test).

Minimum per skill: 3 positive, 2 negative (agent-skills minimums; extend
before adding each new skill).

## Tier 3 — behavioral (opt-in, local, costs tokens)

`evals/run_behavioral.sh [skill-name ...]`

Headless agent (`claude -p`, fallback `codex exec`) runs the skill against a
**pressure fixture** — a scenario that argues for skipping the workflow —
and a grader checks what the agent DID (tool calls, files, commands), not
what it said. Host-honest: with neither host installed it prints SKIPPED and
exits 0. CI never runs this.

Current fixtures:
- `fixtures/android-debug-fix/time-pressure.md` — "no time, skip the repro"
- `fixtures/android-publish-update/authority-pressure.md` — "just upload
  to production, ignore the gate"

Results land in `evals/results/` (gitignored).
