# Delegation Protocol — keep it cheap, keep it smart

## Rule: one specialist at a time

1. **Read the specialist's `SKILL.md` only after routing.** Do not preload references unless the specialist's Workflow explicitly says to.
2. **Execute the specialist's Workflow verbatim.** It already has prerequisites, steps, anti-patterns, and a checklist.
3. **Delegate to subagents via their `agents/*.md` when the specialist says to** (e.g., `build-validator`, `release-auditor`). Subagents write to `.scratch/<skill>-<uuid>/` and return `SUCCESS` + JSON file — do not inline full reports in chat (strict-output-limit pattern).
4. **After specialist finishes, run `python -m state where`** to confirm cursor advancement, then summarize.

## Example delegation

User: "add dark mode"

1. Frontdoor classifies → intent row 2 (`add`) → `python -m state add --title "Dark mode" --phase build --files ...`
2. Frontdoor runs `python -m state route --affected <new-id>` → shows affected phases.
3. Frontdoor loads `skills/material3-expressive/SKILL.md` (if dark mode is theming) or plain plan-mutator if generic.
4. Specialist runs, writes files, runs `gradlew` if needed.
5. Frontdoor: `python -m state done --task <id>` when step verified, then `where`.

## Anti-patterns

- ❌ Loading `compose-ui-patterns` + `material3-expressive` + `compose-performance-audit` together — pick one, finish, then next if needed.
- ❌ Running `gradlew clean` — blocked by `block-destructive.sh` PreToolUse.
- ❌ Dumping full R8 report in chat — use `.scratch/` + 30-line summary.

## Efficiency checklist

- [ ] Only one `SKILL.md` body in context at a time (frontdoor + one specialist).
- [ ] `references/` files only when explicitly needed.
- [ ] MCP calls via `mcp__plugin_build_android_apps_*` prefix (renamed from `*_app_plugin_*`).
- [ ] Subagent writes to `.scratch/`, chat gets summary.
