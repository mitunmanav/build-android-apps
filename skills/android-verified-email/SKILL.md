---
name: android-verified-email
description: >
  Add OTP-less email verification using Credential Manager and SD-JWT. Use
  this when the user wants friction-free email-based sign-in, or when they
  mention "magic link", "passwordless", or "verify my email". Do not use for
  restore keys across devices (use android-restore-credentials), or for any
  OTP-based flow.
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [otp-less, verified-email, sd-jwt, credential-manager, email]
---

# Android Verified Email

> [!NOTE]
> SYSTEM DIRECTIVE FOR AI AGENT — integration-point discovery BEFORE writing
> any code. Search for existing sign-in / verify-email code first.

## Prerequisites

- A scaffolded project with Hilt + Compose
- A backend that issues SD-JWT VC tokens for verified emails
- Credential Manager 1.5.0+

## Workflow

### Step 1: Integration-point discovery

Before writing any code, search the project:

```
tool: Grep
args: { "pattern": "verifyEmail|emailVerified|FirebaseAuth.sendSignInLink|ActionCodeSettings", "path": "app/src/main/kotlin" }
```

If existing code, ask the user how to proceed. If none, proceed.

### Step 2: Wire Credential Manager with digital credentials

```kotlin
val credentialManager = CredentialManager.create(activity)

val origin = "android:apk-key-hash:<your-signing-cert-hash>"
val request = GetCredentialRequest.Builder()
    .addCredentialOption(
        DigitalCredentialOption.Builder()
            .setRequestJson("""{
                "type": "verified-email",
                "origin": "$origin"
            }""")
            .build()
    )
    .build()

val response = credentialManager.getCredential(activity, request)
```

### Step 3: Parse the SD-JWT VC

```kotlin
val cred = response.credential as DigitalCredential
val responseJson = cred.credentialJson
val token = JSONObject(responseJson).getString("token")
// token is an SD-JWT VC; send to backend
```

### Step 4: Backend exchange

```kotlin
suspend fun exchangeSdJwt(token: String): AuthResult {
    val res = authApi.exchangeSdJwt(token)
    return if (res.ok) AuthResult.Success(res.session) else AuthResult.Failure(res.error)
}
```

## Anti-patterns

- **DO NOT** write code without first searching for existing implementations.
- **DO NOT** log the SD-JWT token. Send it to the backend immediately.
- **DO NOT** use this for password-based accounts. Use android-auth.

## Pairing

- `android-auth` — for password-based flows
- `android-restore-credentials` — for new-device sign-in

## References

- See [references/integration-points.md](references/integration-points.md)
  for the full search-string list.
- See [references/sd-jwt-format.md](references/sd-jwt-format.md) for the
  SD-JWT VC structure your backend must issue.
