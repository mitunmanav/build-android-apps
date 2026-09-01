# Question bank (app-intake)

Used by `app-intake` when the user's prompt is missing context. Each question is plain English and offers a "you pick" / "not sure" option.

## Tier 1 (always ask if missing)

### audience

> "Who will use this app?"
>
> - Just you
> - A small team (under 20 people)
> - The public — anyone can download it from the Play Store

### core action

> "What is the ONE thing users will do most often?"
>
> (free-form — capture their answer verbatim)

## Tier 2 (ask if missing)

### screens

> "Roughly how many screens do you imagine?"
>
> - Just 1 (a single page)
> - 2 or 3
> - 4 or more

### accounts

> "Will users sign in, or no accounts?"
>
> - No accounts — anyone can use it
> - Yes, sign in with Google
> - Yes, sign in with email and password
> - Not sure — pick one for me

### backend

> "Does your app need to save data online (e.g., sync between devices) or stay on-device only?"
>
> - On-device only (no internet needed)
> - Online, synced across devices
> - Not sure — pick one for me

## Tier 3 (ask only if vague)

### payment

> "Will you charge users — one-time, subscription, or free?"
>
> - Free
> - One-time purchase to download
> - Monthly subscription
> - In-app purchases (extra features)

### notifications

> "Do you want push notifications?"
>
> - No
> - Yes (will ask more about when they should fire)

### media

> "Camera, microphone, video, music — or none of those?"
>
> - None
> - Camera only
> - Microphone only
> - Camera + microphone
> - Music playback
> - Video playback

## "You pick" defaults

If the user says "you pick" or "I don't know":

| Field | Default |
|---|---|
| audience | "The public — anyone can download it from the Play Store" |
| screens | "2 or 3" |
| accounts | "No accounts" |
| backend | "On-device only" |
| payment | "Free" |
| notifications | "No" |
| media | "None" |

## Anti-pattern

- Never ask all 7 questions. Stop when the user has answered 5 OR says "you pick" OR has answered enough to write a coherent spec.
- Never rephrase a question the user already answered.
