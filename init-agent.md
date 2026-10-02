---
description: Scaffold or upgrade the claude_memory_bank (and, optionally, claude_ticket_workflow) into this project, or into the directory given as an argument.
disable-model-invocation: true
---

Scaffold [claude_memory_bank](https://github.com/TranThanh96/claude_memory_bank) and, optionally,
[claude_ticket_workflow](https://github.com/TranThanh96/claude_ticket_workflow) into the current
project, or into $ARGUMENTS if given. This command itself lives in
[claude_init_setup](https://github.com/TranThanh96/claude_init_setup), a thin orchestrator: the
actual template files and install logic live in the two repos above, each independently
installable on its own if you only want one layer. Never overwrite a file silently.

1. Target = $ARGUMENTS or the current working directory. Shallow-clone the orchestrator to a
   scratch dir: `git clone --depth 1 https://github.com/TranThanh96/claude_init_setup.git <tmpdir>`.
2. If `<target>/.claude/rules/workflow.md` already exists, the target is already on the workflow
   tier — skip this ask (the script keeps it automatically). Otherwise ask the user which tier to
   install:
   - **Core** (default): the memory bank only — `active.md` snapshot, `decisions.md` /
     `patterns.md` / `troubleshooting.md`, the SessionStart/PostToolUse hooks, memory-lint. What
     most projects need.
   - **Core + ticket workflow**: adds the `grilling` / `to-spec` / `to-tickets` /
     `implementation` / `tdd` / `debugging` / `ticket-review` skills, `AGENTS.md`,
     `routing.json`, and `scripts/tasks_status.py` — for projects that plan large features
     spec-first or delegate tickets across Claude/Codex/Antigravity.
   Wait for their answer before continuing.
3. If step 2 chose (or step 2 was skipped because the workflow tier already exists) the ticket
   workflow tier, and there's no `<target>/.claude/routing.json` yet, ask one more question, in
   one shot — don't split it into a yes/no round followed by a name round: "Besides a Claude
   subagent, will you also run another coding CLI yourself (Codex, Antigravity, opencode,
   Cursor's CLI, or similar) to implement some tickets? If so, which one(s)?" Wait for their
   answer — a plain "Claude only" is valid and expected, not a thing to talk them out of; if they
   say yes without naming one, ask which before moving on, since step 8 needs a name to write.
   Remember the answer for step 8, where each name is normalized to a key by this fixed
   algorithm, so the same free-text answer always produces the same key: lowercase it; remove any
   `'s` (possessive); strip everything that isn't a letter, digit, or space; split on whitespace;
   drop any word that's exactly `cli`, `code`, `coding`, `assistant`, or `agent` (generic, not
   part of the product name); join what's left with no separator. Examples: "Codex" -> `codex`,
   "Cursor's CLI" -> `cursor`, "GitHub Copilot CLI" -> `githubcopilot`. The question's wording is
   free-text and isn't itself the key. If `routing.json` already exists, skip this ask entirely
   (their existing `delegates` list already answers it, and it's theirs to edit from here on).
4. Run `bash <tmpdir>/init_agent.sh <target>` with `INIT_AGENT_MEMORY_BANK_REPO`/
   `INIT_AGENT_TICKET_WORKFLOW_REPO` left at their defaults (the two GitHub repos); add
   `--upgrade` before `<target>` if the target already has `.claude/memory/` (it then refreshes
   the template-owned hooks, scripts and skills, skipping any with uncommitted changes), and add
   `--with-workflow` if step 2 chose the workflow tier. This clones each source repo in turn and
   runs its own `install.sh` against `<target>`: files are copied if missing, skipped if present,
   `CLAUDE.md.template` / `AGENTS.md.template` / `settings.json.template` are staged when those
   already exist, `.claude/memory/active.md` is added to `.gitignore`, a v1/v2 layout is detected,
   and a `git pre-commit` hook is installed (only if the target doesn't already have one). Read
   its full output.
5. If templates were staged, do the merge each install.sh's prompt describes. Keep all existing
   project content; remove `@.claude/rules/...` imports (rules auto-load, so importing duplicates
   them). Show me the diffs of `CLAUDE.md`, `AGENTS.md` and `settings.json` and wait for approval.
6. If a v1 or v2 layout was detected, propose the migration the script's prompt describes. Show
   the diff; delete old files only after I approve.
7. If `CLAUDE.md` was newly created and still has placeholders (Overview/Commands/Gotchas): read
   the project's actual source, build files, and CI config, and propose real content. Gotchas must
   come from evidence in the repo (comments, CI steps, configs), not generic advice. Present the
   proposal before writing.

   The `## Project docs` table is handled separately, since reading every doc file can burn a lot
   of tokens. If `<target>/docs/` doesn't exist yet, leave the section as a placeholder for
   whenever docs show up later — don't delete it. If it exists, don't read the files yet: list
   them and guess each one's "Read when / Purpose" from its filename alone (e.g. `architecture.md`
   -> "Before changing module boundaries"). Show me the guesses and ask which are right and which
   I want you to open to verify. Only read a file after I say so; for any guess I neither confirm
   nor authorize reading, leave its row's placeholder and note that file as not yet reviewed.
8. Propose a `.claude/checks.json` from `.claude/checks.example.json` using only linters/type
   checkers the project already uses. Don't introduce new tools. If the workflow tier was
   installed and `<target>/.claude/routing.json` doesn't exist yet, create it by copying
   `.claude/routing.example.json` and setting its `delegates` field from step 3's answer:
   `["claude"]` for Claude-only, or `["claude", "<cli1>", "<cli2>", ...]` naming every CLI they
   gave otherwise, each normalized per step 3's algorithm before comparing or writing. For each
   named CLI whose normalized key isn't already one of the example file's blocks
   (`antigravity`/`codex` already have one), add a matching block keyed by that normalized name —
   `{ "trivial": "", "small": "", "medium": "", "large": "" }` — so the schema stays consistent
   even for a CLI the template didn't anticipate. `delegates` itself can be edited by hand at any
   time afterward to add or drop a CLI (adding a matching block too, if it's a new one), since
   `to-tickets` reads it fresh before every dispatch and needs no reinstall for that.

   Whether `routing.json` was just created above or already existed: if the workflow tier is
   installed, check it (or `routing.example.json` if there's still no `routing.json`) for any
   delegate in `delegates` other than `claude` whose model-name block has a blank field, and
   remind me to fill those in once I've actually used that CLI — do this every run, not only the
   run that creates the file.
9. Run `python3 scripts/memory-lint.py` and fix all errors.
10. Self-update: if `<tmpdir>/init-agent.md` differs from `~/.claude/commands/init-agent.md`,
    copy it over and say so (the new version applies from the next run). Do this before deleting
    the scratch clone.
11. Report: created / updated / skipped / merged / migrated / filled in, and anything left for me
    to decide. On an upgrade, show `git diff --stat` of the updated files. Delete the scratch clone.
