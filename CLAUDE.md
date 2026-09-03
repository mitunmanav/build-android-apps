# build-android-apps

This is the build-android-apps plugin — 29 skills (1 frontdoor + 28 specialists), 32 commands, 8 agents, 5 MCP servers.

## Project Structure

```
skills/       → 29 skills (SKILL.md per directory, frontdoor build-android-apps routes)
agents/       → 8 subagents (implementer, spec-reviewer, quality-reviewer, qa-user + 4 validators)
commands/     → 32 slash commands (all delegate to frontdoor)
references/   → per-skill checklists under skills/<name>/references/
hooks/        → SessionStart + PreToolUsex2 + PostToolUsex2 + Stop
mcp-servers/  → 5 Python stdio servers (adb, gradlew, play-store, keystore, asset)
```

## Conventions

- Every skill lives in `skills/<kebab-case-name>/SKILL.md` with `name` + `description` (<=1024 chars), body <=500 lines.
- Frontdoor only at startup; one specialist at a time.
- `state.json` is single source of truth; all mutations via `python -m state`.
