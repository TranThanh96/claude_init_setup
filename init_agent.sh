#!/usr/bin/env bash
# Scaffold the claude_init_setup memory-bank template into a project.
#
# Usage:
#   init_agent [target_dir]
#
# Env:
#   INIT_AGENT_TEMPLATE  path to the template repo (default: this repo's checkout)
#
# Behavior:
#   - Files that don't exist in the target are copied as-is.
#   - Files that already exist in the target are left untouched (never overwritten).
#   - CLAUDE.md is special-cased: if the target already has one, the template's
#     CLAUDE.md is staged at .claude/CLAUDE.md.template instead of being copied
#     over, and a merge prompt is printed for you to hand to your coding agent.

set -euo pipefail

TEMPLATE_DIR="${INIT_AGENT_TEMPLATE:-$HOME/workspace/claude_init_setup}"
TARGET_DIR="${1:-.}"

if [[ ! -f "$TEMPLATE_DIR/CLAUDE.md" ]]; then
  echo "error: template not found at $TEMPLATE_DIR (set INIT_AGENT_TEMPLATE to override)" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

FILES=(
  "CLAUDE.md"
  "CLAUDE-activeContext.md"
  "CLAUDE-decisions.md"
  "CLAUDE-patterns.md"
  "CLAUDE-troubleshooting.md"
  ".claude/rules/core-rules.md"
  ".claude/rules/coding-guidelines.md"
  ".claude/commands/update-memory-bank.md"
)

created=()
skipped=()
needs_merge=0

for file in "${FILES[@]}"; do
  src="$TEMPLATE_DIR/$file"
  dst="$TARGET_DIR/$file"

  if [[ "$file" == "CLAUDE.md" && -f "$dst" ]]; then
    mkdir -p "$TARGET_DIR/.claude"
    cp "$src" "$TARGET_DIR/.claude/CLAUDE.md.template"
    needs_merge=1
    continue
  fi

  if [[ -f "$dst" ]]; then
    skipped+=("$file")
    continue
  fi

  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  created+=("$file")
done

echo "== init_agent: $TARGET_DIR =="
echo "created:"
for f in "${created[@]:-}"; do
  [[ -n "$f" ]] && echo "  + $f"
done
echo "skipped (already exists):"
for f in "${skipped[@]:-}"; do
  [[ -n "$f" ]] && echo "  = $f"
done

if [[ "$needs_merge" -eq 1 ]]; then
  cat <<EOF

CLAUDE.md already exists in $TARGET_DIR — it was NOT overwritten.
The template version was staged at: $TARGET_DIR/.claude/CLAUDE.md.template

Hand this prompt to your coding agent to merge it in:

---
Read .claude/CLAUDE.md.template and merge its "## Rules" and "## Memory Bank"
and "## Memory Rules" sections into CLAUDE.md. Do not alter or remove any
existing project-specific content (Overview, Commands, or any other section
already there). If "## Rules" already includes the @.claude/rules/core-rules.md
or @.claude/rules/coding-guidelines.md lines, don't duplicate them. After
merging, delete .claude/CLAUDE.md.template.
---
EOF
fi
