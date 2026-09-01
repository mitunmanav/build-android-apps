# gradlew-mcp

MCP server wrapping Gradle (`./gradlew`) for AI agents.

## What it does

Exposes the Android Gradle build as typed MCP tools so an AI agent can:

- List all tasks (`./gradlew tasks --all`)
- Run a specific task (`./gradlew assembleDebug`)
- Parse dependencies (`:app:dependencies`)
- Run lint, tests, R8
- Verify keystore signing config

## Install

```bash
pip install -e ./mcp-servers/gradlew-mcp
```

## Run standalone (for debugging)

```bash
gradlew-mcp
# or
python -m gradlew_mcp
```

## Tools provided (this slice)

| Tool | Annotations | Purpose |
|---|---|---|
| `list_tasks` | read-only, idempotent | `./gradlew tasks --all` parsed into structured output |
| `run_task` | non-idempotent, long-running | `./gradlew <task>` |

More tools arrive in later slices. See SPEC.md §9 for the full list.

## Working directory

Tools default to the current working directory (`$PWD`). Set `cwd` per-call to override. The MCP host should be started from (or pass `cwd` explicitly pointing at) your Android project root.

## License

Apache-2.0.
