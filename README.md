# claude_init_setup

**The guided install for a coding agent's memory bank, plus an optional ticket workflow — one
command, two independently-installable repos underneath.**

This repo carries no template files of its own. It's a thin orchestrator: `/init-agent` clones
whichever of the two repos below you need and delegates to their own `install.sh`.

| Repo | What it gives you | Standalone install |
| --- | --- | --- |
| [claude_memory_bank](https://github.com/TranThanh96/claude_memory_bank) | The agent remembers what it was doing, past decisions, patterns, and known issues — across sessions, compaction, and restarts. | `git clone` it and run its `install.sh` directly — no dependency on this repo. |
| [claude_ticket_workflow](https://github.com/TranThanh96/claude_ticket_workflow) | Spec-first planning for large features, and tickets you can delegate across Claude, Codex, and Antigravity. Assumes the memory bank above is already installed. | Same — `git clone` + `install.sh`, once the memory bank is in place. |

Each of those repos is public and guest-installable on its own. Use this repo when you want both
picked and wired up for you in one guided pass, with a merge/upgrade/migration flow handled by
Claude instead of by hand.

**Requirements:** Claude Code, `git`, `python3` (standard library only — no `pip install`, no `jq`).

---

## 1. Install (once per machine)

```sh
curl -fsSL --create-dirs -o ~/.claude/commands/init-agent.md \
  https://raw.githubusercontent.com/TranThanh96/claude_init_setup/main/init-agent.md
```

That's all: it adds the `/init-agent` command to Claude Code. Nothing else is cloned or kept on
the machine — each run of `/init-agent` fetches the latest orchestrator, and the two source
repos, from GitHub, and keeps the command itself up to date.
(No Claude Code? See [Without Claude Code](#without-claude-code).)

## 2. Add it to a project

1. Open Claude Code in the project and run `/init-agent`.
2. It asks which tier to install: **Core** (default — just the memory bank), or
   **Core + ticket workflow**. You can add the workflow tier later by running `/init-agent`
   again, so when in doubt, pick Core.
3. It clones [claude_memory_bank](https://github.com/TranThanh96/claude_memory_bank) (and, if you
   picked the workflow tier, [claude_ticket_workflow](https://github.com/TranThanh96/claude_ticket_workflow)
   too) and runs each one's own installer against your project. Files that already exist are
   staged as `<file>.template` next to the original, never overwritten silently.
4. `/init-agent` then reads your code, build files and CI and proposes the `CLAUDE.md` sections:
   Overview, Commands, Gotchas. Check them: **Gotchas** — traps a new engineer would fall into —
   is the most valuable part.
5. It also proposes a `.claude/checks.json` built from the linters the project already uses,
   so Claude gets their errors right after each edit. Optional: accept or skip.
6. Commit. `.claude/memory/active.md` is added to `.gitignore` for you — it stays local.

## 3. Check that it works, use it day to day, troubleshoot

All of that lives in the two source repos, since that's where the actual mechanics are:

- [claude_memory_bank's README](https://github.com/TranThanh96/claude_memory_bank#readme) —
  the everyday memory-bank workflow, what goes where, mechanics reference, troubleshooting.
- [claude_ticket_workflow's README](https://github.com/TranThanh96/claude_ticket_workflow#readme) —
  the skills, delegation across Claude/Codex/Antigravity, ticket status.

## 4. Keep it up to date

Run `/init-agent` again in a project that already has any version installed: it detects the
existing install and upgrades, keeping whichever tier is already there (a project with the
workflow tier stays on it; a core-only project stays core-only unless you now say yes to the
workflow question). Template-owned files are replaced with the new version — unless you have
uncommitted changes in them, in which case they're listed and left alone. Your own files
(`CLAUDE.md`, `settings.json`, `core-rules.md`, `coding-guidelines.md`, everything in
`.claude/memory/`) are never overwritten.

**Update `/init-agent` itself:** nothing to do. Every run fetches the latest orchestrator and
source repos, and if the command file has changed too, it replaces
`~/.claude/commands/init-agent.md` with the new one.

## Without Claude Code

The orchestrator is a plain bash script; `/init-agent` just runs it and then does the merging and
`CLAUDE.md` drafting for you. To use it directly:

```sh
git clone https://github.com/TranThanh96/claude_init_setup.git ~/workspace/claude_init_setup
ln -sf ~/workspace/claude_init_setup/init_agent.sh ~/.local/bin/init_agent   # a symlink, not a copy
init_agent path/to/project                            # install: core tier only
init_agent --with-workflow path/to/project            # install: core + ticket workflow
init_agent --upgrade path/to/project                  # upgrade an existing install (keeps its tier)
```

Or skip this repo entirely and install one or both source repos yourself — see their own READMEs
linked above.

Then do by hand what `/init-agent` would: merge any staged `*.template` files, fill in the
`CLAUDE.md` sections, and optionally copy `.claude/checks.example.json` to `.claude/checks.json`.

## Developing this repo

```
python3 -m unittest discover -s tests -v   # end-to-end tests, stdlib only
```

CI runs on Linux and macOS (bash 3.2) with Python 3.9 and 3.12. Tests point the orchestrator at
local checkouts of the two source repos via `INIT_AGENT_MEMORY_BANK_REPO` /
`INIT_AGENT_TICKET_WORKFLOW_REPO` env vars, so they never hit the network.

This repo only orchestrates; it has no template content of its own to keep in sync with what it
ships. Changes to the memory bank or the ticket workflow happen in their own repos.
