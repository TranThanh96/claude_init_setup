# claude_init_setup

**A memory bank for your coding agent — loaded by hooks, enforced by lint, in one command.**

Every new session, a coding agent starts from zero: no idea what you decided last week, which
patterns you settled on, what already broke and why, or where the current task stopped.
You re-explain, or the agent "remembers" wrong and quietly reinvents a decision you already made.

`claude_init_setup` adds four small memory files to your project. The one that matters at the
start of every session (what you were in the middle of) is **injected by a hook**, so the agent
can't skip it; the others are read when the task calls for them; a **linter** keeps them all
short and pointing at code that still exists.

**Requirements:** Claude Code, `git`, `python3` (standard library only — no `pip install`, no `jq`).

---

## 1. Install (once per machine)

```sh
curl -fsSL --create-dirs -o ~/.claude/commands/init-agent.md \
  https://raw.githubusercontent.com/TranThanh96/claude_init_setup/main/init-agent.md
```

That's all: it adds the `/init-agent` command to Claude Code. Nothing else is cloned or kept on
the machine — each run of `/init-agent` fetches the latest template from GitHub and keeps the
command itself up to date.
(No Claude Code? See [Without Claude Code](#without-claude-code).)

## 2. Add it to a project

1. Open Claude Code in the project and run `/init-agent`.
2. The installer copies the files that are missing and **never overwrites existing ones**. If
   the project already has a `CLAUDE.md` or `.claude/settings.json`, it stages a `.template`
   next to it; with `/init-agent`, Claude merges it and shows you the diff.
3. `/init-agent` then reads your code, build files and CI and proposes the `CLAUDE.md` sections:
   Overview, Commands, Gotchas. Check them: **Gotchas** — traps a new engineer would fall into —
   is the most valuable part.
4. It also proposes a `.claude/checks.json` built from the linters the project already uses,
   so Claude gets their errors right after each edit. Optional: accept or skip.
5. Commit. `.claude/memory/active.md` is added to `.gitignore` for you — it stays local.

The installer also sets up a git `pre-commit` hook (unless one already exists; then it prints
the one line to add to yours).

## 3. Check that it works

Open a **new** Claude Code session in the project:

- `/hooks` lists **SessionStart** and **PostToolUse** from *Project Settings*.
  (Plugins may add their own entries; those are fine.)
- `/context` lists each `.claude/rules/*.md` file once under Memory files.
- Ask Claude to "update memory", start another session, and ask "what was I working on?" —
  it should answer from `active.md` without reading anything.

## 4. Everyday workflow

| When | You do | Happens automatically |
| --- | --- | --- |
| Start a session (also `/clear`, resume, after compaction) | Nothing | The hook shows Claude `active.md`, when it was written, how many commits landed since, and how many files are uncommitted |
| While working | Nothing | Claude reads `decisions.md` before design choices, `patterns.md` before implementing, `troubleshooting.md` when debugging — the table in `CLAUDE.md` tells it when. Edits are linted if you set up `checks.json` |
| You stop, or reach a milestone | Say **"update memory"** (or `/update-memory-bank`) | Claude rewrites `active.md` and records any new decision, pattern or tricky fix; review `git diff -- .claude/memory/` |
| You commit | Nothing | The pre-commit hook **warns, never blocks**, if a memory file is over budget, cites a path that no longer exists, or memory hasn't been updated for a while |
| The task is done | Say "update memory" | Durable knowledge moves to the committed files; `active.md` is deleted |
| Every ~2 weeks | `/memory-audit` | Re-checks only entries whose cited files changed since the last audit, and proposes fixes for you to approve |

What `active.md` looks like — Claude writes it; you rarely edit it by hand:

```markdown
# Task: rate-limit the public API
## Goal & done criteria
- 429 after 100 req/min per key; `tests/test_ratelimit.py` passes
## Status
- [x] Token bucket in `src/api/ratelimit.py`
- [ ] Wire into `src/api/app.py` middleware  ← resume here
## Key references
- `src/api/app.py:40-75` — middleware order matters (auth must run first)
## Learnings / dead ends
- Redis INCR+EXPIRE races under load; switched to a Lua script
```

### What goes where

| You just… | Record it in | Shared? |
| --- | --- | --- |
| stopped mid-task | `.claude/memory/active.md` | No — local to this checkout |
| made a design choice others must follow | `.claude/memory/decisions.md` | Yes, committed |
| settled on "how we do X here" | `.claude/memory/patterns.md` | Yes |
| fixed a bug whose cause wasn't obvious | `.claude/memory/troubleshooting.md` | Yes |
| learned something true for one module only | `.claude/rules/<module>.md` with `paths:` | Yes — loads only when that module is touched |
| found a trap anyone would hit | the **Gotchas** section of `CLAUDE.md` | Yes — loaded every session |

You normally don't pick the file yourself: "update memory" does. Record only what the code and
git log can't tell you, and cite code as paths (`src/x.py:10`) rather than pasting it. The full
rules are in [`.claude/rules/memory-files.md`](.claude/rules/memory-files.md).

## 5. Keep it up to date

**Upgrade a project** that already has any version installed:

Run `/init-agent` in it again: it detects the existing install and upgrades.

| Files | On upgrade |
| --- | --- |
| Template-owned: hooks, scripts, the `update-memory-bank` and `memory-audit` skills, `memory-files.md`, `checks.example.json` | Replaced with the new version — **unless you have uncommitted changes in them**; those are listed and left alone (commit or stash, then re-run) |
| Yours: `CLAUDE.md`, `settings.json`, `core-rules.md`, `coding-guidelines.md`, everything in `.claude/memory/` | Never overwritten. `CLAUDE.md` / `settings.json` get a `.template` to merge |

Review with `git diff` and commit. Upgrading from an older layout (v1: `CLAUDE-*.md` in the root;
v2: `.claude/memory/tasks/`, `project-state.md`, `decisions/`) also prints a migration prompt for
Claude; nothing old is moved or deleted without your approval.

**Update `/init-agent` itself:** nothing to do. Every run fetches the latest template, and if
the command file has changed too, it replaces `~/.claude/commands/init-agent.md` with the new one.

## 6. Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| New session says "No work in progress is recorded" | Normal until the first "update memory", and after a task is finished |
| Claude doesn't know where the task stopped | `active.md` wasn't updated at the end of the last session. Say "update memory" before you stop |
| Pre-commit warns "N file(s) changed across M commit(s) since .claude/memory/ was last updated" | Say "update memory". Tune with `MEMORY_NUDGE_MIN_FILES` (default 3) and `MEMORY_NUDGE_MIN_COMMITS` (default 5); `0` turns a signal off |
| Pre-commit or lint reports "`src/…` does not exist" | A memory entry cites a moved or deleted file. Update the entry, or run `/memory-audit` |
| `active.md` disappeared | It's gitignored: `git clean -fdx` and removing the worktree delete it, and it doesn't sync across machines. Use `git clean -fd` to keep ignored files |
| Two sessions overwrite each other's `active.md` | They share one checkout. Give each parallel session its own `git worktree` |
| `/hooks` doesn't list the project hooks | Start a new session after installing; check `.claude/settings.json` is valid JSON |

---

## How it works

| What | Where | How it reaches the agent |
| --- | --- | --- |
| Overview, commands, gotchas, memory map | `CLAUDE.md` | Loaded every session, subagents included |
| Behaviour rules | `.claude/rules/*.md` | Loaded every session (no `@import` needed) |
| Rules for editing memory | `.claude/rules/memory-files.md` | Only when a memory file is read (`paths:`) |
| Work in progress | `.claude/memory/active.md` — local, gitignored | **SessionStart hook**, with its age and the uncommitted-file count |
| Decisions, patterns, known issues | `.claude/memory/{decisions,patterns,troubleshooting}.md` | Read on demand, per the "Read when" table in `CLAUDE.md` |
| Memory drift, over-budget files, dead references | `scripts/pre_commit_memory_check.py` | **git pre-commit hook**: warns, for any tool and any developer |
| Lint/type errors in edited files | `.claude/checks.json` | **PostToolUse hook** feeds failures back to Claude |
| Secrets, force-push, hard reset | `.claude/settings.json` | `permissions.deny` |
| Memory stays small and true | `scripts/memory-lint.py` | Size budgets, cited paths exist, every entry cites a file |

**Only one thing is forced into context.** Knowing what you were in the middle of can't be
optional, so a hook delivers it. Everything else is read on demand, so the default context stays
small as the project grows — module-specific knowledge goes in path-scoped rules that load only
when that module is touched.

**Why `active.md` is local.** It's a snapshot of *this checkout's* work, not project knowledge.
Each worktree gets its own, so parallel sessions in separate worktrees never collide, and there's
nothing to merge or clean up in a PR. What's worth keeping moves to the committed files.

**Why the memory map lives in `CLAUDE.md`.** Every agent loads it, subagents included. A
subagent doesn't get the SessionStart snapshot, so the map tells it to read `active.md` if the
task is unclear.

**Memory can be wrong; the code can't.** The injected snapshot says how old it is, the linter
flags citations of files that are gone, and `/memory-audit` re-checks entries whose code changed.
When memory and code disagree, Claude is told to trust the code.

### What's included

```
CLAUDE.md                               # always loaded: overview, commands, gotchas, memory map
.claude/settings.json                   # hooks + permissions.deny
.claude/checks.example.json             # per-glob fast checks for the PostToolUse hook
.claude/rules/core-rules.md             # always loaded
.claude/rules/coding-guidelines.md      # always loaded (karpathy-guidelines, MIT)
.claude/rules/memory-files.md           # path-scoped: the one source of memory-editing rules
.claude/hooks/session_start.py          # injects active.md, its age, uncommitted-file count
.claude/hooks/post_edit_check.py        # runs checks.json on each edited file
.claude/skills/update-memory-bank/      # "update memory" / /update-memory-bank
.claude/skills/memory-audit/            # /memory-audit
.claude/memory/                         # decisions.md, patterns.md, troubleshooting.md (+ local active.md)
scripts/memory-lint.py                  # budgets + reference checks (local, pre-commit, CI)
scripts/pre_commit_memory_check.py      # git pre-commit hook
```

### Optional: CI and pre-commit framework

In CI: `python3 scripts/memory-lint.py --strict` (warnings fail too).
With the [pre-commit](https://pre-commit.com) framework, add to `.pre-commit-config.yaml`:

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

## Without Claude Code

The installer is a plain bash script; `/init-agent` just runs it and then does the merging and
`CLAUDE.md` drafting for you. To use it directly:

```sh
git clone https://github.com/TranThanh96/claude_init_setup.git ~/workspace/claude_init_setup
ln -sf ~/workspace/claude_init_setup/init_agent.sh ~/.local/bin/init_agent   # a symlink, not a copy
init_agent path/to/project              # install
init_agent --upgrade path/to/project    # upgrade an existing install
git -C ~/workspace/claude_init_setup pull   # update the installer + template
```

Then do by hand what `/init-agent` would: merge any staged `*.template` files, fill in the
`CLAUDE.md` sections, and optionally copy `.claude/checks.example.json` to `.claude/checks.json`.

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

## Credits

- Flat memory-bank layout and the "read when" map from [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup).
- `coding-guidelines.md` from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT).
- Handoff snapshot inspired by HumanLayer's `create_handoff` / `resume_handoff` commands.
- Re-injecting context on `SessionStart` (including after compaction) follows the pattern used by [obra/superpowers](https://github.com/obra/superpowers).
