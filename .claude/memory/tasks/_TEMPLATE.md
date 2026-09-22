---
branch: <branch name>
updated: YYYY-MM-DD HH:MM
git_commit: <short sha at time of writing>
status: in-progress   # in-progress | blocked | done
---
<!-- One file per branch: tasks/<branch with / replaced by __>.md
     Snapshot for the NEXT session. Overwrite on every update. Budget: <= 60 lines.
     Delete this file in the PR that finishes the task (it has served its purpose;
     durable knowledge goes to ADRs / troubleshooting / patterns instead). -->
# Task: <one-line description>

## Goal & done criteria
- <what "done" means, verifiable: tests / behaviour>

## Status
- [x] <completed step>
- [ ] <next step>  ← resume here

## Key references
<!-- 2-5 file:line refs or plan/spec docs the next session must read first. -->
- `path/to/file.ext:10-40` — <why it matters>

## Learnings / dead ends
<!-- Approaches already tried that failed, and why. Saves the next session from repeating them. -->
- <...>
