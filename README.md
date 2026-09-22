# claude_init_setup

**A memory bank for your coding agent — loaded by hooks, enforced by lint, in one command.**

Every new session, a coding agent starts from zero: no idea what you decided last week, which
patterns you settled on, what already broke and why, or where the task on this branch stopped.
You re-explain, or the agent "remembers" wrong and quietly reinvents a decision you already made.

`claude_init_setup` fixes that with a small, git-committed memory bank — and, unlike a pile of
markdown the agent is *asked* to read, the important parts are **delivered by hooks** and
**checked by a linter**, so they don't depend on the agent remembering instructions.

```
/init-agent
```

## Design: split memory by *when* it's needed, and by *who guarantees it*

| What | Where | How it reaches Claude | Guarantee |
| --- | --- | --- | --- |
| Project overview, commands, gotchas | `CLAUDE.md` (≤100 lines) | Loaded every session | Built-in |
| Behaviour rules | `.claude/rules/*.md` | Loaded every session (no `@import` needed) | Built-in |
| Rules for editing memory | `.claude/rules/memory-files.md` | Only when a memory file is read (`paths:`) | Built-in |
| Project snapshot | `.claude/memory/project-state.md` | **SessionStart hook**, also after `/compact` | Hook |
| This branch's task state | `.claude/memory/tasks/<branch>.md` | **SessionStart hook**, with "N commits since written" | Hook |
| Decisions (ADRs) | `.claude/memory/decisions/INDEX.md` + one file per ADR | `project-memory` skill, before design choices | Skill trigger |
| Patterns, known issues | `.claude/memory/patterns.md`, `troubleshooting.md` | `project-memory` skill, when implementing / debugging | Skill trigger |
| "Update memory before you forget" | — | **Stop hook**, once per session, only if code changed and memory didn't | Hook |
| Memory drift since last update, per commit | — | **`git pre-commit` hook**, from git log, any tool, any developer | Hook |
| Lint/type errors in edited files | `.claude/checks.json` | **PostToolUse hook** feeds failures back to Claude | Hook |
| Secrets, force-push, hard reset | `.claude/settings.json` | `permissions.deny` | Client-enforced |
| Memory stays small and consistent | `scripts/memory-lint.py` | Budgets, ADR index, orphaned task files | Lint / CI |

Why per-branch task files: a single "active context" file breaks as soon as you use more than one
branch, worktree, or agent at a time — sessions overwrite each other's snapshot. Project state and
task state also have different lifetimes, so they live in different files.

## What's included

```
CLAUDE.md                               # always loaded: overview, commands, gotchas, memory map
.claude/settings.json                   # hooks + permissions.deny
.claude/checks.example.json             # per-glob fast checks for the PostToolUse hook
.claude/rules/core-rules.md             # always loaded
.claude/rules/coding-guidelines.md      # always loaded (karpathy-guidelines, MIT)
.claude/rules/memory-files.md           # path-scoped: only when touching .claude/memory/
.claude/hooks/session_start.py          # injects project-state + tasks/<branch>.md, with staleness
.claude/hooks/stop_memory_nudge.py      # one-time nudge to update memory
.claude/hooks/post_edit_check.py        # runs checks.json on each edited file
.claude/hooks/session_end.py            # removes the per-session temp marker
.claude/skills/project-memory/          # auto-triggered: ADRs / patterns / troubleshooting lookup
.claude/skills/update-memory-bank/      # /update-memory-bank
.claude/skills/memory-audit/            # /memory-audit
.claude/memory/                         # the memory bank itself (committed, reviewed like code)
scripts/memory-lint.py                  # budgets + consistency checks (local, pre-commit, CI)
scripts/pre_commit_memory_check.py      # git pre-commit hook: warns on memory drift, any tool/dev
```

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
install -m 755 ~/workspace/claude_init_setup/init_agent.sh ~/.local/bin/init_agent
init_agent [target_dir]
```

Both never overwrite existing files. An existing `CLAUDE.md` or `.claude/settings.json` gets a
`.template` staged next to it plus a merge prompt. A v1 layout (`CLAUDE-*.md` in the root) is
detected and a migration prompt is printed; nothing is moved automatically.

## Daily usage

- **Start of session:** nothing to do. The hook injects project state and this branch's task file,
  and tells Claude how many commits have landed since each was written.
- **During work:** edits are checked by `checks.json`; the `project-memory` skill pulls in ADRs,
  patterns, or known issues when the task calls for them.
- **End of a task:** `/update-memory-bank` (the Stop hook will ask once if you forget). Review
  `git diff -- .claude/memory/` like any other change.
- **Every commit:** the git `pre-commit` hook warns (never blocks) if code has drifted from the
  last commit that touched `.claude/memory/` — by file count or by commit count, whichever crosses
  its threshold first. Catches the case a single-commit check misses: several small commits that
  each stay under the file threshold but add up to real drift. Fires for any commit, from any tool,
  not just inside Claude Code — so it still catches a teammate who isn't using Claude Code at all.
- **Task finished:** delete `tasks/<branch>.md` in the PR that lands it; durable knowledge has moved
  to ADRs / patterns / troubleshooting.
- **Every ~2 weeks or after a model upgrade:** `/memory-audit`.
- **CI (optional):** `python3 scripts/memory-lint.py --strict`.

Tuning: `MEMORY_NUDGE_MIN_FILES` (default 3, `0` disables the Stop nudge and the file-count signal
of the pre-commit warning) and `MEMORY_NUDGE_MIN_COMMITS` (default 5, `0` disables the commit-count
signal). Both `0` disables the pre-commit warning entirely.

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

- `/hooks` lists SessionStart, PostToolUse, Stop and SessionEnd from *Project Settings*.
- `/context` shows each `.claude/rules/*.md` file once (not twice) under Memory files.
- `/permissions` shows the `deny` rules from `.claude/settings.json`.
- The first reply of a new session on a branch with a task file knows where the task stopped.

## Developing this template

```
python3 -m unittest discover -s tests -v   # 30 end-to-end tests, stdlib only
python3 scripts/memory-lint.py
```

CI runs both on Linux and macOS (bash 3.2) with Python 3.9 and 3.12.

## Memory rules

- Record only what can't be inferred from the code or git log.
- Snapshots (`project-state.md`, `tasks/<branch>.md`) are overwritten, never appended.
- One file per ADR. Superseded, never deleted.
- Budgets are enforced; over budget means merge or delete stale entries, not trim words.
- Project knowledge goes in `.claude/memory/` (shared, reviewed). Claude's auto memory is for
  personal preferences.

## Credits

- Memory-bank layout inspired by [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup).
- `coding-guidelines.md` from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT).
- Commit-stamped handoffs inspired by HumanLayer's `create_handoff` / `resume_handoff` commands.
- Re-injecting context on `SessionStart` (including after compaction) follows the pattern used by [obra/superpowers](https://github.com/obra/superpowers).
