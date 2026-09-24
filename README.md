# claude_init_setup

**A memory bank for your coding agent — loaded by hooks, enforced by lint, in one command.**

Every new session, a coding agent starts from zero: no idea what you decided last week, which
patterns you settled on, what already broke and why, or where the current task stopped.
You re-explain, or the agent "remembers" wrong and quietly reinvents a decision you already made.

`claude_init_setup` fixes that with four small memory files. Like
[centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup), it keeps
them flat and lets `CLAUDE.md` say which one to read when. Unlike a pile of markdown the agent is
only *asked* to read, the work-in-progress snapshot is **delivered by a hook** and the files are
**checked by a linter**, so continuity doesn't depend on the agent remembering instructions.

```
/init-agent
```

## Design: four files, one hook

| What | Where | How it reaches the agent |
| --- | --- | --- |
| Overview, commands, gotchas, memory map | `CLAUDE.md` (≤100 lines) | Loaded every session, subagents included |
| Behaviour rules | `.claude/rules/*.md` | Loaded every session (no `@import` needed) |
| Rules for editing memory | `.claude/rules/memory-files.md` | Only when a memory file is read (`paths:`) |
| Work in progress | `.claude/memory/active.md` — **local, gitignored** | **SessionStart hook** (startup, resume, `/clear`, after compaction), with its age and the uncommitted-file count |
| Decisions | `.claude/memory/decisions.md` | Read on demand: "before a design choice" row in `CLAUDE.md` |
| Patterns | `.claude/memory/patterns.md` | Read on demand: "before implementing" |
| Known issues | `.claude/memory/troubleshooting.md` | Read on demand: "when debugging" |
| Memory drift, over-budget files | `scripts/pre_commit_memory_check.py` | **git pre-commit hook**: warns, from any tool, any developer |
| Lint/type errors in edited files | `.claude/checks.json` | **PostToolUse hook** feeds failures back to Claude |
| Secrets, force-push, hard reset | `.claude/settings.json` | `permissions.deny` |
| Memory stays small and true | `scripts/memory-lint.py` | Budgets, cited paths exist, every entry cites a file, `active.md` gitignored (local / pre-commit / CI) |

Why `active.md` is gitignored: it is a snapshot of *this checkout's* work, not project knowledge.
Uncommitted, each worktree has its own, so parallel sessions in separate worktrees never overwrite
each other, and there's nothing to merge, conflict on, or delete in a PR. Anything worth keeping
moves to the three committed files.

The flip side: `active.md` doesn't follow you to another machine, and anything that deletes
ignored files deletes it too — `git clean -fdx` (use `-fd` to keep ignored files), or removing
the worktree it lives in. Before either, move anything worth keeping into the committed files,
or copy `active.md` somewhere safe.

Why the memory map lives in `CLAUDE.md`: every agent loads it, including subagents and sessions
that never trigger a skill. A subagent doesn't get the SessionStart snapshot, so the map tells it
to read `active.md` if the task is unclear.

## What's included

```
CLAUDE.md                               # always loaded: overview, commands, gotchas, memory map
.claude/settings.json                   # hooks + permissions.deny
.claude/checks.example.json             # per-glob fast checks for the PostToolUse hook
.claude/rules/core-rules.md             # always loaded
.claude/rules/coding-guidelines.md      # always loaded (karpathy-guidelines, MIT)
.claude/rules/memory-files.md           # path-scoped: the one source of memory-editing rules
.claude/hooks/session_start.py          # injects active.md, its age, uncommitted-file count
.claude/hooks/post_edit_check.py        # runs checks.json on each edited file
.claude/skills/update-memory-bank/      # /update-memory-bank (Claude may also run it at milestones)
.claude/skills/memory-audit/            # /memory-audit
.claude/memory/                         # decisions.md, patterns.md, troubleshooting.md (+ local active.md)
scripts/memory-lint.py                  # budgets + consistency checks (local, pre-commit, CI)
scripts/pre_commit_memory_check.py      # git pre-commit hook: warns on memory drift, any tool/dev
```

The installer also adds `.claude/memory/active.md` to the project's `.gitignore`.

`init_agent.sh` also installs `scripts/pre_commit_memory_check.py` as `.git/hooks/pre-commit`
(only if that file doesn't already exist — never overwritten; if it does, the installer prints the
one line to add to it or to your hook manager instead).

Hooks and the linter are Python 3 standard library only: no `jq`, no `pip install`.

## Quick start

**In Claude Code** — install the slash command once, then run it in any project:

```
mkdir -p ~/.claude/commands
curl -fsSL https://raw.githubusercontent.com/TranThanh96/claude_init_setup/main/init-agent.md \
  -o ~/.claude/commands/init-agent.md
```
```
/init-agent [target_dir]
```

