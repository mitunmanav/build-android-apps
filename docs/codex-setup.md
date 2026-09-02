# Codex Setup

This repository is a [Codex plugin](https://developers.openai.com/codex/plugins). The same root-level `skills/` directory used by Claude Code is consumed by Codex — no files are copied or duplicated.

## Install (Codex CLI v0.122+)

```bash
codex plugin marketplace add mitunmanav/build-android-apps
codex plugin add build-android-apps@build-android-apps
```

> On older releases the command was `codex marketplace add`.

Local clones work too:

```bash
codex plugin marketplace add /path/to/your/clone
codex plugin add build-android-apps@build-android-apps
```

Start a new session after install so skills are discovered.

## Install (Codex desktop app, macOS / Windows)

1. Open **Plugins** in the sidebar.
2. Choose the `build-android-apps` marketplace source (or search the universal directory once published).
3. Click **+** next to Build Android App and follow the prompts.
4. Restart the app if the plugin was just added to a marketplace source.

The app picks up your CLI config, so MCP servers and plugin state carry over.

## How it works

| Path | What Codex reads |
|---|---|
| `.codex-plugin/plugin.json` | Manifest: `skills: ./skills/`, `mcpServers: ./.mcp.json`, `hooks: ./hooks/hooks.json` |
| `skills/<name>/SKILL.md` | One file serves Codex and Claude Code — same `name` + `description` frontmatter |
| `skills/<name>/agents/openai.yaml` | Codex-specific UI metadata, invocation policy, MCP dependencies |
| `.agents/plugins/marketplace.json` | Repo-scoped marketplace entry (source `./`) |
| `codex_config.example.toml` | Optional user-level `[mcp_servers.*]` tables for `~/.codex/config.toml` — not needed with the plugin route |

## Using it

- Invoke the frontdoor skill explicitly: `$build-android-apps` or `@build-android-apps`.
- Or just describe the task ("make a habit tracker with streaks") — the frontdoor is implicitly invokable and routes to 1 of 28 specialists.
- **Slash commands from `commands/` do not load on Codex.** There is no `commands` manifest key. Use the frontdoor skill instead — it routes to the same workflows.

## Hooks

The plugin bundles 5 lifecycle hooks (`hooks/hooks.json`). Codex skips plugin hooks until you review and trust them: run `/hooks` in the CLI, review the 5 handlers, and trust them. Codex records trust against the hook's hash — after a plugin update, re-review. Skills need no trust.

## MCP servers

Bundled via `.mcp.json` (stdio): `adb`, `gradlew`, `play-store`, `keystore`, `asset`. Bundling an `.mcp.json` marks the plugin **"Desktop only"** in the universal directory — expected, since stdio servers can't run on web. Tool approvals can be tuned per plugin in `config.toml` without editing the plugin.

## Verify

```bash
bash scripts/smoke.sh
python3 scripts/verify-install.py
python3 scripts/generate-host-wrappers.py --check
```
