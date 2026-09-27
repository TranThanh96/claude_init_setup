#!/usr/bin/env bash
# Orchestrator: install claude_memory_bank (always) and claude_ticket_workflow
# (with --with-workflow) into a project, by delegating to each repo's own install.sh.
#
# Usage:
#   init_agent.sh [--upgrade] [--with-workflow] [target_dir]
#
# Env (each may be a git URL or a local path to an existing checkout -- a local path
# is used as-is, with no clone, which is what the test suite and local development use):
#   INIT_AGENT_MEMORY_BANK_REPO      default: https://github.com/TranThanh96/claude_memory_bank.git
#   INIT_AGENT_TICKET_WORKFLOW_REPO  default: https://github.com/TranThanh96/claude_ticket_workflow.git
#
# This script owns no template files itself -- it only locates the two source repos
# (cloning them to a scratch dir if a local path wasn't given) and runs their install.sh
# against target_dir, forwarding --upgrade. See their own install.sh for what actually
# gets copied.
#
# A target that already has .claude/rules/workflow.md keeps the workflow tier
# automatically; --with-workflow is only needed to add it for the first time.

set -euo pipefail

MEMORY_BANK_REPO="${INIT_AGENT_MEMORY_BANK_REPO:-https://github.com/TranThanh96/claude_memory_bank.git}"
TICKET_WORKFLOW_REPO="${INIT_AGENT_TICKET_WORKFLOW_REPO:-https://github.com/TranThanh96/claude_ticket_workflow.git}"

UPGRADE=0
WORKFLOW=0
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --upgrade) UPGRADE=1 ;;
    --with-workflow) WORKFLOW=1 ;;
    *) echo "error: unknown flag $1" >&2; exit 1 ;;
  esac
  shift
done
TARGET_DIR="${1:-.}"

if [[ -f "$TARGET_DIR/.claude/rules/workflow.md" ]]; then
  WORKFLOW=1
fi

SCRATCH=""
# Preserve whatever exit status triggered this trap (0 on success, non-zero from
# `set -e`) instead of letting cleanup's own commands silently replace it.
cleanup() {
  local code=$?
  if [[ -n "$SCRATCH" ]]; then rm -rf "$SCRATCH"; fi
  exit "$code"
}
trap cleanup EXIT

# Prints the local directory to use for $2 (a git URL or local path already), cloning
# to a fresh scratch dir first if it isn't already a local directory.
resolve_repo() {
  local ref="$1" name="$2"
  if [[ -d "$ref" ]]; then
    echo "$ref"
    return
  fi
  if [[ -z "$SCRATCH" ]]; then
    SCRATCH="$(mktemp -d)"
  fi
  local dest="$SCRATCH/$name"
  echo "cloning $ref ..." >&2
  git clone --depth 1 -q "$ref" "$dest" >&2
  echo "$dest"
}

mkdir -p "$TARGET_DIR"

# Forwards --upgrade to <dir>/install.sh without an array: an optional flag held in
# an empty array and expanded as "${arr[@]}" crashes with "unbound variable" under
# `set -u` on bash 3.2 (macOS's default /bin/bash), even when explicitly declared
# empty with `arr=()` -- fixed upstream in bash 4.4, but 3.2 is what macOS ships.
install_layer() {
  local dir="$1"
  if [[ $UPGRADE -eq 1 ]]; then
    bash "$dir/install.sh" --upgrade "$TARGET_DIR"
  else
    bash "$dir/install.sh" "$TARGET_DIR"
  fi
}

MEMORY_BANK_DIR="$(resolve_repo "$MEMORY_BANK_REPO" memory_bank)"
echo "== claude_memory_bank =="
install_layer "$MEMORY_BANK_DIR"

if [[ $WORKFLOW -eq 1 ]]; then
  TICKET_WORKFLOW_DIR="$(resolve_repo "$TICKET_WORKFLOW_REPO" ticket_workflow)"
  echo
  echo "== claude_ticket_workflow =="
  install_layer "$TICKET_WORKFLOW_DIR"
else
  echo
  echo "Ticket workflow (grilling/to-spec/to-tickets/implementation/tdd/debugging/ticket-review,"
  echo "AGENTS.md, routing.json) not installed. Re-run with --with-workflow to add it later."
fi
