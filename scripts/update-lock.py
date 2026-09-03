#!/usr/bin/env python3
"""scripts/update-lock.py — regenerate plugin.lock.json.

Integrity scheme (documented, deterministic):
- file entry   (agents/*.md, commands/*.md, hooks/*.sh): sha256 of file bytes
- dir entry    (skills/<name>/): sha256 over the concatenation of each file's
  relative path + NUL + content, sorted by relative path (excluding
  .gitignore and __pycache__)

Usage: python3 scripts/update-lock.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".gitignore", "__pycache__"}


def file_integrity(p: Path) -> str:
    return "sha256-" + hashlib.sha256(p.read_bytes()).hexdigest()


def dir_integrity(d: Path) -> str:
    h = hashlib.sha256()
    files = sorted(
        f for f in d.rglob("*")
        if f.is_file() and not (set(f.parts) & SKIP)
    )
    for f in files:
        rel = f.relative_to(d).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(f.read_bytes())
    return "sha256-" + h.hexdigest()


def entry(id_: str, path: Path) -> dict:
    return {
        "id": id_,
        "vendoredPath": path.relative_to(ROOT).as_posix(),
        "integrity": dir_integrity(path) if path.is_dir() else file_integrity(path),
        "source": {
            "type": "github",
            "repo": "mitunmanav/build-android-apps",
            "path": path.relative_to(ROOT).as_posix(),
            "ref": "main",
        },
    }


def main() -> int:
    lock = json.loads((ROOT / "plugin.lock.json").read_text(encoding="utf-8"))
    lock["skills"] = [entry(d.name, d) for d in sorted((ROOT / "skills").glob("*/")) if (d / "SKILL.md").is_file()]
    lock["commands"] = [entry(f.stem, f) for f in sorted((ROOT / "commands").glob("*.md"))]
    lock["agents"] = [entry(f.stem, f) for f in sorted((ROOT / "agents").glob("*.md"))]
    lock["mcpServers"] = [entry(d.name, d) for d in sorted((ROOT / "mcp-servers").glob("*/")) if (d / "pyproject.toml").is_file()]
    lock["hooks"] = [
        {"id": f.stem, "integrity": file_integrity(f),
         "source": {"type": "github", "repo": "mitunmanav/build-android-apps",
                    "path": f"hooks/{f.name}", "ref": "main"}}
        for f in sorted(p for p in (ROOT / "hooks").iterdir() if p.is_file() and (p.suffix == ".sh" or p.name == "session-start"))
    ]
    lock["generatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (ROOT / "plugin.lock.json").write_text(
        json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"plugin.lock.json: {len(lock['skills'])} skills, {len(lock['commands'])} commands, "
          f"{len(lock['agents'])} agents, {len(lock['mcpServers'])} mcpServers, {len(lock['hooks'])} hooks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
