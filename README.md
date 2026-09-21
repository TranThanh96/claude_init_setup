# claude_init_setup

Minimal boilerplate for a CLAUDE.md-based memory bank, meant to be dropped into
any project that uses a coding agent (Claude Code or similar).

## What's included

```
CLAUDE.md                          # always loaded — project overview, commands, rule includes
CLAUDE-activeContext.md            # current state snapshot, read at the start of a session
CLAUDE-decisions.md                # ADRs, read before a design/architecture decision
CLAUDE-patterns.md                 # project-specific code patterns
CLAUDE-troubleshooting.md          # known issues and fixes
.claude/rules/core-rules.md        # short project-specific behavior rules (always loaded)
.claude/rules/coding-guidelines.md # general LLM-coding guardrails (always loaded)
.claude/commands/update-memory-bank.md  # /update-memory-bank slash command
```

`patterns` and `troubleshooting` start empty and fill in as the project grows.

## Install the `init_agent` command

```bash
git clone https://github.com/TranThanh96/claude_init_setup.git ~/workspace/claude_init_setup
install -m 755 ~/workspace/claude_init_setup/init_agent.sh ~/.local/bin/init_agent
```

`init_agent` reads its template from `INIT_AGENT_TEMPLATE` (default:
`/u01/thanhtm/workspace/claude_init_setup` — set the env var if you clone it
elsewhere). Make sure `~/.local/bin` is on your `PATH`.

## Scaffold into a project

```bash
init_agent [target_dir]   # defaults to the current directory
```

Behavior:

- **New project / missing files:** copied as-is.
- **File already exists in target:** left untouched, never overwritten.
- **`CLAUDE.md` already exists:** not overwritten. The template version is staged
  at `.claude/CLAUDE.md.template` instead, and `init_agent` prints a ready-to-use
  prompt — hand it to your coding agent so it merges the `## Rules`, `## Memory
  Bank`, and `## Memory Rules` sections into the existing `CLAUDE.md` without
  touching the project-specific content already there, then deletes the staged
  template file. Merging markdown sections needs context the script doesn't
  have, so this step is left to the agent rather than done blindly by shell.

After scaffolding a genuinely new project, ask your coding agent to read the
codebase and fill in the `Overview` and `Commands` sections of `CLAUDE.md`, plus
an initial `CLAUDE-activeContext.md`. Review the result before committing.

## Usage

- **Start of session:** read `CLAUDE-activeContext.md` first (or let `CLAUDE.md`'s
  Memory Bank table remind the agent to).
- **During work:** use `.claude/rules/core-rules.md` and `coding-guidelines.md` as
  the behavior contract — read relevant code before changing it, keep changes
  surgical, define verifiable success criteria before looping.
- **Design decisions:** check `CLAUDE-decisions.md` first; add a new ADR when you
  make one. Superseded decisions are marked `superseded by ADR-00X`, never deleted.
- **After a bug fix:** add symptom/cause/fix to `CLAUDE-troubleshooting.md`.
- **End of a major task:** run `/update-memory-bank` to have the agent refresh
  `CLAUDE-activeContext.md` and append any new ADRs/patterns/troubleshooting notes.
- **Every ~2 weeks:** ask the agent to diff the memory bank against the actual
  code and remove anything stale.

## Memory rules

- Only record what can't be inferred from the code or git log.
- `CLAUDE-activeContext.md` is a snapshot — overwrite it, don't append a log.
- A new decision supersedes an old one; mark the old one superseded, don't delete it.
- As the project grows and `CLAUDE.md` gets long, move per-module descriptions to
  `src/<module>/CLAUDE.md` instead of piling them into the root file.
