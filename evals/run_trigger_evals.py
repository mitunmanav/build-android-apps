#!/usr/bin/env python3
"""evals/run_trigger_evals.py — Tier 2 trigger & routing evals (zero-dep).

Loads every SKILL.md description (the agent's routing index) and checks the
case files in evals/cases/*.json:

- trigger.positive[]  : realistic user prompts; the named skill must rank
                        within top_k (default 3). Rank-1 rate is printed.
- trigger.negative[]  : prompts owned by ANOTHER skill; with "owner", the
                        runner asserts the owner outranks the skill — turning
                        the negative into a real pairwise routing test.
- catalog collision   : errors at >=75% pairwise description similarity,
                        warns at >=50% (agent-skills thresholds).

CI floor: --min-rank1 80. Raise the floor as routing improves; never lower
it to make a regression pass.

Usage:
    python3 evals/run_trigger_evals.py [--cases DIR] [--top-k 3] [--min-rank1 80]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

COLLISION_WARN = 0.50
COLLISION_ERROR = 0.75


def load_descriptions() -> dict[str, str]:
    """skill name -> frontmatter description text (parsed with yaml)."""
    import yaml
    out: dict[str, str] = {}
    for md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = md.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict):
            continue
        name, desc = fm.get("name"), fm.get("description", "")
        if name and desc:
            out[str(name)] = " ".join(str(desc).split())
    return out


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    """Light stemming: strip common suffixes so 'scrolling'~'scroll'."""
    out = []
    for t in TOKEN_RE.findall(text.lower()):
        if len(t) > 4 and t.endswith("ing"):
            t = t[:-3]
        elif len(t) > 4 and t.endswith("ed"):
            t = t[:-2]
        elif len(t) > 3 and t.endswith("es"):
            t = t[:-2]
        elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.append(t)
    return out


STOP = {
    "the", "a", "an", "to", "for", "of", "in", "on", "my", "is", "it",
    "and", "or", "with", "this", "that", "how", "do", "i", "me", "you",
    "can", "should", "what", "when", "where", "why", "app", "please",
}


def tfidf_vector(text: str, idf: dict[str, float]) -> dict[str, float]:
    vec: dict[str, float] = {}
    for t in tokens(text):
        if t in STOP:
            continue
        vec[t] = vec.get(t, 0.0) + 1.0
    for t in vec:
        vec[t] *= idf.get(t, 1.0)
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def build_ranker(descriptions: dict[str, str]):
    import collections
    df: collections.Counter = collections.Counter()
    for d in descriptions.values():
        df.update(set(t for t in tokens(d) if t not in STOP))
    n = max(len(descriptions), 1)
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
    vecs = {name: tfidf_vector(desc, idf) for name, desc in descriptions.items()}

    def rank(prompt: str) -> list[tuple[float, str]]:
        q = tfidf_vector(prompt, idf)
        scored = [(cosine(q, v), name) for name, v in vecs.items()]
        return sorted(scored, key=lambda x: -x[0])

    return rank


def similarity(a: str, b: str) -> float:
    ta, tb = set(tokens(a)) - STOP, set(tokens(b)) - STOP
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(Path(__file__).parent / "cases"))
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--min-rank1", type=int, default=80)
    ap.add_argument("--catalog-only", action="store_true")
    args = ap.parse_args()

    descriptions = load_descriptions()
    if not descriptions:
        print("FAIL: no SKILL.md descriptions loaded", file=sys.stderr)
        return 2
    rank = build_ranker(descriptions)
    failures: list[str] = []

    # ---- catalog collision check (all 29 descriptions) ----
    names = sorted(descriptions)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            s = similarity(descriptions[a], descriptions[b])
            if s >= COLLISION_ERROR:
                failures.append(f"collision {s:.0%} between {a} and {b} — differentiate the descriptions")
            elif s >= COLLISION_WARN:
                print(f"warn: {s:.0%} description similarity {a} / {b}")

    if not args.catalog_only:
        case_dir = Path(args.cases)
        files = sorted(case_dir.glob("*.json")) if case_dir.is_dir() else []
        if not files:
            failures.append("no eval case files found — every routing-critical skill needs one")
        pos_total = pos_rank1 = 0
        for cf in files:
            data = json.loads(cf.read_text(encoding="utf-8"))
            for p in data.get("positive", []):
                pos_total += 1
                ranked = [name for _, name in rank(p)]
                if data["skill"] in ranked[: args.top_k]:
                    if ranked[0] == data["skill"]:
                        pos_rank1 += 1
                else:
                    failures.append(
                        f"{cf.stem}: positive prompt not in top-{args.top_k}: {p!r} -> {ranked[:3]}"
                    )
            for p in data.get("negative", []):
                owner = p.get("owner", "")
                prompt = p["prompt"]
                ranked = [name for _, name in rank(prompt)]
                both = [r for r in ranked if r in (data["skill"], owner)]
                if len(both) < 2 or both[0] != owner:
                    failures.append(
                        f"{cf.stem}: owner {owner!r} must outrank {data['skill']!r} for {prompt!r} (got {ranked[:3]})"
                    )
        if pos_total:
            rate = round(100 * pos_rank1 / pos_total)
            print(f"trigger rank-1 rate: {rate}% ({pos_rank1}/{pos_total})")
            if rate < args.min_rank1:
                failures.append(f"rank-1 rate {rate}% < floor {args.min_rank1}%")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"OK: {len(names)} descriptions, collisions checked, routing cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
