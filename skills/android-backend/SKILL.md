---
name: android-backend
description: >
  Add a data layer (Room + DataStore) and a network layer (Retrofit + OkHttp)
  to an Android app. Includes pre-built templates for Supabase and Firebase
  backends. Use this when the user said "yes, sync between devices" in
  /make-app, or when they ask to add a database, save user data, or call a
  REST API. Do not use for analytics, push, or auth flows (use android-ops,
  android-auth) or for raw backend hosting (not in v1.0).
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [room, datastore, retrofit, okhttp, supabase, firebase, backend]
---

# Android Backend

> [!NOTE]
> Wire Room + DataStore + Retrofit. Pick Supabase or Firebase template.

## Prerequisites

- A scaffolded project (Phase 5 done)
- The user picked a backend during /make-app intake

## Workflow

### Step 1: Read the spec

Read `.build-android/spec.md` for `backend` field. Allowed values:

- `Supabase` → Postgres + Auth + Storage via supabase-kt
- `Firebase` → Firestore + Auth + Storage via firebase-kt
- `Both` → primary Firebase, secondary Supabase
- `On-device only` → exit; this skill doesn't apply

### Step 2: Add dependencies

Edit `gradle/libs.versions.toml`:

**Supabase:**
```toml
supabase-kt = { module = "io.github.jan-tennert.supabase:postgrest-kt", version = "3.0.0" }
supabase-auth = { module = "io.github.jan-tennert.supabase:auth-kt", version = "3.0.0" }
supabase-storage = { module = "io.github.jan-tennert.supabase:storage-kt", version = "3.0.0" }
```

**Firebase:**
```toml
firebase-bom = { module = "com.google.firebase:firebase-bom", version = "33.7.0" }
firebase-firestore = { module = "com.google.firebase:firebase-firestore-ktx" }
firebase-auth = { module = "com.google.firebase:firebase-auth-ktx" }
```

### Step 3: Data layer (Room)

Generate entities, DAOs, and database:

```kotlin
@Entity(tableName = "items")
data class Item(
    @PrimaryKey val id: String,
    val title: String,
    val createdAt: Long = System.currentTimeMillis()
)

@Dao interface ItemDao {
    @Query("SELECT * FROM items ORDER BY createdAt DESC") fun observeAll(): Flow<List<Item>>
    @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun upsert(item: Item)
    @Query("DELETE FROM items WHERE id = :id") suspend fun delete(id: String)
}

@Database(entities = [Item::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun items(): ItemDao
}
```

Provide via Hilt:

```kotlin
@Module @InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides @Singleton
    fun provideDatabase(@ApplicationContext ctx: Context): AppDatabase =
        Room.databaseBuilder(ctx, AppDatabase::class.java, "app.db").build()

    @Provides fun provideItemDao(db: AppDatabase): ItemDao = db.items()
}
```

### Step 4: Preferences (DataStore)

```kotlin
val Context.dataStore by preferencesDataStore("settings")
object PrefsKeys {
    val DARK_MODE = booleanPreferencesKey("dark_mode")
    val LAST_SYNC = longPreferencesKey("last_sync")
}
```

### Step 5: Network layer (Retrofit)

For Supabase, you usually skip Retrofit and use the Supabase client directly. For Firebase, you also skip Retrofit. Add Retrofit only when the user explicitly says "I have a custom REST API I need to call".

If needed:

```toml
retrofit = { module = "com.squareup.retrofit2:retrofit", version = "2.11.0" }
okhttp = { module = "com.squareup.okhttp3:okhttp", version = "4.12.0" }
okhttp-logging = { module = "com.squareup.okhttp3:logging-interceptor", version = "4.12.0" }
moshi = { module = "com.squareup.moshi:moshi-kotlin", version = "1.15.1" }
```

### Step 6: Wire account deletion endpoint

> [!IMPORTANT]
> If the app has accounts (login flow), Google Play Data Safety requires a way for users to request account deletion. See `android-auth/references/account-deletion.md` for the contract.

Add to your repository:

```kotlin
suspend fun deleteAccount() {
    api.deleteAccount()  // Supabase/Firebase admin SDK call from your backend
    auth.signOut()
    context.dataStore.edit { it.clear() }
    db.clearAllTables()
}
```

## Anti-patterns

- **DO NOT** store secrets (API keys) in the app. Use a backend proxy or the platform's secret manager.
- **DO NOT** access Room on the main thread. Wrap in `withContext(Dispatchers.IO)`.
- **DO NOT** forget to expose `deleteAccount()`. Play Store will reject the submission otherwise.
- **DO NOT** use `EncryptedSharedPreferences` for large blobs. Use Encrypted file storage.

## Pairing

- `android-auth` — sign-in flow
- `android-ops` — Crashlytics + Analytics on the same data
- `app-planner` — adds a "Set up data layer" task during planning

## References

- See [references/patterns.md](references/patterns.md) for full Right/Wrong
  code pairs (Room queries, Retrofit setup, Supabase client config).
