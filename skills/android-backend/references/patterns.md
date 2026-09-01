# Backend patterns (android-backend)

Right vs Wrong code patterns for Room + DataStore + Retrofit. Adopt the Right patterns; reject the Wrong ones.

## Room queries

**Right** (suspend + Flow):
```kotlin
@Dao interface ItemDao {
    @Query("SELECT * FROM items WHERE id = :id")
    suspend fun getById(id: String): Item?
    @Query("SELECT * FROM items")
    fun observeAll(): Flow<List<Item>>
}
```

**Wrong** (blocking on main thread):
```kotlin
@Query("SELECT * FROM items") fun getAll(): List<Item>  // blocks UI
```

## DataStore

**Right** (typed, async):
```kotlin
val Context.dataStore by preferencesDataStore("settings")
suspend fun read(ctx: Context) = ctx.dataStore.data.first()[PrefsKeys.DARK_MODE] ?: false
```

**Wrong** (SharedPreferences):
```kotlin
SharedPreferences(ctx).getBoolean("dark_mode", false)  // not Flow, not safe
```

## Retrofit

**Right** (interface + suspend):
```kotlin
interface Api {
    @GET("items") suspend fun list(): List<ItemDto>
    @POST("items") suspend fun create(@Body item: ItemDto): ItemDto
}
```

**Wrong** (raw URL concat):
```kotlin
val url = "${BASE_URL}items?q=$query"  // no encoding, breaks on special chars
```

## Supabase client init

**Right**:
```kotlin
val client = createSupabaseClient(
    supabaseUrl = BuildConfig.SUPABASE_URL,
    supabaseKey = BuildConfig.SUPABASE_ANON_KEY,
) {
    install(Postgrest)
    install(Auth)
    install(Storage)
}
```

**Wrong** (hardcoded URL):
```kotlin
val client = createSupabaseClient("https://example.supabase.co", "eyJ...", ...)  // secret in source
```

## Firebase init

**Right** (use google-services plugin + google-services.json):
```kotlin
// Plugin applies Firebase init automatically
```

**Wrong** (manual init):
```kotlin
Firebase.initializeApp(this)  // duplicates what the plugin does
```
