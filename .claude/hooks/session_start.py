#!/usr/bin/env python3
"""SessionStart hook: inject project memory into the session.

Fires on startup, resume, /clear and after compaction (see matcher in
.claude/settings.json), so the snapshot survives a compacted context.

Injects, as factual statements (not imperative instructions):
  - .claude/memory/project-state.md
  - .claude/memory/tasks/<branch>.md for the current git branch
  - how many commits have landed since each snapshot was written (staleness)

Also records the HEAD commit at session start so the Stop hook can tell
what changed during this session. Stdlib only: no jq, no pip installs.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_CHARS = 9000  # Claude Code caps additionalContext at 10,000 chars
PLACEHOLDER = re.compile(r"<\.\.\.>|<one-line description>|<short sha")


def git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def strip_comments(text: str) -> str:
    """Drop HTML comments and YAML frontmatter (the staleness line replaces it)."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def frontmatter_value(text: str, key: str) -> str | None:
    m = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.split(":", 1)[0].strip() == key:
            value = line.split(":", 1)[1].split("#", 1)[0].strip()
            return value or None
    return None


def staleness(root: Path, text: str) -> str:
    sha = frontmatter_value(text, "git_commit")
    if not sha or sha.startswith("<"):
        return "It records no git commit, so its age is unknown."
    count = git(root, "rev-list", "--count", f"{sha}..HEAD")
    if count is None:
        return f"It was written at commit {sha}, which is not in this branch's history."
    if count == "0":
        return f"It was written at commit {sha} (current HEAD)."
    return f"It was written at commit {sha}; {count} commit(s) have landed since then."


def marker_path(session_id: str) -> Path:
    """Per-session state file shared by the SessionStart, Stop and SessionEnd hooks."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:128]
    return Path(tempfile.gettempdir()) / f"claude-memory-{safe}.json"


def task_filename(branch: str) -> str:
    return branch.replace("/", "__") + ".md"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    mem = root / ".claude" / "memory"
    if not mem.is_dir():
        return 0  # project not initialised with the memory bank; stay silent

    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    head = git(root, "rev-parse", "--short", "HEAD")

    # Record HEAD at the first start of this session for the Stop hook. Never
    # overwrite an existing marker: on resume / clear / compact that would reset
    # the "already nudged" flag and the session's starting point.
    session_id = payload.get("session_id")
    if session_id and head:
        marker = marker_path(session_id)
        if not marker.exists():
            try:
                marker.write_text(json.dumps({"start_head": head}))
            except OSError:
                pass

    parts: list[str] = ["Project memory for this repository (from .claude/memory/):"]

    state_file = mem / "project-state.md"
    if state_file.is_file():
        raw = state_file.read_text(encoding="utf-8")
        body = strip_comments(raw)
        if PLACEHOLDER.search(body):
            parts.append("project-state.md still contains template placeholders and has not been filled in yet.")
        else:
            parts.append(f"## project-state.md\n{staleness(root, raw)}\n\n{body}")

    if branch and branch != "HEAD":
        task_file = mem / "tasks" / task_filename(branch)
        if task_file.is_file():
            raw = task_file.read_text(encoding="utf-8")
            parts.append(
                f"## Task file for branch '{branch}' (tasks/{task_file.name})\n"
                f"{staleness(root, raw)} Claims in it may be outdated; the code is the source of truth.\n\n"
                f"{strip_comments(raw)}"
            )
        else:
            parts.append(
                f"No task file exists for branch '{branch}' (expected at .claude/memory/tasks/{task_file.name})."
            )
    elif branch == "HEAD":
        parts.append("The repository is in detached HEAD state, so no branch task file applies.")

    if payload.get("source") == "compact":
        parts.append("This context was just compacted; the memory above was re-injected from disk.")

    context = "\n\n".join(parts)
    if len(context) > MAX_CHARS:
        context = context[:MAX_CHARS] + "\n\n[truncated: memory files exceed the injection budget; run /memory-audit]"

    json.dump(
        {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
