---
name: android-ops
description: >
  Wire operational concerns: Firebase Cloud Messaging (push), Analytics,
  Background WorkManager jobs, and verify Crashlytics is wired. Use this
  when the user said "yes, push notifications" in /make-app, or asks to add
  analytics, scheduled background work, or to verify crash reporting. Do not
  use for auth (use android-auth), data layer (use android-backend), or media
  (use android-media).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [fcm, push, analytics, workmanager, crashlytics, ops]
---

# Android Ops

> [!NOTE]
> Wire FCM, Analytics, WorkManager. Verify Crashlytics. Silent by default
> for Crashlytics (added at scaffold time).

## Prerequisites

- A scaffolded project
- `google-services.json` at `app/google-services.json`
- The user picked `notifications: yes` during /make-app

## Workflow

### Step 1: Read the spec

Read `.build-android/spec.md` for `notifications` and any "background work" mentions.

### Step 2: FCM (push)

Add to `app/build.gradle.kts`:
```kotlin
implementation(libs.firebase.messaging)
```

Create `MyFirebaseMessagingService`:
```kotlin
@AndroidEntryPoint
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onMessageReceived(message: RemoteMessage) {
        val title = message.notification?.title ?: "Update"
        val body = message.notification?.body ?: ""
        showNotification(title, body)
    }
    override fun onNewToken(token: String) {
        // send to backend
    }
}
```

Register in `AndroidManifest.xml`:
```xml
<service
    android:name=".MyFirebaseMessagingService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

### Step 3: Analytics

Add to `app/build.gradle.kts`:
```kotlin
implementation(libs.firebase.analytics)
```

Log events:
```kotlin
Firebase.analytics.logEvent("screen_view") { param(FirebaseAnalytics.Param.SCREEN_NAME, screen) }
```

### Step 4: WorkManager

For background sync / scheduled tasks:

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted ctx: Context,
    @Assisted params: WorkerParameters,
    private val repo: ItemRepository,
) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result = try {
        repo.sync()
        Result.success()
    } catch (e: Exception) { Result.retry() }
}

// Schedule
val req = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
    .build()
WorkManager.getInstance(ctx).enqueueUniquePeriodicWork("sync", ExistingPeriodicWorkPolicy.KEEP, req)
```

### Step 5: Verify Crashlytics

Confirm `app/build.gradle.kts` has `id("com.google.firebase.crashlytics")`. Confirm `google-services.json` is at `app/google-services.json`. Confirm manifest has the `<meta-data android:name="com.google.firebase.crashlytics.enable" .../>` entry.

If any are missing, add them silently (per android-scaffold). Don't ask the user; they opted in.

### Step 6: Test push

Send a test message from Firebase Console → Cloud Messaging → New Campaign. Confirm the device receives it within 5 seconds.

## Anti-patterns

- **DO NOT** block the UI thread to wait for the FCM token. Fire-and-forget.
- **DO NOT** log PII in analytics events. Hash user ids; never log email or name.
- **DO NOT** enqueue WorkManager work without constraints (battery, network).
- **DO NOT** disable Crashlytics on debug builds. The whole point is to catch bugs early.

## Pairing

- `android-scaffold` — added Crashlytics at scaffold time
- `android-auth` — Firebase Auth tokens feed into FCM token refresh

## References

- See [references/fcm-payloads.md](references/fcm-payloads.md) for the
  payload format that survives Doze mode.
