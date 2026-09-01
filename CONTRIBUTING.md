# Contributing to build-android-apps

:v1: **Thank you.** Every contribution is welcome.

## Ground rules

1. **Author: Mitun only.** No `Co-authored-by:` footers. Commits reflect work done in this session; if you submit a PR from your own account with outside contributions, note it transparently in the PR body.
2. **Pass smoke locally before pushing.** Run `bash scripts/smoke.sh` — all 6 checks must green.
3. **Pass CI before merge.** The `smoke` workflow must pass on your PR branch.
4. **Scope discipline.** Change only what the task requires. No unsolicited refactors, no "clean up" of adjacent code, no adding features not in the spec.
5. **Keep the changelog current.** Add a single line under `[Unreleased]` for every user-facing change.

## What to work on

See the [v1.1 backlog](https://github.com/mitunmanav/build-android-apps/issues?q=label%3Av1.1) for planned work. Good first issues are tagged `good first issue`.

## Before you start

```
ASSUMPTIONS I'M MAKING:
1. You're working from a feature branch (not main)
2. You've run `bash scripts/smoke.sh` and it passes
3. Your change matches SPEC.md — if it doesn't, update SPEC.md first
→ Correct me now or I'll proceed with these.
```

## Commit style

This project uses **Conventional Commits** in spirit (not machine-enforced):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

| Type     | When to use                            |
|----------|----------------------------------------|
| `feat`   | New skill, command, or MCP server      |
| `fix`    | Bug fix in any module                  |
| `docs`   | README, CHANGELOG, inline docs         |
| `ci`     | Workflow or CI script changes           |
| `refactor` | Code restructuring (no behavior change |
| `chore`  | Dep updates, lockfile bumps            |

Examples:
```
feat(keystore-mcp): add rotate tool
fix(smoke): detect flat-layout MCP dirs
docs(readme): add compatibility table
ci(smoke): pip install mcp SDK before running
```

## PR checklist

- [ ] Branch is `feat/` or `fix/`, not `main`
- [ ] `bash scripts/smoke.sh` passes locally
- [ ] `smoke` CI passes on the PR
- [ ] CHANGELOG updated under `[Unreleased]`
- [ ] Any new skill has its `SKILL.md` and `references/` complete
- [ ] No `Co-authored-by:` footer added (per project rule)
- [ ] Docs updated if behavior changed

## Getting help

Open a **GitHub Discussion** (not an Issue) for design questions before submitting a large PR.

## License

By contributing, you agree your contribution is licensed under [Apache-2.0](LICENSE).
