# Foreign-tool fingerprints (android-importer)

How to detect projects from specific AI code generators. None of this is documented officially; we infer from default files + structure.

## Lovable

- **Indicator**: `lovable.json` or `lovable.config.json` in project root
- **Default structure**: Vite + React frontend, Supabase backend, no Android
- **Action**: User almost certainly pasted a web project. Stop and ask if they meant to build an Android version instead.

## Bolt.new

- **Indicator**: `bolt.yaml` or `bolt.json`
- **Default structure**: Web app; usually not Android
- **Action**: Same as Lovable. Confirm intent.

## v0.dev

- **Indicator**: Generated React/Tailwind components; `package.json` shows `next` or `react`
- **Default structure**: Web app
- **Action**: Same.

## ChatGPT (Code Interpreter)

- **Indicator**: No specific marker; usually a single `.py` or `.html` file
- **Action**: If user has a folder of Android files, ask: "Did ChatGPT generate this, or are these your own?"

## Cursor / Cline

- **Indicator**: `.cursorrules` or `.clinerules` in root
- **Default structure**: Whatever the user is building; could be Android
- **Action**: Standard import flow. These tools produce native Android projects if asked.

## Other (generic)

- **Indicator**: Just a folder with `settings.gradle.kts` + `app/`
- **Action**: Standard import flow. Don't guess the origin.

## Detection priority

1. Check `settings.gradle.kts` and `app/build.gradle.kts` first.
2. If those exist and look like Android, proceed.
3. If they exist but look like web (e.g. references to `npm` or `next`), warn the user.
4. If they don't exist, ask the user if this is the right folder.
