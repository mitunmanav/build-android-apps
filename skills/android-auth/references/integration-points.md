# Integration points (android-auth)

Search strings to find existing auth code before adding new code. Use these in `Grep` calls to detect legacy implementations.

## Legacy Google Sign-In

```
signInWithCredential
FirebaseAuth.getInstance
GoogleSignIn.getLastSignedInAccount
GoogleSignInAccount
```

## Legacy Facebook

```
LoginManager.getInstance
FacebookCallback
AccessToken.getCurrentAccessToken
```

## Legacy email/password

```
FirebaseAuth.signInWithEmailAndPassword
createUserWithEmailAndPassword
sendPasswordResetEmail
```

## Passkey

```
PublicKeyCredential
GetCredentialRequest
BeginGetCredentialOption
```

## What to do when found

1. If the legacy code is from another `auth` skill output, replace it.
2. If the legacy code is custom-written, ask the user before touching it.
3. If multiple are present (e.g., Firebase + Facebook), the user explicitly multi-auth'd — keep both.

## What to do when none are found

Proceed with the standard Credential Manager flow.
