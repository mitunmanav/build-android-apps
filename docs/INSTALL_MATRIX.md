# Install Matrix — All Hosts

One plugin, all hosts. Canonical source: `.mcp.json` (`mcpServers` object). Host wrappers generated via `scripts/generate-host-wrappers.py` — do not hand-edit.

| Host | Type | Config path | Key | Install |
|---|---|---|---|---|
| **Codex CLI** (v0.122+) | CLI | `.codex-plugin/plugin.json` + `~/.codex/config.toml` | `[mcp_servers.*]` (TOML) | `codex plugin marketplace add mitunmanav/build-android-apps` then `codex plugin add build-android-apps@build-android-apps` — new session after install. Local clone: `codex plugin marketplace add /path/to/clone`. Invoke skills as `$build-android-apps` or `@build-android-apps` |
| **Codex Desktop / App** (macOS, Windows) | Desktop | same harness + config as CLI | `[mcp_servers.*]` (TOML) | App → Plugins sidebar → choose the `build-android-apps` marketplace source → `+` install → restart app. Bundling `.mcp.json` marks the plugin "Desktop only" (expected — stdio MCP can't run on web). Review and trust plugin hooks via `/hooks` in the CLI before they run |
| **Claude Code CLI** | CLI | `<repo>/.mcp.json` + `~/.claude.json` | `mcpServers` | `claude plugin marketplace add mitunmanav/build-android-apps && claude plugin install build-android-apps@build-android-apps` |
| **Claude Desktop** | Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) <br> `%APPDATA%\Claude\claude_desktop_config.json` (Win) <br> `~/.config/Claude/claude_desktop_config.json` (Linux) | `mcpServers` | Copy `claude_desktop_config.example.json` → path above, restart Desktop |
| **Cursor Desktop** | Desktop IDE | `.cursor/mcp.json` (project) / `~/.cursor/mcp.json` (global) | `mcpServers` | `git clone ... ~/.agents/plugins/build-android-apps` or Team Marketplace `Add Marketplace → https://github.com/mitunmanav/build-android-apps` — hot reload, no restart |
| **VS Code + Copilot** | Desktop IDE | `.vscode/mcp.json` | `servers` ⚠️ not `mcpServers` | Copy `.vscode/mcp.json`; enable `chat.mcp.enabled: true` in `.vscode/settings.json` (see `.vscode/settings.json.example`) |
| **Gemini CLI → Antigravity** | CLI → Desktop | `gemini-extension.json` at repo root | `mcpServers` | `gemini extensions install https://github.com/mitunmanav/build-android-apps` (Antigravity shares harness) |
| **.agents (any)** | Generic | `~/.agents/plugins/build-android-apps` + `AGENTS.md` | `mcpServers` + `AGENTS.md` | `git clone https://github.com/mitunmanav/build-android-apps ~/.agents/plugins/build-android-apps` — works for Copilot, Cursor, Gemini, OpenCode, Cline/Roo compat |
| **OpenCode** | CLI | `~/.config/opencode/opencode.json` `mcpServers` | `mcpServers` | `opencode` auto-loads `AGENTS.md` + `.mcp.json` directly (no generator entry; canonical `.mcp.json` is used as-is) |

## Generating wrappers

```bash
python3 scripts/generate-host-wrappers.py          # generate all
python3 scripts/generate-host-wrappers.py --check  # CI check (fail if stale)
python3 scripts/generate-host-wrappers.py --dry-run # preview
```

## Common pitfalls

- **Codex:** plugin hooks are skipped until you review and trust them (`/hooks` in the CLI) — Codex records trust against the hook hash, so updates re-trigger review. Skills need no trust.
- **Codex:** slash commands from `commands/` do not load on Codex (no `commands` manifest key exists). Use `$build-android-apps` / `@build-android-apps`; the frontdoor skill routes to the same workflows.
- **VS Code:** `mcpServers` silently fails — must be `servers`. Generator enforces.
- **Claude Desktop:** requires full restart after editing `claude_desktop_config.json`. Claude Code CLI hot-reloads.
- **Cursor:** `.cursor/mcp.json` project overrides global `~/.cursor/mcp.json`.
- **Gemini sunset:** After Jun 18 2026, `Gemini CLI` is replaced by `Antigravity CLI` — same `gemini-extension.json` works.

## More hosts (v1.1, docs only)

Zed `~/.config/zed/settings.json` `context_servers` via `mcp-remote`, Continue `~/.continue/config.json` array, Windsurf `~/.codeium/windsurf/mcp_config.json` `serverUrl`, JetBrains `Settings → Tools → MCP → Auto-Configure` — all can use `AGENTS.md` + `npx skills add` as fallback.

Verify: `bash scripts/smoke.sh` + `python3 scripts/generate-host-wrappers.py --check` must pass on PR.
