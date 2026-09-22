# <Project Name>

## Overview
- Goal: <1-2 sentences>
- Stack: <language/runtime, framework, database, ...>
- init- Architecture: <3-5 lines: main modules and data flow>

## Commands
- Install: `...`
- Test: `...`
- Lint/format: `...`
- Run local: `...`

## Rules
@.claude/rules/core-rules.md
@.claude/rules/coding-guidelines.md

## Memory Bank
The files below are NOT auto-loaded. Read them at the right time:

| File | Read when |
|---|---|
| CLAUDE-activeContext.md | At the start of every session |
| CLAUDE-decisions.md | Before making a design/architecture decision |
| CLAUDE-patterns.md | Before implementing a new feature |
| CLAUDE-troubleshooting.md | While debugging an issue |

## Memory Rules
- Only record what CANNOT be inferred from the code or git log.
- activeContext is a snapshot: overwrite it, don't append a log.
- A new decision supersedes an old one: mark the old one as superseded, don't delete it.
- Update the memory bank after every major task (use /update-memory-bank).
