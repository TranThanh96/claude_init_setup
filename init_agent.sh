#!/usr/bin/env bash
# Scaffold the claude_init_setup memory bank (v2) into a project.
#
# Usage:
#   init_agent [target_dir]
#
# Env:
#   INIT_AGENT_TEMPLATE  path to the template repo (default: ~/workspace/claude_init_setup)
#
# Behavior:
#   - Files that don't exist in the target are copied as-is.
#   - Files that already exist are never overwritten.
#   - CLAUDE.md and .claude/settings.json are special-cased: if the target already
#     has one, the template is staged next to it (*.template) and a merge prompt
#     is printed for your coding agent. A script can't safely merge markdown/JSON.
#   - A v1 layout (CLAUDE-*.md in the project root) is detected and a migration
#     prompt is printed. Nothing from v1 is moved or deleted automatically.

set -euo pipefail

TEMPLATE_DIR="${INIT_AGENT_TEMPLATE:-$HOME/workspace/claude_init_setup}"
TARGET_DIR="${1:-.}"

if [[ ! -f "$TEMPLATE_DIR/CLAUDE.md" || ! -d "$TEMPLATE_DIR/.claude/memory" ]]; then
  echo "error: v2 template not found at $TEMPLATE_DIR (set INIT_AGENT_TEMPLATE to override)" >&2
  exit 1
fi
command -v python3 >/dev/null || echo "warning: python3 not found on PATH; hooks and memory-lint need it." >&2

mkdir -p "$TARGET_DIR"

FILES=(
  "CLAUDE.md"
  ".claude/settings.json"
  ".claude/checks.example.json"
  ".claude/rules/core-rules.md"
  ".claude/rules/coding-guidelines.md"
  ".claude/rules/memory-files.md"
  ".claude/hooks/session_start.py"
  ".claude/hooks/stop_memory_nudge.py"
  ".claude/hooks/post_edit_check.py"
  ".claude/skills/project-memory/SKILL.md"
  ".claude/skills/update-memory-bank/SKILL.md"
  ".claude/skills/memory-audit/SKILL.md"
  ".claude/memory/project-state.md"
  ".claude/memory/patterns.md"
  ".claude/memory/troubleshooting.md"
  ".claude/memory/decisions/INDEX.md"
  ".claude/memory/decisions/ADR-000-template.md"
  ".claude/memory/tasks/_TEMPLATE.md"
  "scripts/memory-lint.py"
)
MERGE_FILES=("CLAUDE.md" ".claude/settings.json")

created=()
skipped=()
staged=()

for file in "${FILES[@]}"; do
  src="$TEMPLATE_DIR/$file"
  dst="$TARGET_DIR/$file"

  if [[ -f "$dst" ]]; then
    if [[ " ${MERGE_FILES[*]} " == *" $file "* ]]; then
      cp "$src" "$dst.template"
      staged+=("$file")
    else
      skipped+=("$file")
    fi
    continue
  fi

  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  created+=("$file")
done

chmod +x "$TARGET_DIR"/.claude/hooks/*.py "$TARGET_DIR/scripts/memory-lint.py" 2>/dev/null || true

echo "== init_agent (v2): $TARGET_DIR =="
echo "created:"
for f in "${created[@]:-}"; do [[ -n "$f" ]] && echo "  + $f"; done
echo "skipped (already exists):"
for f in "${skipped[@]:-}"; do [[ -n "$f" ]] && echo "  = $f"; done

if [[ ${#staged[@]} -gt 0 ]]; then
  echo
  echo "Already existed, template staged as <file>.template (NOT overwritten):"
  for f in "${staged[@]}"; do echo "  ~ $f.template"; done
  cat <<'EOF'

Hand this prompt to your coding agent:
---
Merge the staged *.template files into their originals, then delete the .template files.
- CLAUDE.md: add the "## Gotchas" and "## Project memory" sections if missing. Keep every
  existing section unchanged. Remove any "@.claude/rules/..." import lines: .claude/rules/
  loads automatically, so importing a rule injects it twice.
- .claude/settings.json: add the template's hooks and permissions.deny entries to the existing
  arrays. Do not remove or reorder existing entries. Validate the result is valid JSON.
Show me both diffs before finishing.
---
EOF
fi

if compgen -G "$TARGET_DIR/CLAUDE-*.md" >/dev/null; then
  cat <<'EOF'

Detected a v1 memory bank (CLAUDE-*.md in the project root). Hand this prompt to your agent:
---
Migrate the v1 memory bank into .claude/memory/ (read .claude/rules/memory-files.md first):
- CLAUDE-activeContext.md → split: project-level state into .claude/memory/project-state.md;
  the current task into .claude/memory/tasks/<branch>.md (branch "/" → "__", use _TEMPLATE.md).
- CLAUDE-decisions.md → one file per ADR in .claude/memory/decisions/ADR-NNN-slug.md, keeping
  numbers and statuses, plus one line each in decisions/INDEX.md.
- CLAUDE-patterns.md → .claude/memory/patterns.md; CLAUDE-troubleshooting.md →
  .claude/memory/troubleshooting.md (append below the header, drop obsolete entries).
- .claude/commands/update-memory-bank.md (v1) is replaced by the update-memory-bank skill,
  which has the same /name. Delete the old command so the two don't collide.
- In .claude/rules/core-rules.md, drop the "remind me to run /update-memory-bank" rule:
  the Stop hook now does that.
- Run python3 scripts/memory-lint.py until it reports no errors.
- Show me the diff. Only after I approve, git rm the old CLAUDE-*.md files.
---
EOF
fi

echo
echo "Next: fill CLAUDE.md (Overview, Commands, Gotchas), copy .claude/checks.example.json to"
echo ".claude/checks.json for per-edit lint, then run: python3 scripts/memory-lint.py"
