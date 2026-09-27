<!--
  Always loaded, every session. Budget: <= 100 lines (checked by scripts/memory-lint.py).
  HTML comments like this one are stripped before Claude sees the file: use them
  for notes to human maintainers, they cost zero context.
  Put here only what Claude cannot infer from the code or git log.
-->

## Overview
- Goal: guided `/init-agent` installer that scaffolds two sibling repos —
  [claude_memory_bank](https://github.com/TranThanh96/claude_memory_bank) and
  [claude_ticket_workflow](https://github.com/TranThanh96/claude_ticket_workflow) — into a
  target project. This repo carries no template payload of its own; `init_agent.sh` only
  locates those two repos (git URL or a local sibling checkout) and delegates to each one's
  own `install.sh`.
- Stack: bash (installer) + Markdown (the `/init-agent` Claude Code command) + Python 3 stdlib
  (tests). No build step, no runtime dependencies.
- Architecture: `init-agent.md` (the command) clones this repo, runs `init_agent.sh`, which
  resolves and runs `claude_memory_bank/install.sh` (always) and
  `claude_ticket_workflow/install.sh` (with `--with-workflow`) against the target directory.

## Commands
- Install: nothing to install; `bash init_agent.sh [--upgrade] [--with-workflow] <target>`
- Test (all): `python3 -m unittest discover -s tests -v`
- Test (one file): same command — there's only `tests/test_template.py`
- Lint/format: `bash -n init_agent.sh` (syntax check; no formatter)
- Run local: `INIT_AGENT_MEMORY_BANK_REPO=../claude_memory_bank INIT_AGENT_TICKET_WORKFLOW_REPO=../claude_ticket_workflow bash init_agent.sh <target>`

## Gotchas
- The two source repos must exist as sibling checkouts (`../claude_memory_bank`,
  `../claude_ticket_workflow`) for tests to run without hitting the network — they're
  skipped otherwise (see `tests/test_template.py`'s `SOURCES_PRESENT` guard).
- `resolve_repo()` treats an `INIT_AGENT_*_REPO` value that's an existing local directory as
  a checkout to use as-is (no clone); anything else is treated as a git URL and shallow-cloned.
  This is what makes local testing network-free.
- The `cleanup` trap must never be a bare `[[ cond ]] && action` as its last statement: with
  `set -e`, that construct's own exit status becomes the script's final exit code when it fires
  on `EXIT`, silently turning a successful run into a reported failure. Use `if`/`fi` instead.
- Don't add real memory-bank or workflow *content* to this repo's own `.claude/` — it was
  self-installed here for dogfooding (so this repo's own sessions get the same guardrails it
  ships), not as a second copy of the template source. The canonical source of each file lives
  in its own repo; upgrade this repo's copies with `init_agent.sh --upgrade --with-workflow .`

## Project memory
`.claude/memory/` holds what the code and git log can't tell you. Read a file when its row applies:

| File | Read when |
| --- | --- |
| `active.md` (local, gitignored) | Injected at session start. A subagent without it in context: read it if the current task is unclear |
| `decisions.md` | Before a design choice, a public-interface change or a new dependency |
| `patterns.md` | Before implementing a feature, module or test |
| `troubleshooting.md` | When a bug or failure has no obvious cause |

- An `active` decision is a constraint: if a change contradicts one, stop and tell the user which one and why.
- Memory can be stale: when it disagrees with the code, trust the code and point out the stale entry.
- Project facts go here, not in Claude's auto memory (which holds personal preferences only).
- When compacting, preserve: the list of modified files and the test commands run with their results.
