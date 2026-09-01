#!/usr/bin/env python3
"""
generate-host-wrappers.py — single source .mcp.json → host-specific configs.

Canonical: .mcp.json {mcpServers:{adb,gradlew,play-store,keystore,asset}} stdio.

Emits (Tier-1 simple):
  .vscode/mcp.json                  {servers:{}}  — VS Code Copilot trap
  .cursor/mcp.json                  {mcpServers:{}} (global also ~/.cursor/mcp.json)
  claude_desktop_config.example.json {mcpServers:{}} — copy to ~/Library/.../Claude/...
  gemini-extension.json             {name,version,mcpServers,...} — Gemini CLI → Antigravity
  .agents/skills/ is canonical; .github/skills/ is symlink instruction (not generated)

No drift: run --check in CI to fail if generated files stale or keys wrong.

Usage:
  python scripts/generate-host-wrappers.py              # generate
  python scripts/generate-host-wrappers.py --check      # verify (CI)
  python scripts/generate-host-wrappers.py --dry-run    # preview diff
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = ROOT / ".mcp.json"

# Hosts that need distinct key shapes — the 2026 trap matrix
HOSTS = {
    "vscode": {
        "path": ROOT / ".vscode" / "mcp.json",
        "key": "servers",  # VS Code: NOT mcpServers (silent fail)
        "wrap": lambda servers: {"servers": servers},
        "unwrap": lambda data: data.get("servers", {}),
    },
    "cursor": {
        "path": ROOT / ".cursor" / "mcp.json",
        "key": "mcpServers",
        "wrap": lambda servers: {"mcpServers": servers},
        "unwrap": lambda data: data.get("mcpServers", {}),
    },
    "claude-desktop": {
        "path": ROOT / "claude_desktop_config.example.json",
        "key": "mcpServers",
        "wrap": lambda servers: {"mcpServers": servers},
        "unwrap": lambda data: data.get("mcpServers", {}),
        "note": "Copy to ~/Library/Application Support/Claude/claude_desktop_config.json (macOS) | %APPDATA%\\Claude\\claude_desktop_config.json (Win) | ~/.config/Claude/claude_desktop_config.json (Linux), then restart Claude Desktop. Claude Code CLI uses .mcp.json directly.",
    },
    "gemini": {
        "path": ROOT / "gemini-extension.json",
        "key": "mcpServers",  # gemini-extension.json spec: top-level mcpServers
        "wrap": None,  # custom
        "unwrap": lambda data: data.get("mcpServers", {}),
    },
}


def load_canonical() -> dict:
    if not CANONICAL.exists():
        sys.exit(f"Missing canonical {CANONICAL}")
    data = json.loads(CANONICAL.read_text())
    # Accept both wrapped and direct forms
    if "mcpServers" in data:
        servers = data["mcpServers"]
    elif "servers" in data:
        servers = data["servers"]
    elif "mcp_servers" in data:
        servers = data["mcp_servers"]
    else:
        sys.exit(f"Canonical {CANONICAL} missing mcpServers/servers key: {list(data.keys())}")
    if not isinstance(servers, dict) or not servers:
        sys.exit(f"Canonical mcpServers must be non-empty object, got: {servers}")
    return servers


def _transform_env_for_host(servers: dict, host_id: str) -> dict:
    """Map PLAY_STORE_CACHE to host-appropriate variable."""
    import copy

    out = copy.deepcopy(servers)
    for srv_cfg in out.values():
        env = srv_cfg.get("env", {})
        if "PLAY_STORE_CACHE" in env:
            if host_id == "vscode":
                env["PLAY_STORE_CACHE"] = "${workspaceFolder}/.build-android/play-cache"
            else:
                # Codex/Claude/Cursor/Gemini use ${env:HOME} (all support ${env:VAR})
                env["PLAY_STORE_CACHE"] = "${env:HOME}/.cache/build-android-apps/play-cache"
    return out


def build_vscode(servers: dict) -> dict:
    # VS Code Copilot: {servers:{}} — must use ${workspaceFolder}
    return {"servers": _transform_env_for_host(servers, "vscode")}


def build_cursor(servers: dict) -> dict:
    return {"mcpServers": _transform_env_for_host(servers, "cursor")}


def build_claude_desktop(servers: dict) -> dict:
    # Claude Desktop: identical shape to canonical, but example file with comment guard
    return {"mcpServers": _transform_env_for_host(servers, "claude-desktop")}


def build_gemini_extension(servers: dict) -> dict:
    # gemini-extension.json is the Go successor (Antigravity) extension manifest.
    # Gemini CLI: gemini extensions install https://github.com/mitunmanav/build-android-apps
    # Antigravity CLI: same, shares harness. Keep minimal required fields.
    # Read version/name from .codex-plugin/plugin.json or fallback
    import textwrap

    plugin_json = ROOT / ".codex-plugin" / "plugin.json"
    name = "build-android-apps"
    version = "2.0.0"
    description = "Build and ship Android apps — 28 skills + 5 MCP servers"
    if plugin_json.exists():
        try:
            pj = json.loads(plugin_json.read_text())
            name = pj.get("name", name)
            version = pj.get("version", version)
            raw_desc = pj.get("description", description)
            # Word-boundary truncate to 200, no mid-word cut
            description = textwrap.shorten(raw_desc, width=197, placeholder="...")
        except Exception:
            pass
    return {
        "name": name,
        "version": version,
        "description": description,
        "author": {"name": "Mitun", "url": "https://github.com/mitunmanav"},
        "homepage": "https://github.com/mitunmanav/build-android-apps",
        "mcpServers": _transform_env_for_host(servers, "gemini"),
        "skills": "./skills/",
        "hooks": "./hooks/hooks.json",
    }


BUILDERS = {
    "vscode": build_vscode,
    "cursor": build_cursor,
    "claude-desktop": build_claude_desktop,
    "gemini": build_gemini_extension,
}


def generate(dry_run: bool = False) -> dict[str, pathlib.Path]:
    servers = load_canonical()
    generated: dict[str, pathlib.Path] = {}
    for host_id, cfg in HOSTS.items():
        builder = BUILDERS[host_id]
        data = builder(servers)
        path: pathlib.Path = cfg["path"]
        content = json.dumps(data, indent=2) + "\n"
        generated[host_id] = path
        if dry_run:
            if path.exists():
                existing = path.read_text()
                if existing != content:
                    print(f"[dry-run] {host_id}: {path} would change ({len(existing)}→{len(content)} bytes)")
                else:
                    print(f"[dry-run] {host_id}: {path} up to date")
            else:
                print(f"[dry-run] {host_id}: {path} would be created ({len(content)} bytes)")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"wrote {host_id}: {path} ({cfg['key']})")
    # Also ensure .vscode/settings.json hint for chat.mcp.enabled (not overwriting user settings)
    vscode_settings_hint = ROOT / ".vscode" / "settings.json.example"
    hint = {
        "_comment": "Copy to .vscode/settings.json or merge — enables MCP in VS Code Copilot",
        "chat.mcp.enabled": True,
        "chat.mcp.discovery.enabled": True,
    }
    if not dry_run:
        if not vscode_settings_hint.exists():
            vscode_settings_hint.write_text(json.dumps(hint, indent=2) + "\n")
            print(f"wrote hint: {vscode_settings_hint}")
    return generated


def check() -> int:
    """Exit 0 if all generated files match canonical, else 1 and print diff."""
    servers = load_canonical()
    ok = True
    for host_id, cfg in HOSTS.items():
        path: pathlib.Path = cfg["path"]
        builder = BUILDERS[host_id]
        expected = json.dumps(builder(servers), indent=2) + "\n"
        if not path.exists():
            print(f"✗ {host_id}: missing {path} — run python scripts/generate-host-wrappers.py")
            ok = False
            continue
        actual = path.read_text()
        if actual != expected:
            print(f"✗ {host_id}: {path} stale — run python scripts/generate-host-wrappers.py")
            # Show first diff line
            for i, (a, b) in enumerate(zip(actual.splitlines(), expected.splitlines()), 1):
                if a != b:
                    print(f"  line {i} actual:   {a!r}")
                    print(f"  line {i} expected: {b!r}")
                    break
            ok = False
        else:
            # Also validate key trap
            data = json.loads(actual)
            if host_id == "vscode" and "mcpServers" in data and "servers" not in data:
                print(f"✗ {host_id}: uses mcpServers but VS Code requires 'servers' — generator bug")
                ok = False
            elif host_id in ("cursor", "claude-desktop") and "servers" in data and "mcpServers" not in data:
                print(f"✗ {host_id}: uses servers but host requires 'mcpServers'")
                ok = False
            else:
                print(f"✓ {host_id}: {path} ok ({cfg['key']})")
    # Canonical itself must have mcpServers
    canon_data = json.loads(CANONICAL.read_text())
    if "mcpServers" not in canon_data:
        print(f"✗ canonical {CANONICAL} must have 'mcpServers' (not 'servers')")
        ok = False
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate host wrappers from .mcp.json")
    ap.add_argument("--check", action="store_true", help="verify generated files are up to date (CI)")
    ap.add_argument("--dry-run", action="store_true", help="preview without writing")
    args = ap.parse_args()
    if args.check:
        sys.exit(check())
    generate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
