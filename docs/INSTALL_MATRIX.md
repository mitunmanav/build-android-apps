# Install Matrix — All Hosts

One plugin, all hosts. Canonical source: `.mcp.json` (`mcpServers` object). Host wrappers generated via `scripts/generate-host-wrappers.py` — do not hand-edit.

| Host | Type | Config path | Key | Install |
|---|---|---|---|---|
| **Codex CLI** | CLI | `.codex-plugin/plugin.json` + `~/.codex/config.toml` | `mcpServers` | `codex plugin install github.com/mitunmanav/build-android-apps` |
| **Codex Desktop / App** | Desktop | same as CLI (shared harness) | `mcpServers` | same — restart app |
| **Claude Code CLI** | CLI | `<repo>/.mcp.json` + `~/.claude.json` | `mcpServers` | `claude plugin marketplace add mitun/mitun && claude plugin install build-android-apps@mitun` |
| **Claude Desktop** | Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) <br> `%APPDATA%\Claude\claude_desktop_config.json` (Win) <br> `~/.config/Claude/claude_desktop_config.json` (Linux) | `mcpServers` | Copy `claude_desktop_config.example.json` → path above, restart Desktop |
| **Cursor Desktop** | Desktop IDE | `.cursor/mcp.json` (project) / `~/.cursor/mcp.json` (global) | `mcpServers` | `git clone ... ~/.agents/plugins/build-android-apps` or Team Marketplace `Add Marketplace → https://github.com/mitunmanav/build-android-apps` — hot reload, no restart |
| **VS Code + Copilot** | Desktop IDE | `.vscode/mcp.json` | `servers` ⚠️ not `mcpServers` | Copy `.vscode/mcp.json`; enable `chat.mcp.enabled: true` in `.vscode/settings.json` (see `.vscode/settings.json.example`) |
| **Gemini CLI → Antigravity** | CLI → Desktop | `gemini-extension.json` at repo root | `mcpServers` | `gemini extensions install https://github.com/mitunmanav/build-android-apps` (Antigravity shares harness) |
| **.agents (any)** | Generic | `~/.agents/plugins/build-android-apps` + `AGENTS.md` | `mcpServers` + `AGENTS.md` | `git clone https://github.com/mitunmanav/build-android-apps ~/.agents/plugins/build-android-apps` — works for Copilot, Cursor, Gemini, OpenCode, Cline/Roo compat |
| **OpenCode** | CLI | `~/.config/opencode/opencode.json` `mcpServers` | `mcpServers` | `opencode` auto-loads `AGENTS.md` + `.mcp.json` via generator |

## Generating wrappers

```bash
python3 scripts/generate-host-wrappers.py          # generate all
python3 scripts/generate-host-wrappers.py --check  # CI check (fail if stale)
python3 scripts/generate-host-wrappers.py --dry-run # preview
```

## Common pitfalls

- **VS Code:** `mcpServers` silently fails — must be `servers`. Generator enforces.
- **Claude Desktop:** requires full restart after editing `claude_desktop_config.json`. Claude Code CLI hot-reloads.
- **Cursor:** `.cursor/mcp.json` project overrides global `~/.cursor/mcp.json`.
- **Gemini sunset:** After Jun 18 2026, `Gemini CLI` is replaced by `Antigravity CLI` — same `gemini-extension.json` works.

## More hosts (v1.1, docs only)

Zed `~/.config/zed/settings.json` `context_servers` via `mcp-remote`, Continue `~/.continue/config.json` array, Windsurf `~/.codeium/windsurf/mcp_config.json` `serverUrl`, JetBrains `Settings → Tools → MCP → Auto-Configure` — all can use `AGENTS.md` + `npx skills add` as fallback. See `research/` for 17-host matrix.

Verify: `bash scripts/smoke.sh` + `python3 scripts/generate-host-wrappers.py --check` must pass on PR.
