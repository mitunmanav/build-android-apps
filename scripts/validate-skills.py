#!/usr/bin/env python3
"""Minimal skills validator.

Enforces the open-standard agentskills.io frontmatter rules against
all SKILL.md files under ./skills/.

Rules (per https://agentskills.io/specification):
  - YAML frontmatter delimited by `---` lines
  - name: 1-64 chars; pattern ^[a-z0-9]+(-[a-z0-9]+)*$; no leading/trailing hyphen
  - description: 1-1024 chars
  - license: present (recommended)
  - metadata: block present (recommended)

Body rules:
  - File must parse as Markdown (we just check it's not empty and has a heading)
  - Should reference at most a small number of references/ files
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESC = 1024
MAX_BODY_LINES = 500


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body). Returns (None, text) if no frontmatter."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    fm_text = text[4:end]
    body = text[end + 5 :]
    try:
        return yaml.safe_load(fm_text), body
    except yaml.YAMLError:
        return None, body


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"{path}: not a file"]
    text = path.read_text()
    fm, body = parse_frontmatter(text)
    if fm is None:
        return [f"{path}: missing or invalid YAML frontmatter"]
    name = fm.get("name", "")
    if not isinstance(name, str) or not (1 <= len(name) <= MAX_NAME):
        errors.append(f"{path}: name length must be 1..{MAX_NAME} chars (got {len(name) if isinstance(name, str) else 'non-str'})")
    elif not NAME_RE.match(name):
        errors.append(f"{path}: name '{name}' does not match {NAME_RE.pattern}")
    desc = fm.get("description", "")
    if not isinstance(desc, str) or len(desc) < 1:
        errors.append(f"{path}: description missing")
    elif len(desc) > MAX_DESC:
        errors.append(f"{path}: description too long ({len(desc)} > {MAX_DESC} chars)")
    if "license" not in fm:
        errors.append(f"{path}: license field missing (recommended)")
    if "metadata" not in fm:
        errors.append(f"{path}: metadata block missing (recommended)")
    body_lines = body.count("\n") + 1
    if body_lines > MAX_BODY_LINES:
        errors.append(f"{path}: body too long ({body_lines} > {MAX_BODY_LINES} lines; split to references/)")
    if not body.lstrip().startswith("#"):
        errors.append(f"{path}: body should start with a top-level heading")
    return errors


def validate_plugin(root: Path) -> int:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print(f"ERROR: no skills/ dir at {skills_dir}", file=sys.stderr)
        return 1
    skill_dirs = sorted([p for p in skills_dir.iterdir() if p.is_dir()])
    if not skill_dirs:
        print(f"ERROR: no skill subdirs under {skills_dir}", file=sys.stderr)
        return 1
    all_errors: list[str] = []
    for sd in skill_dirs:
        skill_md = sd / "SKILL.md"
        errs = validate_skill(skill_md)
        all_errors.extend(errs)
        oyaml = sd / "agents" / "openai.yaml"
        if not oyaml.is_file():
            all_errors.append(f"{oyaml}: missing (Codex UI metadata)")
        else:
            try:
                yaml.safe_load(oyaml.read_text())
            except yaml.YAMLError as e:
                all_errors.append(f"{oyaml}: invalid YAML: {e}")
    print(f"Validated {len(skill_dirs)} skill dirs in {skills_dir}")
    for sd in skill_dirs:
        skill_md = sd / "SKILL.md"
        fm, _ = parse_frontmatter(skill_md.read_text()) if skill_md.is_file() else ({}, "")
        status = "OK" if not [e for e in all_errors if str(skill_md) in e] else "FAIL"
        nm = fm.get("name", "?") if fm else "?"
        print(f"  [{status}] {nm:<35} ({skill_md.stat().st_size:>5} bytes)")
    if all_errors:
        print("\nERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        return 1
    print("\nAll skills valid.")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sys.exit(validate_plugin(root))
