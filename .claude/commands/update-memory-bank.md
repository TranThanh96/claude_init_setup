Update the memory bank based on this session's work:

1. Overwrite CLAUDE-activeContext.md with the current state (don't append).
2. If there's a new design decision → add an ADR to CLAUDE-decisions.md.
3. If a recurring pattern was found → add it to CLAUDE-patterns.md.
4. If a tricky bug was fixed → add it to CLAUDE-troubleshooting.md (symptom, cause, fix).
5. DO NOT record: directory structure, commit history, anything already clear from the code.
6. Re-read each file after editing to confirm the changes were saved.
7. Give a short summary of what was updated.
