---
name: app-intake
description: >
  Translate a vague or short app idea into a concrete, ship-ready spec. Use
  this skill whenever the user types /make-app or says something like "I want
  to build an app", "make me a X", "I have an idea", or provides 1-3 sentence
  description of what the app does. The skill detects what's missing, asks up
  to 5 plain-English questions, and emits a spec ready for `app-planner` to
  break into tasks. Do not use this skill for bug fixes, edits to an existing
  app, or build errors — those are /add, /change, or /build respectively.
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [intake, planning, onboarding, vibe-coder, non-technical]
---

# App Intake

> [!NOTE]
> Turn a vague idea into a buildable spec. Asks plain-English questions,
> never jargon. Persists everything to state.json.

## Prerequisites

- A `.build-android/state.json` file (auto-created by `/make-app`)
- No technical knowledge required from the user

## Workflow

### Step 1: Capture the prompt

Take `$ARGUMENTS` verbatim. Save it to `state.json.cursor.prompt_raw` via:

```
tool: Bash
args: { "command": "python3 -m state set-prompt .build-android/state.json '$ARGUMENTS'", "description": "Save raw prompt" }
```

### Step 2: Classify

Ask the `intake-clarifier` subagent to classify the prompt into one of:

- **fully-specified** — ready to plan (skip to step 4)
- **partially-specified** — needs <=3 clarifying questions
- **vague** — needs up to 5 plain-English questions

### Step 3: Ask the user

For each missing field, ask **one question at a time** in plain English. Never batch. Always offer a "not sure" or "you pick" option.

| Field | Plain-English question |
|---|---|
| audience | "Who will use this app? (e.g., just you, your team, the public)" |
| core action | "What is the ONE thing users will do most often?" |
| screens | "Roughly how many screens do you imagine? (1 / 2-3 / 4+)" |
| accounts | "Will users sign in, or no accounts?" |
| backend | "Does your app need to save data online (e.g., sync between devices) or stay on-device only?" |
| payment | "Will you charge users — one-time, subscription, or free?" |
| notifications | "Do you want push notifications?" |
| media | "Camera, microphone, video, music — or none of those?" |

Stop asking as soon as the user answers "you pick" or after 5 questions.

### Step 4: Synthesize spec

Write a 1-page spec to `.build-android/spec.md`:

```markdown
# App Spec: <name>

## What it does
<2-3 sentences>

## Users
<who, how many, how often>

## Core action
<the ONE thing>

## Screens
- Screen 1: <purpose>
- Screen 2: <purpose>
- ...

## Accounts
<yes / no / which provider>

## Data
<on-device only / Supabase / Firebase / both>

## Money
<free / one-time / subscription / in-app purchases>

## Notifications
<yes / no>

## Media
<none / camera / audio / video / music>

## Other
<anything the user named that doesn't fit above>
```

### Step 5: Hand off to planner

Tell the user the spec is ready, and offer to:

> Run `/continue` to break this into a build plan, or change anything first.

## Anti-patterns

- **DO NOT** ask 5 questions in one message. One at a time.
- **DO NOT** use jargon ("API", "endpoint", "schema", "Firebase SDK").
- **DO NOT** assume the user knows what Supabase or Firebase is. Just ask "do you want data synced between devices?"
- **DO NOT** skip the spec.md write step. It's the contract for `app-planner`.

## Pairing

- `intake-clarifier` subagent — classifies the prompt
- `app-planner` skill — turns the spec into a build plan
- `/make-app` slash command — pre-approved entry point

## References

- See [references/question-bank.md](references/question-bank.md) for the full
  plain-English question library and "you pick" defaults.
