<!--
  Always loaded, every session. Budget: <= 100 lines (checked by scripts/memory-lint.py).
  HTML comments like this one are stripped before Claude sees the file: use them
  for notes to human maintainers, they cost zero context.
  Put here only what Claude cannot infer from the code or git log.
-->

## Overview
<!-- 1-2 sentences: what this project is for and who uses it. -->
- Goal: <...>
- Stack: <language/runtime, framework, database>
<!-- Architecture: 3-5 lines on main modules and data flow. Delete if the
     directory structure already makes it obvious. -->
- Architecture: <...>

## Commands
<!-- Exact commands. In a monorepo, put per-module commands in <module>/CLAUDE.md. -->
- Install: `...`
- Test (all): `...`
- Test (one file): `...`
- Lint/format: `...`
- Run local: `...`

## Gotchas
<!-- Highest-value section. Traps a new engineer would fall into:
     invariants, generated files, public APIs that must not change,
     things that look wrong but are intentional. One line each. -->
- <...>

## Project memory
Committed project memory lives in `.claude/memory/`:

| File | Loaded |
| --- | --- |
| `project-state.md` | Injected at session start by a hook |
| `tasks/<branch>.md` | Injected at session start for the current branch |
| `decisions/INDEX.md` → `ADR-NNN-*.md` | On demand, via the `project-memory` skill |
| `troubleshooting.md`, `patterns.md` | On demand, via the `project-memory` skill |

- `.claude/memory/` holds shared project knowledge (reviewed like code).
  Claude's auto memory holds personal preferences only; project facts do not go there.
- Run `/update-memory-bank` at the end of a task; `/memory-audit` every ~2 weeks.
- When compacting, preserve: the list of modified files, test commands run and their results, and the current task file path.
