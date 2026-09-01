---
name: android-auth
description: >
  Add a sign-in flow to an Android app using Credential Manager. Supports
  Google sign-in, email/password, and passkeys. Use this when the user said
  "yes, sign in" during /make-app, or when they ask to add login. Do not use
  for OTP-less verified email (use android-verified-email), for restoring
  credentials on a new device (use android-restore-credentials), or for
  sign-out only (use /change to find the existing logout).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [auth, credential-manager, google-sign-in, signin, login]
---

# Android Auth

> [!NOTE]
> Credential Manager first. Never raw Google Sign-In SDK. Integration-point
> discovery via search strings (matches Google's `verified-email` pattern).

## Prerequisites

- A scaffolded project with Hilt + Compose
- The user picked an auth provider during /make-app intake

## Workflow

### Step 1: Read the spec

Read `.build-android/spec.md` for `accounts` field:

- `Google` → Google sign-in via Credential Manager
- `Email and password` → email/password + reset link
- `Passkeys` → passkey-only (newer, simpler UX)
- `Both Google + Email` → Google as primary, email as fallback
- `No` → exit; this skill doesn't apply

### Step 2: Add dependencies

```toml
androidx-credentials = { module = "androidx.credentials:credentials", version = "1.5.0" }
androidx-credentials-play-services = { module = "androidx.credentials:credentials-play-services", version = "1.5.0" }
google-id = { module = "com.google.android.gms:play-services-auth", version = "21.3.0" }
```

### Step 3: Integration-point discovery

Before adding any code, search the project to find existing auth-related code:

```
tool: Grep
args: { "pattern": "signInWithCredential|FirebaseAuth|GoogleSignIn|getCredentialAsync", "path": "app/src/main/kotlin" }
```

If existing code uses the legacy `GoogleSignInClient`, warn the user that we'll be replacing it. Don't silently overwrite.

### Step 4: Credential Manager flow

```kotlin
suspend fun signInWithGoogle(activity: Activity): AuthResult {
    val credentialManager = CredentialManager.create(activity)
    val request = GetCredentialRequest.Builder()
        .addCredentialOption(GoogleIdOptionCredentialOption.Builder()
            .setFilterByAuthorizedAccounts(false)
            .setServerClientId(BuildConfig.GOOGLE_WEB_CLIENT_ID)
            .build())
        .build()
    val response = credentialManager.getCredential(activity, request)
    return when (val cred = response.credential) {
        is GoogleIdOption -> {
            val idToken = credentialManager.getCredential(activity, request).credential
                .data.getString("idToken")!!
            // pass to backend
            AuthResult.Success(idToken = idToken)
        }
        else -> AuthResult.Failure("Unsupported credential")
    }
}
```

### Step 5: Account deletion

Wire `deleteAccount()` per `android-backend`. Test that it:

1. Deletes the backend account
2. Clears local storage (Room + DataStore)
3. Signs out the user
4. Returns to the splash screen

### Step 6: Compose UI

Build a `SignInScreen` that:

- Shows the sign-in button(s) for the configured provider(s)
- Shows "Skip for now" only if the spec allows anonymous use
- On success, navigates to the home screen
- On failure, shows an error message and offers retry

## Anti-patterns

- **DO NOT** use the legacy `GoogleSignInClient` directly. Use `CredentialManager` only.
- **DO NOT** store the ID token in DataStore. Send it to your backend immediately and discard.
- **DO NOT** skip the account deletion endpoint. Play Store Data Safety requires it.
- **DO NOT** use `GoogleSignIn` on its own; `CredentialManager` already supports multiple providers.

## Pairing

- `android-backend` — wires the backend that consumes the ID token
- `android-restore-credentials` — handles new-device sign-in
- `android-verified-email` — for OTP-less email verification

## References

- See [references/integration-points.md](references/integration-points.md)
  for the full search-string list to find existing auth code.
- See [references/account-deletion.md](references/account-deletion.md) for
  the Play Store Data Safety contract.
