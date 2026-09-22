---
name: project-memory
description: Use before making a design or architecture decision, before implementing a new feature or module, and when debugging a failure whose cause is not obvious from the code. Reads this project's recorded decisions (ADRs), code patterns, and known issues from .claude/memory/.
user-invocable: false
---

# Project memory lookup

Pick the file for the situation. Read only what the task needs.

| Situation | Read |
| --- | --- |
| Design / architecture choice, changing a public interface, adding a dependency | `.claude/memory/decisions/INDEX.md`, then only the ADRs whose Scope overlaps the change |
| Implementing a new feature, endpoint, module, or test | `.claude/memory/patterns.md` |
| Bug, failing test, flaky behaviour, strange error | `.claude/memory/troubleshooting.md` |

## How to use what you find
- An **active** ADR is a constraint. If the planned change contradicts one, stop and tell the user
  which ADR conflicts and why, before writing code. Do not silently work around it.
- A **superseded** ADR is history: follow the ADR that superseded it.
- Memory can be stale. If a file reference in memory no longer matches the code, trust the code,
  and mention the stale entry so it gets fixed at the next `/update-memory-bank`.
- If nothing relevant is recorded, say so briefly and continue; don't invent project conventions.
