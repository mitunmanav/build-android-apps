# Firebase template

## Setup

1. Create a Firebase project at https://console.firebase.google.com → Add Android app.
2. Download `google-services.json` and place at `app/google-services.json` (do NOT commit it).
3. Add to `gradle/libs.versions.toml`:

   ```toml
   firebase-bom = { module = "com.google.firebase:firebase-bom", version = "33.7.0" }
   firebase-firestore = { module = "com.google.firebase:firebase-firestore-ktx" }
   firebase-auth = { module = "com.google.firebase:firebase-auth-ktx" }
   firebase-messaging = { module = "com.google.firebase:firebase-messaging-ktx" }
   firebase-analytics = { module = "com.google.firebase:firebase-analytics-ktx" }
   firebase-crashlytics = { module = "com.google.firebase:firebase-crashlytics-ktx" }
   ```

4. The `com.google.gms.google-services` and `com.google.firebase.crashlytics` plugins are already applied by `android-scaffold`.

## Common gotchas

- `google-services.json` MUST match the package name in `applicationId`. Mismatch → "Default FirebaseApp is not initialized".
- Each flavor (debug/release) can have its own `google-services.json`. Drop them in `src/debug/google-services.json` and `src/release/google-services.json` if you want different projects per flavor.
- Crashlytics upload of proguard mapping is automatic via the plugin.

## Account deletion (Play Store Data Safety)

Firebase Auth doesn't delete on the client. You need a Cloud Function:

```js
exports.deleteUser = functions.https.onCall(async (data, context) => {
  await admin.auth().deleteUser(context.auth.uid);
  await admin.firestore().collection('users').doc(context.auth.uid).delete();
});
```

Call from your app's `deleteAccount()` (in `android-auth`).

## What this template does NOT do

- BigQuery export (manual setup in console)
- Custom ML model hosting (use Firebase ML)
- A/B testing (manual setup)
