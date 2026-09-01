---
name: app-planner
description: >
  Break a written app spec into a sequenced, resumable build plan and persist
  it to state.json. Run this after app-intake finishes writing `.build-android/spec.md`,
  or any time the user wants to re-plan from a spec. The plan items become the
  /add /remove /change inputs. Do not use this skill for vague prompts (use
  app-intake) or for executing plan items (use the per-phase skills).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [planning, sequencing, deps, plan-algebra]
---

# App Planner

> [!NOTE]
> Read a spec, emit a build plan, save it to state.json. Uses Kahn's deps
> algorithm via the phase-router.

## Prerequisites

- A spec at `.build-android/spec.md` (produced by `app-intake`)
- A state.json file at `.build-android/state.json` (Phase 1 created)

## Workflow

### Step 1: Read the spec

```
tool: Read
args: { "file_path": ".build-android/spec.md" }
```

Extract the 9 spec fields. If any is missing, return to `app-intake` rather than guessing.

### Step 2: Generate plan items

Map spec fields to plan items using this default template:

| # | Phase | Title | Deps |
|---|---|---|---|
| 1 | scaffold | Set up the project (Gradle + Compose + signing) | — |
| 2 | build | Add first screen: `<core action>` | 1 |
| 3 | build | Add navigation between screens | 1, 2 |
| 4 | build | Set up data layer (`<backend>`) | 1 |
| 5 | build | Add sign-in flow (`<accounts>`) | 1 |
| 6 | build | Add push notifications (`<notifications>`) | 1 |
| 7 | build | Add media support (`<media>`) | 1 |
| 8 | build | Add payment support (`<payment>`) | 1 |
| 9 | test | Generate screenshots for all screens | 2, 3 |
| 10 | publish | Write store listing | — |
| 11 | publish | Submit to internal test track | 10 |

Adjust: drop items for fields where the answer is "No" / "None" / "Free".

### Step 3: Persist via state-manager

For each plan item:

```
tool: Bash
args: { "command": "python3 -m state add .build-android/state.json --title '<title>' --phase <phase> --deps '<deps>' --id <id> --by agent", "description": "Add plan item" }
```

### Step 4: Verify with phase-router

Run:

```
tool: Bash
args: { "command": "python3 -m state route .build-android/state.json", "description": "Show ordered plan" }
```

Confirm no cycles:

```
tool: Bash
args: { "command": "python3 -m state check-cycle .build-android/state.json", "description": "Detect cycles" }
```

If a cycle is found, identify and remove the offending `deps`.

### Step 5: Hand off

Print the routed plan to the user in plain English:

> Here's your build plan, in order:
>
> 1. Set up the project
> 2. Add first screen: track recipes
> 3. Add navigation
> ...
>
> Run `/continue` to start working on item 1.

## Anti-patterns

- **DO NOT** include plan items for spec fields the user said "No" to.
- **DO NOT** create plan items the user didn't ask for ("while we're here, let's add analytics").
- **DO NOT** skip cycle detection. Cycles mean a future phase can never start.
- **DO NOT** create a plan item per spec field. Map multiple related fields to one item.

## Pairing

- `app-intake` — upstream (writes the spec)
- `phase-router` (Kahn's deps in `state/router.py`) — verifies the plan
- `state-manager` (`state/manager.py`) — persists plan items

## References

- See [references/spec-to-plan-mapping.md](references/spec-to-plan-mapping.md)
  for the full template and how to drop items for "No" answers.
