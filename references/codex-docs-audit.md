# Codex Docs Audit — build-android-apps

> Verified 2026-09-01 against official sources only. Every row cites the doc URL that proves the claim.

## Sources fetched (official)

| # | Doc | URL |
|---|-----|-----|
| D1 | Skills & Plugins overview | https://developers.openai.com/codex/skills-and-plugins |
| D2 | Build skills | https://developers.openai.com/codex/build-skills |
| D3 | Build plugins | https://developers.openai.com/codex/build-plugins |
| D4 | Plugin architecture | https://developers.openai.com/plugins/concepts/plugins |
| D5 | Skills concept | https://developers.openai.com/plugins/concepts/skills |
| D6 | MCP server concept | https://developers.openai.com/plugins/concepts/mcp-server |
| D7 | Build MCP server | https://developers.openai.com/plugins/build/mcp-server |
| D8 | Package your plugin | https://developers.openai.com/plugins/build/plugins |
| D9 | Hooks | https://developers.openai.com/codex/hooks |
| D10 | Plugins (install/use) | https://developers.openai.com/codex/plugins |
| D11 | Skill Creator / Installer | https://developers.openai.com/codex/skills |
| D12 | AgentSkills spec | https://agentskills.io/specification |

## Progressive disclosure budget (the efficiency driver)

> **D2/D3:** Codex starts with `name + description` for every installed skill. Budget = **2% of context window OR 8,000 chars** (when unknown). If too many skills, **shortens descriptions first, then omits skills with warning**. Full `SKILL.md` only loaded when skill selected. [D2]

**Implication:** 27 skills × ~150-char avg description = ~4,050 chars + names ≈ 5k — within 8k but tight. 28 (with frontdoor) ≈ 5.3k. Frontdoor with `allow_implicit_invocation:true` + specialists `allow_implicit_invocation:false` keeps budget healthy: frontdoor always matches, specialists load lazily.

## Skill frontmatter — what is legal

| Field | Required | Constraint | Source |
|-------|----------|------------|--------|
| `name` | Yes | 1-64, `^[a-z0-9]+(-[a-z0-9]+)*$`, no leading/trailing `-`, no `--`, must match dir name | D12 |
| `description` | Yes | 1-1024, front-load trigger keywords (descriptions get shortened) | D2, D12 |
| `license` | No | string | D12 |
| `compatibility` | No | 1-500 | D12 |
| `metadata` | No | map string→string (arbitrary keys) | D12 |
| `allowed-tools` | No | space-separated string, **experimental** (support varies) | D12 |

**Verdict on current skills:** 10 files have top-level `platform`, `version`, `keywords` — **illegal** (not in D12). Must move into `metadata:` or drop. `allowed-tools` and `compatibility` are legal (contrary to earlier SPEC claim that they should be removed).

## Plugin manifest — what is legal

Per D8 (`Package your plugin`):

- Required entry: `.codex-plugin/plugin.json` with at least `name` (kebab-case, stable identifier), `version`, `description`.
- Optional pointers: `skills: "./skills/"`, `mcpServers: "./.mcp.json"`, `hooks: "./hooks/hooks.json"`, `apps: "./.app.json"` — **all must start `./` and stay inside plugin root**. D8: "Only `plugin.json` belongs in `.codex-plugin/`. Keep `skills/`, `hooks/`, `assets/`, `.mcp.json`, `.app.json` at plugin root." ✓ we do.
- Rich `interface.*` block (displayName, shortDescription, brandColor, defaultPrompt, logo, etc.) is valid for `plugins/build/plugins` manifest — D8 complete example includes it.
- Marketplace files: `~/.agents/plugins/marketplace.json` / `$REPO_ROOT/.agents/plugins/marketplace.json` — local marketplace JSON with `name`, `interface.displayName`, `plugins[{name, source{source,path}, policy{installation,authentication}, category}]`. D8 describes this shape. Legacy `~/.codex` paths also work.

**Current plugin:** `.codex-plugin/plugin.json` matches D8 rich manifest (name kebab, skills + mcpServers + interface). Needs rename only.

## Hooks — verified events & output

Per D9:

