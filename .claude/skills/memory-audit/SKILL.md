---
name: memory-audit
description: Audit .claude/memory/ against the actual codebase — find stale claims, dead file references, orphaned task files, and over-budget files, then propose fixes.
disable-model-invocation: true
---

# Memory audit (run every ~2 weeks, or after a major refactor / model upgrade)

Do the checking in a subagent (Explore) where possible, so this session's context stays small.

## 1. Mechanical checks
- Run `python3 scripts/memory-lint.py`. It reports budgets, index consistency, orphaned task
  files, leftover placeholders, and duplicate rule imports.

## 2. Verify claims against code
For every entry in `patterns.md`, `troubleshooting.md`, active ADRs, and `project-state.md`:
- Do referenced files / symbols still exist? (`git ls-files`, grep, LSP if available)
- Does the described behaviour still match the code?
- Is a troubleshooting entry obsolete because the underlying cause was fixed?

## 3. Review always-loaded context
- `CLAUDE.md` and `.claude/rules/*.md` without `paths`: is every line still needed?
  A rule written to compensate for an older model's weakness may now just cost context.
  Test: "if I delete this line, would Claude make a mistake?" If not, propose deleting it.

## 4. Report — don't apply silently
Present a table: file · entry · problem · proposed action (update / delete / supersede).
Apply only what the user approves. Never delete an ADR; supersede it instead.
