# Supabase template

## Setup

1. Create a Supabase project at https://supabase.com → copy the URL + anon key.
2. Add to `app/build.gradle.kts`:

   ```kotlin
   android {
       defaultConfig {
           buildConfigField("String", "SUPABASE_URL", "\"https://<your-project>.supabase.co\"")
           buildConfigField("String", "SUPABASE_ANON_KEY", "\"<your-anon-key>\"")
       }
   }
   dependencies {
       implementation(libs.supabase.postgrest)
       implementation(libs.supabase.auth)
       implementation(libs.supabase.storage)
   }
   ```

3. Copy `SupabaseModule.kt` into your project's `di/` package.
4. Inject `SupabaseClient` into repositories.

## Account deletion (Play Store Data Safety)

Create a Supabase Edge Function that:
1. Accepts the user's auth token.
2. Deletes the user from `auth.users` (cascades to your tables).
3. Deletes any storage objects owned by the user.
4. Returns 204.

Call from your app's `deleteAccount()` (in `android-auth`).

## RLS policies

Always enable Row Level Security on your tables:

```sql
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "owner_select" ON items FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "owner_insert" ON items FOR INSERT WITH CHECK (auth.uid() = user_id);
```

## What this template does NOT do

- Custom server-side business logic (use Supabase Edge Functions)
- Email sending (use Supabase Auth templates)
- Scheduled jobs (use Supabase pg_cron)
