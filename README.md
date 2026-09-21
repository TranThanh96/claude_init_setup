# claude_init_setup

**A memory bank for your coding agent, in one command.**

Every new session, a coding agent starts from zero: no idea what you decided
last week, no idea which patterns you settled on, no idea what already broke
and why. You end up re-explaining the same context over and over — or the
agent "remembers" wrong and quietly reinvents a decision you already made.

`claude_init_setup` fixes that with a tiny, git-committed memory bank:
a `CLAUDE.md` the agent always reads, plus a handful of files it reads only
when it matters (start of session, before a design call, while debugging).
One command scaffolds it into a brand-new project — or merges it into a
project that already has a `CLAUDE.md`, without touching what's already there.

```
/init-agent
```

That's the whole install for the common case. Read on for what it does and why.

## Why this instead of a giant CLAUDE.md

Most projects either have no persistent memory at all, or one CLAUDE.md file
that keeps growing until nobody trusts it's still accurate. This repo splits
memory by *when it should be read*, not by topic, so the agent's context stays
small and the always-loaded file stays under 100 lines:

| File | Read when | Loaded by default? |
|---|---|---|
| `CLAUDE.md` | Every session | Yes |
| `.claude/rules/core-rules.md` | Every session | Yes (via `@import`) |
| `.claude/rules/coding-guidelines.md` | Every session | Yes (via `@import`) |
| `CLAUDE-activeContext.md` | Start of session | On request |
| `CLAUDE-decisions.md` | Before a design/architecture decision | On request |
| `CLAUDE-patterns.md` | Before implementing a new feature | On request |
| `CLAUDE-troubleshooting.md` | While debugging | On request |

`patterns` and `troubleshooting` start empty and fill in as the project grows.
Decisions are never deleted, only superseded — so the history of *why* stays
intact instead of getting silently overwritten.

## Quick start

**Already in Claude Code?** Install the slash command once:

```bash
mkdir -p ~/.claude/commands
curl -fsSL https://raw.githubusercontent.com/TranThanh96/claude_init_setup/main/init-agent.md \
  -o ~/.claude/commands/init-agent.md
```

Then, in any project:

```
/init-agent
```

It clones this repo, drops in whatever files are missing, and — if the
project already has a `CLAUDE.md` — merges the Rules/Memory Bank sections into
it without touching your existing Overview, Commands, or anything else you
wrote. It shows you the merged result and asks you to sanity-check it, then
offers to read your actual source and fill in any placeholders that are left.
Nothing is overwritten silently, ever.

**No agent, just a terminal?** Use the shell version instead — see
[Option B](#option-b-init_agent-shell-script-no-agent-required) below.

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

## Option A: `/init-agent` slash command (recommended if you use Claude Code)

```bash
mkdir -p ~/.claude/commands
curl -fsSL https://raw.githubusercontent.com/TranThanh96/claude_init_setup/main/init-agent.md \
  -o ~/.claude/commands/init-agent.md
```

```
/init-agent [target_dir]   # defaults to the current directory
```

What it does:

- **File missing in target:** copied in as-is.
- **File already exists in target:** left untouched — never overwritten.
- **`CLAUDE.md` already exists:** the Rules / Memory Bank / Memory Rules
  sections are merged in; every other section (Overview, Commands, anything
  custom) is left exactly as-is. You're shown the result and asked to check
  for duplicates or conflicts before moving on.
- **Newly created files still have placeholders:** the agent offers to read
  your actual source and propose real content — you approve before it writes
  anything.

See [`init-agent.md`](init-agent.md) for the exact instructions the agent follows.

## Option B: `init_agent` shell script (no agent required)

```bash
git clone https://github.com/TranThanh96/claude_init_setup.git ~/workspace/claude_init_setup
install -m 755 ~/workspace/claude_init_setup/init_agent.sh ~/.local/bin/init_agent
```

`init_agent` reads its template from `INIT_AGENT_TEMPLATE` (default:
`~/workspace/claude_init_setup` — set the env var if you clone it elsewhere).
Make sure `~/.local/bin` is on your `PATH`.

```bash
init_agent [target_dir]   # defaults to the current directory
```

Same missing/existing-file rules as Option A. The one thing a plain script
can't safely do is merge markdown content, so if `CLAUDE.md` already exists,
it stages the template at `.claude/CLAUDE.md.template` and prints a
ready-to-paste merge prompt for your agent instead of guessing.

After scaffolding a genuinely new project, ask your coding agent to read the
codebase and fill in the `Overview` and `Commands` sections of `CLAUDE.md`, plus
an initial `CLAUDE-activeContext.md`. Review the result before committing.

## Daily usage

- **Start of session:** read `CLAUDE-activeContext.md` first (or let `CLAUDE.md`'s
  Memory Bank table remind the agent to).
- **During work:** `.claude/rules/core-rules.md` and `coding-guidelines.md` are
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

## Credit

Inspired by [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup),
stripped down to the minimum file set and workflow described above.
