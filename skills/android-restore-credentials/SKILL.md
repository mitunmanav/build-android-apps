---
name: android-restore-credentials
description: >
  Restore a user's sign-in on a new device using Credential Manager's restore
  keys feature. Use this when the user has multiple devices and wants automatic
  sign-in across them, or when they ask for "magic link", "sign in across
  devices", or "restore my account". Do not use for first-time sign-in
  (use android-auth) or for OTP-less email verification (use
  android-verified-email).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [restore-keys, credential-manager, multi-device, signin]
---

# Android Restore Credentials

> [!NOTE]
> SYSTEM DIRECTIVE FOR AI AGENT — keep all reads/writes to `<temp_dir>/`.
> Don't dump sensitive tokens to chat. Don't auto-send restore invitations
> without the user's request.

## Prerequisites

- A scaffolded project with Hilt + Compose
- android-auth skill already ran (Credential Manager is wired)
- The user has at least one existing account

## Workflow

### Step 1: Confirm the use case

Ask the user:

> "Did you sign in on another device, and you want to sign in here automatically? (yes / no)"

If no, exit and use android-auth.

### Step 2: Check Credential Manager restore keys support

```kotlin
val credentialManager = CredentialManager.create(activity)
val capabilities = credentialManager.getCapabilitiesAsync()
// capabilities includes RestoreKeys if SDK >= 34
```

If unavailable, show a manual sign-in button.

### Step 3: Initiate restore

```kotlin
val request = GetCredentialRequest.Builder()
    .addCredentialOption(RestoreKeyOptionCredentialOption())
    .build()
val response = credentialManager.getCredential(activity, request)
// handle response.credential as a RestoreKey
```

If the user has a restore key, sign them in. If not, fall back to the standard sign-in.

### Step 4: Secure backend exchange

> [!CAUTION]
> Treat the restore key like a password. Never log it. Never store it locally. Send it to your backend immediately.

```kotlin
suspend fun exchangeRestoreKey(restoreKey: String): AuthResult {
    return authApi.exchangeRestoreKey(restoreKey)  // backend mints session
}
```

## Anti-patterns

- **DO NOT** store the restore key anywhere. It's a one-shot token.
- **DO NOT** auto-send a restore invitation. Wait for the user to ask.
- **DO NOT** fall back to plaintext password entry. Restore only.

## Pairing

- `android-auth` — sign-in flow
- `android-verified-email` — different flow (OTP-less email)

## References

- See [references/architecture.md](references/architecture.md) for the
  backend fence pattern that keeps the restore key out of the app's memory.
