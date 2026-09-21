Scaffold the personal CLAUDE.md memory-bank template (github.com/TranThanh96/claude_init_setup) into the current project, or the directory given as $ARGUMENTS.

1. Determine the target directory: $ARGUMENTS if given, otherwise the current working directory.
2. Shallow-clone the template into a scratch directory: `git clone --depth 1 https://github.com/TranThanh96/claude_init_setup.git <tmpdir>`.
3. The template's relevant files (ignore its own README.md, init_agent.sh, and init-agent.md — those belong to the template repo, not to target projects):
   - CLAUDE.md
   - CLAUDE-activeContext.md
   - CLAUDE-decisions.md
   - CLAUDE-patterns.md
   - CLAUDE-troubleshooting.md
   - .claude/rules/core-rules.md
   - .claude/rules/coding-guidelines.md
   - .claude/commands/update-memory-bank.md
4. For every file above that does NOT already exist in the target directory: copy it in as-is.
5. For every file above that DOES already exist in the target directory: leave it untouched — except CLAUDE.md, which needs a merge (step 6). Do not silently overwrite anything else either.
6. If the target already has a CLAUDE.md:
   - Read both the existing CLAUDE.md and the template's CLAUDE.md.
   - Add a `## Rules` section if missing; make sure it includes `@.claude/rules/core-rules.md` and `@.claude/rules/coding-guidelines.md` — but don't duplicate either line if one is already present under any existing Rules section.
   - Add the `## Memory Bank` table and `## Memory Rules` section from the template if the existing CLAUDE.md doesn't already have something equivalent.
   - Do NOT alter, reformat, or remove any existing project-specific content (Overview, Commands, or any other section already there).
   - After merging, show the user the merged CLAUDE.md and explicitly ask them to review it for duplicated or conflicting information (e.g. two Rules sections, an Overview that now contradicts the merged content, stale info) — do not silently resolve conflicts yourself.
7. Delete the scratch clone directory when done.
8. For every CLAUDE.md / CLAUDE-*.md file that was newly created in this run (not ones that already existed and were left untouched) and still has template placeholders (`<...>`) in its Overview/Commands/activeContext sections: read the project's actual source code and propose real content to fill them in. Present the proposed content before writing it — don't overwrite silently.
9. Report a short summary: which files were created, which were skipped because they already existed, what was merged into CLAUDE.md (if anything), and what was filled in from reading the source.
