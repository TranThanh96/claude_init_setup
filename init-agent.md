---
description: Scaffold or upgrade the claude_init_setup memory bank (v3) in this project, or in the directory given as an argument.
disable-model-invocation: true
---

Scaffold the claude_init_setup memory bank (github.com/TranThanh96/claude_init_setup) into the
current project, or into $ARGUMENTS if given. Never overwrite a file silently.

1. Target = $ARGUMENTS or the current working directory. Shallow-clone the template to a scratch
   dir: `git clone --depth 1 https://github.com/TranThanh96/claude_init_setup.git <tmpdir>`.
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
3. Run `bash <tmpdir>/init_agent.sh <target>` with `INIT_AGENT_TEMPLATE=<tmpdir>`; add `--upgrade`
   before `<target>` if the target already has `.claude/memory/` (it then refreshes the
   template-owned hooks, scripts and skills, skipping any with uncommitted changes), and add
   `--with-workflow` if step 2 chose the workflow tier. It copies missing files, skips existing
   ones, stages `CLAUDE.md.template` / `settings.json.template` when those already exist, adds
   `.claude/memory/active.md` to `.gitignore`, detects a v1 or v2 layout, and installs a `git
   pre-commit` hook that warns on memory drift (only if the target doesn't already have one).
   Read its full output.
4. If templates were staged, do the merge the script's prompt describes. Keep all existing project
   content; remove `@.claude/rules/...` imports (rules auto-load, so importing duplicates them).
   Show me the diffs of CLAUDE.md and settings.json and wait for approval.
5. If a v1 or v2 layout was detected, propose the migration the script's prompt describes. Show
   the diff; delete old files only after I approve.
6. If CLAUDE.md was newly created and still has placeholders (Overview/Commands/Gotchas): read
   the project's actual source, build files, and CI config, and propose real content. Gotchas must come from
   evidence in the repo (comments, CI steps, configs), not generic advice. Present the proposal
   before writing.
7. Propose a `.claude/checks.json` from `.claude/checks.example.json` using only linters/type
   checkers the project already uses. Don't introduce new tools. If the workflow tier was
   installed, also mention `.claude/routing.example.json` → `.claude/routing.json` (fill in
   codex/antigravity model names once those are actually used).
8. Run `python3 scripts/memory-lint.py` and fix all errors.
9. Self-update: if `<tmpdir>/init-agent.md` differs from `~/.claude/commands/init-agent.md`,
   copy it over and say so (the new version applies from the next run). Do this before deleting
   the scratch clone.
10. Report: created / updated / skipped / merged / migrated / filled in, and anything left for me
    to decide. On an upgrade, show `git diff --stat` of the updated files. Delete the scratch clone.
