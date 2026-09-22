---
paths:
  - ".claude/memory/**"
---
<!-- Path-scoped: loads only when Claude reads a memory file, so these rules
     cost nothing in sessions that never touch memory. -->
# Rules for editing project memory
- Record only what cannot be inferred from the code or git log (no directory trees, no commit summaries).
- `project-state.md` and `tasks/<branch>.md` are snapshots: overwrite them, never append a log.
- Decisions: one file per ADR (`decisions/ADR-NNN-slug.md`) plus one line in `decisions/INDEX.md`.
  Never delete an ADR; set `Status: superseded by ADR-NNN` and update the index line.
- `troubleshooting.md` entries: symptom / cause / fix / file reference, max ~5 lines each.
- Respect the size budgets in `scripts/memory-lint.py`. Over budget → merge or remove stale entries, don't just trim words.
- Prefer `path/to/file.ext:line` references over pasted code.
