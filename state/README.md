# state/ — per-project state.json (build loop position)

## What this is

Single source of truth for "where is this project in the build loop?"
Lives at `<project>/.build-android/state.json` (created at runtime by
SessionStart or `/where` / `/make-app`). Gitignored per-project.

## Schema

`schema.json` is the contract. Current version: **2**. See `state.py`
for the field-by-field invariant checks (dependency-free).

## Why a dedicated module

The plugin uses many hosts (Codex, Claude Code, `.agents`). Each can
spawn many subagents. They all need to read/write the same file without
races. A single Python module with `load`/`save`/`validate`/`migrate`
gives every host and subagent a consistent API.

## Files

| File | Purpose |
|---|---|
| `schema.json` | JSON Schema for validation (jsonschema-compatible; optional) |
| `state.py` | load/save/validate; dependency-free |
| `migrate.py` | version migrations (v0→v1→v2) |
| `__init__.py` | re-exports public API |
| `__main__.py` | CLI: `python -m state <cmd> [args]` |

## CLI

```bash
# Print current state (or DEFAULT_STATE if file missing)
python -m state load /path/to/.build-android/state.json

# Write state.json (validates first)
python -m state save /path/to/state.json '{"schema_version":2,"phase":"intake","plan":[],"cursor":{"phase":"intake","task_id":""},"history":[]}'

# Validate existing file
python -m state validate /path/to/state.json

# Migrate older file to current version
python -m state migrate old.json new.json
```

## What this is NOT

- NOT only plan algebra. `state/manager.py` ships plan-mutator
  (`/add` `/remove` `/change` `/undo`) + orchestration ledger.
- NOT only the phase router. `state/router.py` ships Kahn's-algorithm deps resolver
  that reads `plan[].deps` and emits the minimal phase sequence.
- NOT only snapshots. `/import` snapshots go to
  `.build-android/snapshot-<ts>/`.