**From a terminal:**

```
git clone https://github.com/TranThanh96/claude_init_setup.git ~/workspace/claude_init_setup
ln -sf ~/workspace/claude_init_setup/init_agent.sh ~/.local/bin/init_agent   # symlink, not a copy
init_agent [target_dir]
```

The symlink keeps script and template in one clone: `git -C ~/workspace/claude_init_setup pull`
updates both.

**Upgrading a project that already has it** (any older version):

```
init_agent --upgrade [target_dir]      # /init-agent does this by itself when it finds an install
```

`--upgrade` replaces the template-owned files — hooks, scripts, the two skills,
`memory-files.md`, `checks.example.json` — with the template's version, but only when they have
no uncommitted changes (those are listed and left alone; commit or stash, then re-run). Review
the result with `git diff`. User-owned files — `CLAUDE.md`, `settings.json`, `core-rules.md`,
`coding-guidelines.md`, and everything in `.claude/memory/` — are never overwritten. Without
`--upgrade`, the installer only says how many template files are out of date.

Otherwise the installer never overwrites existing files. An existing `CLAUDE.md` or `.claude/settings.json` gets a
`.template` staged next to it plus a merge prompt. An older layout — v1 (`CLAUDE-*.md` in the root)
or v2 (`.claude/memory/tasks/`, `project-state.md`, `decisions/`) — is detected and a migration
prompt is printed; nothing is moved automatically.

## Daily usage

- **Start of session:** nothing to do. The hook injects `active.md`, when it was written, how many
  commits landed since, and how many files are uncommitted.
- **During work:** edits are checked by `checks.json`; the memory map in `CLAUDE.md` points the
  agent at decisions, patterns, or known issues when the task calls for them.
- **Milestone or end of session:** `/update-memory-bank` (or ask Claude to "update memory").
  It overwrites `active.md` and records any new decision, pattern, or tricky fix. Review
  `git diff -- .claude/memory/` like any other change.
- **Every commit:** the git `pre-commit` hook warns (never blocks) if a memory file is over its
  budget, or if code has drifted from the last commit that touched `.claude/memory/`, by file
  count or by commit count.
- **Project grows:** a pattern or decision for one module goes in a path-scoped
  `.claude/rules/<module>.md`, so it loads only when that module is touched; the shared memory
  files keep only what applies project-wide. A replaced decision shrinks to one line or is deleted
  (git history keeps it).
- **Task finished:** `/update-memory-bank` moves what's durable into the committed files and
  deletes `active.md`.
- **Every ~2 weeks or after a model upgrade:** `/memory-audit`. It is incremental: it re-checks
  only entries whose cited files changed since the last `memory-audit:` commit, reading their diffs,
  never the whole codebase.
- **CI (optional):** `python3 scripts/memory-lint.py --strict`.

Tuning the pre-commit warning: `MEMORY_NUDGE_MIN_FILES` (default 3) and `MEMORY_NUDGE_MIN_COMMITS`
(default 5); `0` disables that signal, both `0` disables the drift warning (budget warnings stay).

**pre-commit (optional)** — add to the project's `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: memory-lint
      name: memory-lint
      entry: python3 scripts/memory-lint.py
      language: system
      pass_filenames: false
      files: ^(CLAUDE\.md|\.claude/)
```

## Verify in a real session

After installing, open Claude Code in the project and check:

- `/hooks` lists SessionStart and PostToolUse from *Project Settings*.
- `/context` shows each `.claude/rules/*.md` file once (not twice) under Memory files.
- `/permissions` shows the `deny` rules from `.claude/settings.json`.
- After `/update-memory-bank`, the first reply of a new session knows where the task stopped.

## Developing this template

```
python3 -m unittest discover -s tests -v   # end-to-end tests, stdlib only
python3 scripts/memory-lint.py
```

CI runs both on Linux and macOS (bash 3.2) with Python 3.9 and 3.12.

Every file here, `CLAUDE.md` and `.claude/memory/` included, is the template that `init_agent`
copies into other projects. Don't record this repo's own decisions, patterns, or fixes there:
they would ship to every installed project. Rationale belongs in this README and in commit
messages; `.claude/memory/active.md` is gitignored, so it is safe to use while working here.

## Memory rules

See [`.claude/rules/memory-files.md`](.claude/rules/memory-files.md), the single source; budgets
are in `scripts/memory-lint.py`.

## Credits

- Flat memory-bank layout and the "read when" map from [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup).
- `coding-guidelines.md` from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT).
- Handoff snapshot inspired by HumanLayer's `create_handoff` / `resume_handoff` commands.
- Re-injecting context on `SessionStart` (including after compaction) follows the pattern used by [obra/superpowers](https://github.com/obra/superpowers).