- Events: `SessionStart` (matcher: `startup|resume|clear|compact`), `SessionEnd`, `PreToolUse` (matcher: tool name e.g. `Bash`, `apply_patch`, `mcp__*`), `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop`. **No `PreSubmit`** event — our `hooks/hooks.json` uses invalid event name `PreSubmit` → must be `PreToolUse` with matcher `mcp__.*__submit_for_review|upload_aab`.
- Matchers are **regex strings**; `*`/`""`/omit = match all.
- `timeout` defaults 600s (SessionEnd default 1s, max 3s).
- Command hooks receive JSON on stdin (`session_id`, `cwd`, `hook_event_name`, `tool_input`, etc.), should emit JSON with `hookSpecificOutput{hookEventName, additionalContext|permissionDecision}` or Codex shape `{continue, stopReason, systemMessage}` depending on host. Our bash hooks emit `hookSpecificOutput` shape — valid per D9 for Claude compat, but Codex also accepts `PLUGIN_ROOT`.
- Plugin hook env vars: `PLUGIN_ROOT` / `PLUGIN_DATA` (canonical). `CLAUDE_PLUGIN_ROOT` is set **for compat**. D9: "Codex also sets `CLAUDE_PLUGIN_ROOT` for compatibility". Our hooks using only `CLAUDE_PLUGIN_ROOT` work via compat but should prefer `PLUGIN_ROOT`.
- `additionalContext` capped ~2,500 tokens default; `additionalContextLimit: 5000` raises it. Large output spilled to `<temp_dir>/hook_outputs/`.
- Plugin hooks live at `hooks/hooks.json` by default; if `hooks` field in manifest, that overrides default. Docs: "If you define `hooks` in `.codex-plugin/plugin.json`, Codex uses manifest entries instead of default `hooks/hooks.json`." We rely on default — correct.

## MCP server — verified

Per D6/D7:

- MCP server optional; can be skills-only, MCP-only, or both. D4 shape table confirms.
- MCP tools need `title`, `description`, `inputSchema`, `outputSchema`, `annotations{readOnlyHint, destructiveHint, openWorldHint}`.
- Transport: **streamable HTTP** for production public plugins; **stdio via `.mcp.json`** is the bundled-local pattern documented in D8. Our `stdio` with `mcp>=2.0` is correct for Codex CLI local.
- Server `instructions` (≤512 chars important part) guides tool sequence — we set it.
- `.mcp.json` can be direct map `{server: {command, args}}` or wrapped `{mcp_servers: {...}}` or `{mcpServers: {...}}`. D8 shows both direct and wrapped forms. Our `{"mcpServers": {adb:{command:python,args:[-m,adb_mcp]}}}` matches Claude shape; Codex also accepts `"mcpServers"` (verified via config).

## Packaging rules

- Marketplace `source.path` must start `./`, be relative to marketplace root, stay inside root. D8: "Keep `source.path` relative to the marketplace root, start it with `./`, and keep it inside that root." Our `.agents/plugins/marketplace.json` uses `./` — correct.
- Publishing: shared universal directory via submission portal. Local marketplace is separate authoring/testing source.

## Audit verdict → fixes queued

| # | Issue | Doc proof | Fix queued as |
|---|-------|-----------|---------------|
| F1 | `skills/*/SKILL.md` top-level `platform`/`version` illegal | D12: only name/description/license/compatibility/metadata/allowed-tools allowed | P4 |
| F2 | `hooks/hooks.json` event `PreSubmit` invalid | D9: valid events list has no PreSubmit | P5 |
| F3 | Hook env var `CLAUDE_PLUGIN_ROOT` only | D9: canonical is `PLUGIN_ROOT` + compat | P5 |
| F4 | Count drift: SPEC says 22/21/6 but actual 27/22/4 | D2 budget reasoning shows why 27 needs frontdoor | P1 |
| F5 | Plugin name is stable kebab-case identifier `build-android-apps` | D8: name is stable identifier, kebab-case | P2 (no-op, already correct) |
| F6 | Efficiency requires frontdoor due to 8k cap | D2: 2%/8k cap, shorten/omit warning | P3 |
| F7 | `allowed-tools` legal experimental — keep | D12: allowed-tools exists | P4 (keep, just format) |
| F8 | `.mcp.json` shape compatible | D8: both direct/wrapped accepted | Keep, just add missing servers to docs |

*P0–P5 applied as of 2026-09-02 (hooks env fallback, counts 30/28/4, frontdoor, manifests, keywords strings, stdio hook JSON). No version bump.*
