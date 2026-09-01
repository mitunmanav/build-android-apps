---
name: android-store-listing
description: >
  Generate the Play Store listing metadata: title (30 char), short description
  (80 char), full description (4000 char), 8+ screenshots, feature graphic,
  content rating, data safety form. Use this when the user asks to "publish"
  or "list my app", or as a step before /publish. Do not use for the actual
  Play Store upload (use android-play + play-store-mcp).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [store-listing, play-store, description, screenshots, content-rating, data-safety]
---

# Android Store Listing

> [!NOTE]
> Generate every Play Store field from the spec. Save to .build-android/listing/.
> Two-tier checklist (agent self-check + user checklist).

## Prerequisites

- `.build-android/spec.md` (from app-intake)
- A signed release AAB (or running debug for screenshots)
- At least 4 screenshots, ideally 8

## Workflow

### Step 1: Two-tier checklist (BEFORE writing)

**Agent self-check:**
- [ ] Title <= 30 characters
- [ ] Short description <= 80 characters
- [ ] Full description <= 4000 characters
- [ ] All screenshots are 1080×1920 or larger
- [ ] Feature graphic is 1024×500
- [ ] All localized strings are present (if user wants multi-language)

**User checklist (ask before publishing):**
- [ ] What's your target audience?
- [ ] What problem does this app solve?
- [ ] What's the one-line value proposition?
- [ ] Any words to avoid? (competitors, trademarked terms)
- [ ] Languages to support?

### Step 2: Generate the listing

Output to `.build-android/listing/`:

```
title.txt            # 30 char
short-description.txt   # 80 char
full-description.txt    # 4000 char
feature-graphic.png     # 1024x500
screenshots/            # 1080x1920 each, 4-8 files
icon-512.png           # Play Store app icon (high-res)
data-safety.json       # inferred from permissions
content-rating.json    # from questionnaire
privacy-policy.md      # generated template
```

### Step 3: Title (30 char max)

Format: `<app name> - <one-line value>`

Examples (good):
- "Recipes - Daily Meal Ideas"
- "Budget Tracker - Spend Smarter"

Examples (bad):
- "The Best Recipes App Ever Made" (33 char, generic)
- "RecipeApp" (no value prop)

### Step 4: Short description (80 char max)

Two sentences. What + who.

> "Discover quick recipes for any ingredient. Perfect for busy weeknights."

### Step 5: Full description (4000 char max)

Structure:
1. **What it does** (2-3 sentences)
2. **Key features** (5-8 bullets)
3. **Why it's different** (1 paragraph)
4. **What's new** (last 1-2 versions)
5. **Call to action**

### Step 6: Privacy policy

Generate a template based on what the app does:

```markdown
# Privacy Policy for <App Name>

Last updated: <date>

## What we collect

| Data | Purpose | Retention |
|---|---|---|
| Email | Sign in | Until account deleted |
| Crash reports | Stability | 90 days |
| Usage analytics | Improvements | Aggregated |

## What we DON'T collect

- Location (unless specified)
- Contacts
- Files outside the app

## Your rights

- Request account deletion: <email>
- Export your data: <email>

## Contact

<email>
```

User must fill in their email and host this on a website. Play Store requires a URL.

### Step 7: Data safety form

Infer from the dependencies + permissions:

| Permission | Required? | Used? | Data collected? | Shared? |
|---|---|---|---|---|
| INTERNET | auto | yes | yes (analytics) | no |
| CAMERA | opt-in | yes | no | no |
| READ_CONTACTS | — | no | — | — |

Generate a JSON summary the agent can paste into Play Console.

### Step 8: Content rating

Generate the questionnaire response:

- Violence: no
- Sexual content: no
- Language: no
- Controlled substances: no
- User-generated content: depends (ask user)
- Personal data: depends (ask user)
- Financial: depends (ask user)
- Health: depends (ask user)

Submit via Play Console. Standard rating for most utility apps is **Everyone**.

### Step 9: Hand off

> Listing ready at `.build-android/listing/`. Run `/publish` to upload to Play Store.

## Anti-patterns

- **DO NOT** claim "the best" or "the only" without evidence. Play Store rejects superlatives.
- **DO NOT** use competitor names in your title.
- **DO NOT** ship without a privacy policy URL. Play Store rejects.
- **DO NOT** ship with placeholder screenshots. Use real screens.

## Pairing

- `android-icons-assets` — generates the icon + screenshots
- `android-play` — submits to Play Store
- `/privacy-policy` slash command — generates this template on demand

## References

- See [references/store-listing-template.md](references/store-listing-template.md)
  for full templates per app category.
