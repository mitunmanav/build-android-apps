#!/usr/bin/env python3
"""End-to-end verification: install-readiness for Codex + Claude Code + .agents hosts.

Validates everything that can be checked without actually running a host.
Run from the plugin root: `python3 scripts/verify-install.py`
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

errors: list[str] = []
warnings: list[str] = []
checks: list[tuple[str, bool, str]] = []  # (name, passed, detail)


def check(name: str, passed: bool, detail: str = "") -> None:
    checks.append((name, passed, detail))
    if not passed:
        errors.append(f"{name}: {detail}")


def warn(msg: str) -> None:
    warnings.append(msg)


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)


# ---------- 1. Manifests ----------

def verify_manifests() -> None:
    section("1. Manifests")

    codex = ROOT / ".codex-plugin" / "plugin.json"
    claude = ROOT / ".claude-plugin" / "marketplace.json"
    agents = ROOT / ".agents" / "plugins" / "marketplace.json"
    mcp = ROOT / ".mcp.json"

    for p in [codex, claude, agents, mcp]:
        check(f"manifest exists: {p.name}", p.is_file(), f"not found: {p}")

    # Codex
    try:
        with codex.open() as f:
            m = json.load(f)
        required = ["name", "version", "description", "author", "interface", "skills", "mcpServers"]
        missing = [k for k in required if k not in m]
        check("Codex manifest has required fields", not missing, f"missing: {missing}")
        check("Codex manifest interface block", "interface" in m)
        for k in ["displayName", "shortDescription", "category", "capabilities", "defaultPrompt"]:
            check(f"Codex interface.{k}", k in m.get("interface", {}))
        def resolve(p: str) -> Path:
            p = p.lstrip("/")
            if p.startswith("./"):
                return ROOT / p[2:]
            return ROOT / p

        check("Codex skills path resolves", resolve(m["skills"]).is_dir(),
              f"{m['skills']} does not resolve")
        check("Codex mcpServers path resolves", resolve(m["mcpServers"]).is_file(),
              f"{m['mcpServers']} does not resolve")
    except Exception as e:
        check("Codex manifest parse", False, str(e))

    # Claude
    try:
        with claude.open() as f:
            m = json.load(f)
        check("Claude manifest has plugins[]", "plugins" in m and len(m["plugins"]) >= 1)
        check("Claude manifest has category", "category" in m)
    except Exception as e:
        check("Claude manifest parse", False, str(e))

    # .agents
    try:
        with agents.open() as f:
            m = json.load(f)
        check(".agents manifest has plugins[]", "plugins" in m and len(m["plugins"]) >= 1)
    except Exception as e:
        check(".agents manifest parse", False, str(e))

    # .mcp.json
    try:
        with mcp.open() as f:
            m = json.load(f)
        servers = m.get("mcpServers", {})
        check(".mcp.json has mcpServers", len(servers) >= 1)
        for name, srv in servers.items():
            check(f".mcp.json server '{name}' has command", "command" in srv)
            check(f".mcp.json server '{name}' has args", "args" in srv)
    except Exception as e:
        check(".mcp.json parse", False, str(e))


# ---------- 2. Skills ----------

def verify_skills() -> None:
    section("2. Skills (29 expected: 28 specialists + 1 frontdoor)")
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        check("skills/ exists", False, "missing")
        return
    check("skills/ exists", True)
    skill_dirs = sorted([p for p in skills_dir.iterdir() if p.is_dir()])
    check(f"29 skills (got {len(skill_dirs)})", len(skill_dirs) == 29, f"got {len(skill_dirs)} expected 29")

    NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    for sd in skill_dirs:
        md = sd / "SKILL.md"
        check(f"{sd.name}/SKILL.md", md.is_file())
        if not md.is_file():
            continue
        text = md.read_text()
        try:
            parts = text.split("---", 2)
            if len(parts) < 3:
                check(f"{sd.name} has frontmatter", False, "no --- delimiters")
                continue
            fm = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            check(f"{sd.name} frontmatter parses", False, str(e))
            continue
        check(f"{sd.name} has frontmatter", True)
        check(f"{sd.name} name valid", bool(NAME_RE.match(fm.get("name", ""))),
              f"name={fm.get('name')!r}")
        desc = fm.get("description", "")
        check(f"{sd.name} description present", bool(desc))
        check(f"{sd.name} description ≤1024", len(desc) <= 1024, f"len={len(desc)}")
        check(f"{sd.name} license present", "license" in fm)
        check(f"{sd.name} metadata present", "metadata" in fm)
        body_lines = parts[2].count("\n") + 1
        check(f"{sd.name} body ≤500 lines", body_lines <= 500, f"lines={body_lines}")
        oyaml = sd / "agents" / "openai.yaml"
        check(f"{sd.name}/agents/openai.yaml", oyaml.is_file())
        if oyaml.is_file():
            try:
                yaml.safe_load(oyaml.read_text())
                check(f"{sd.name} openai.yaml parses", True)
            except yaml.YAMLError as e:
                check(f"{sd.name} openai.yaml parses", False, str(e))


# ---------- 3. Slash commands ----------

def verify_commands() -> None:
    section("3. Slash commands (32 expected)")
    cmds_dir = ROOT / "commands"
    if not cmds_dir.is_dir():
        check("commands/ exists", False, "missing")
        return
    cmd_files = sorted(cmds_dir.glob("*.md"))
    check("32 commands", len(cmd_files) == 32, f"got {len(cmd_files)}")
    for f in cmd_files:
        text = f.read_text()
        parts = text.split("---", 2)
        if len(parts) < 3:
            check(f"{f.name} has frontmatter", False)
            continue
        try:
            fm = yaml.safe_load(parts[1])
            check(f"{f.name} frontmatter parses", True)
        except yaml.YAMLError as e:
            check(f"{f.name} frontmatter parses", False, str(e))
            continue
        check(f"{f.name} has description", "description" in fm)
        check(f"{f.name} has allowed-tools", "allowed-tools" in fm)
        # Verify all allowed-tools reference MCP servers in our plugin
        for tool in fm.get("allowed-tools", []):
            if tool.startswith("mcp__"):
                check(f"{f.name} tool name format", "mcp__plugin_build_android_apps_" in tool,
                      f"unexpected format: {tool}")


# ---------- 4. Subagents ----------

def verify_agents() -> None:
    section("4. Subagents (8 expected)")
    agents_dir = ROOT / "agents"
    if not agents_dir.is_dir():
        check("agents/ exists", False, "missing")
        return
    agent_files = sorted(agents_dir.glob("*.md"))
    check("8 subagents", len(agent_files) == 8, f"got {len(agent_files)}")
    for f in agent_files:
        text = f.read_text()
        parts = text.split("---", 2)
        if len(parts) < 3:
            check(f"{f.name} has frontmatter", False)
            continue
        try:
            fm = yaml.safe_load(parts[1])
            check(f"{f.name} frontmatter parses", True)
        except yaml.YAMLError as e:
            check(f"{f.name} frontmatter parses", False, str(e))
            continue
        for k in ("name", "description", "tools", "model"):
            check(f"{f.name} has {k}", k in fm)


# ---------- 5. Hooks ----------

def verify_hooks() -> None:
    section("5. Hooks (4 events, 6 handlers expected)")
    hjson = ROOT / "hooks" / "hooks.json"
    check("hooks/hooks.json", hjson.is_file())
    if not hjson.is_file():
        return
    try:
        h = json.loads(hjson.read_text())
    except json.JSONDecodeError as e:
        check("hooks.json parses", False, str(e))
        return
    events = list(h["hooks"].keys())
    expected = {"SessionStart", "PreToolUse", "PostToolUse", "Stop"}
    check("hooks.json has 4 expected events", set(events) == expected,
          f"got {events}, expected {expected}")
    # also verify handler counts: PreToolUse 2 (block + release-check), PostToolUse 2 (lint + slop-gate)
    pre_handlers = h["hooks"].get("PreToolUse", [])
    check("PreToolUse has 2 handlers (block + release-check)", len(pre_handlers) == 2,
          f"got {len(pre_handlers)}")
    post_handlers = h["hooks"].get("PostToolUse", [])
    check("PostToolUse has 2 handlers (lint + slop-gate)", len(post_handlers) == 2,
          f"got {len(post_handlers)}")

    # Check each script exists and is executable
    for ev, matchers in h["hooks"].items():
        for m in matchers:
            for hh in m["hooks"]:
                cmd = hh["command"]
                # ${CLAUDE_PLUGIN_ROOT}/hooks/X.sh -> hooks/X.sh
                parts = cmd.split("/hooks/")
                if len(parts) == 2:
                    script = ROOT / "hooks" / parts[1]
                    check(f"{ev} script {parts[1]} exists", script.is_file())
                    if script.is_file():
                        check(f"{ev} script {parts[1]} executable", os.access(script, os.X_OK))


# ---------- 6. MCP servers (stdio smoke) ----------

def verify_mcp_servers() -> None:
    section("6. MCP servers (stdio smoke)")

    async def smoke(name: str, module: str, src: str) -> tuple[bool, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", module,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONPATH": src},
            )
            init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "verify", "version": "0.1"}}}
            proc.stdin.write((json.dumps(init) + "\n").encode())
            await proc.stdin.drain()
            line = await asyncio.wait_for(proc.stdout.readline(), 5.0)
            if not line:
                return False, "no response"
            resp = json.loads(line)
            if "result" not in resp:
                return False, f"init failed: {resp}"

            proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n").encode())
            await proc.stdin.drain()
            proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n").encode())
            await proc.stdin.drain()
            line = await asyncio.wait_for(proc.stdout.readline(), 5.0)
            resp = json.loads(line)
            tools = resp.get("result", {}).get("tools", [])
            proc.terminate()
            await proc.wait()
            return True, f"{len(tools)} tools: {[t['name'] for t in tools]}"
        except Exception as e:
            try: proc.terminate(); await proc.wait()
            except Exception: pass
            return False, str(e)

    async def run_all():
        a = await smoke("adb-mcp", "adb_mcp", str(ROOT / "mcp-servers" / "adb-mcp" / "src"))
        g = await smoke("gradlew-mcp", "gradlew_mcp", str(ROOT / "mcp-servers" / "gradlew-mcp" / "src"))
        return a, g

    a, g = asyncio.run(run_all())
    check("adb-mcp stdio OK", a[0], a[1])
    check("gradlew-mcp stdio OK", g[0], g[1])


# ---------- 7. MCP server pytest ----------

def verify_mcp_tests() -> None:
    section("7. MCP server tests (pytest)")
    for srv in ["adb-mcp", "gradlew-mcp"]:
        srvdir = ROOT / "mcp-servers" / srv
        result = subprocess.run(
            ["pytest", "-q", "--tb=line"],
            cwd=str(srvdir), capture_output=True, text=True, timeout=60,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        passed = result.returncode == 0
        last = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
        check(f"{srv} pytest", passed, last or result.stderr.splitlines()[-1])


# ---------- Main ----------

def main() -> int:
    verify_manifests()
    verify_skills()
    verify_commands()
    verify_agents()
    verify_hooks()
    verify_mcp_servers()
    verify_mcp_tests()

    section("Summary")
    total = len(checks)
    passed = sum(1 for _, p, _ in checks if p)
    print(f"Passed: {passed}/{total}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        print("\nFAILED checks:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
