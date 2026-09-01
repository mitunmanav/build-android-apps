package com.example.app.di

import android.content.Context
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.storage.Storage
import javax.inject.Singleton

/**
 * Supabase Hilt module — drop into your project's di/ package and add to
 * libs.versions.toml:
 *
 *   supabase-postgrest = { module = "io.github.jan-tennert.supabase:postgrest-kt", version = "3.0.0" }
 *   supabase-auth      = { module = "io.github.jan-tennert.supabase:auth-kt",      version = "3.0.0" }
 *   supabase-storage   = { module = "io.github.jan-tennert.supabase:storage-kt",   version = "3.0.0" }
 *
 * Then add `BuildConfig.SUPABASE_URL` and `BuildConfig.SUPABASE_ANON_KEY`
 * via `buildConfigField` in app/build.gradle.kts (do NOT hardcode these).
 */
@Module
@InstallIn(SingletonComponent::class)
object SupabaseModule {

    @Provides
    @Singleton
    fun provideSupabaseClient(): SupabaseClient = createSupabaseClient(
        supabaseUrl = BuildConfig.SUPABASE_URL,
        supabaseKey = BuildConfig.SUPABASE_ANON_KEY,
    ) {
        install(Postgrest)
        install(Auth)
        install(Storage)
    }
}
