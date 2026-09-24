---
paths:
  - ".claude/memory/**"
---
<!-- Path-scoped: loads only when Claude reads a memory file. The single source of
     memory-editing rules: other files point here instead of repeating them. -->
# Rules for editing project memory
- Record only what cannot be inferred from the code or git log (no directory trees, no commit summaries).
- `active.md` is local (gitignored) and a snapshot for the next session: overwrite it, never append a log.
  Delete it when the task is finished, after moving durable knowledge to the files below.
- `decisions.md`: newest first. When a decision is replaced, shrink the old entry to its heading with
  `— superseded by <newer heading>`, or delete it; `git log -p` keeps the full text.
- `troubleshooting.md`: symptom / cause / fix / file reference, max ~5 lines each. Delete entries a fix made obsolete.
- `patterns.md`: one canonical example file per pattern; no pasted code.
- Size budgets live in `scripts/memory-lint.py`. Over budget → merge or remove stale entries, don't just trim words.
- Prefer `path/to/file.ext:line` references over pasted code.
- A pattern or decision that applies to one module only goes in `.claude/rules/<module>.md` with
  `paths:` frontmatter for that module, not in the files above: it then loads only when that
  module's files are read, and the shared files keep only what applies project-wide.
