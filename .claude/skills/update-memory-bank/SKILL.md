---
name: update-memory-bank
description: Update .claude/memory/ with durable knowledge from this session — task snapshot, ADRs, patterns, known issues.
disable-model-invocation: true
---

# Update the memory bank

Goal: the next session, starting from a clean context, can continue this work without
re-discovering anything. Record only what cannot be inferred from the code or git log.

## 1. Gather facts (don't rely on conversation memory alone)
- `git rev-parse --abbrev-ref HEAD` and `git rev-parse --short HEAD`
- `git status --short` and `git diff --stat` (plus `git log --oneline -10` if commits were made)

## 2. Task snapshot — `.claude/memory/tasks/<branch>.md`
Branch `feature/x` → file `feature__x.md`. Start from `tasks/_TEMPLATE.md` if it doesn't exist.
- **Overwrite** it (it's a snapshot, not a log). Update frontmatter `updated` and `git_commit`.
- Status checklist: mark finished steps, put `← resume here` on the next one.
- Learnings / dead ends: approaches that failed and why. This is the most valuable section.
- If the task is finished: set `status: done` and tell the user the file should be deleted
  in the PR that lands the work, after durable knowledge is moved to the files below.

## 3. Durable knowledge (only if this session produced some)
- **Decision made?** New `decisions/ADR-NNN-slug.md` from `ADR-000-template.md` + one line in
  `decisions/INDEX.md`. Replacing an old decision: mark the old ADR `superseded by ADR-NNN`, never delete it.
- **Tricky bug fixed?** Add symptom / cause / fix / file ref to `troubleshooting.md`.
- **Recurring pattern established?** Add it to `patterns.md` with one canonical example file.
- **Project-level change** (new focus, constraint, notable landing)? Overwrite `project-state.md`.
  Per-task detail never goes there.

## 4. Verify and report
- Run `python3 scripts/memory-lint.py`. Fix every error; merge or remove entries if over budget.
- Show the user `git diff -- .claude/memory/` so they can review the memory changes like code.
- Summarise in 3-5 lines what was recorded and where.
