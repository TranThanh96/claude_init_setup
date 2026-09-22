#!/usr/bin/env python3
"""Stop hook: nudge once per session when code changed but memory did not.

Replaces the old soft rule "remind me to run /update-memory-bank", which the
agent could forget. Logic:
  - Changed files = commits since session start (recorded by session_start.py)
    plus uncommitted changes in the working tree.
  - If >= MEMORY_NUDGE_MIN_FILES non-memory files changed and nothing under
    .claude/memory/ changed, block the stop ONCE per session with a reason.
  - Never blocks twice (stop_hook_active + per-session marker), so it cannot loop.

Tune with env var MEMORY_NUDGE_MIN_FILES (default 3). Set it to 0 to disable.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MEMORY_PREFIX = ".claude/memory/"


def git_lines(root: Path, *args: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    threshold = int(os.environ.get("MEMORY_NUDGE_MIN_FILES", "3"))
    if threshold <= 0 or payload.get("stop_hook_active"):
        return 0

    session_id = payload.get("session_id")
    if not session_id:
        return 0
    marker = Path(tempfile.gettempdir()) / f"claude-memory-{session_id}.json"
    try:
        state = json.loads(marker.read_text())
    except (OSError, json.JSONDecodeError):
        state = {}
    if state.get("nudged"):
        return 0

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    if not (root / ".claude" / "memory").is_dir():
        return 0

    changed: set[str] = set()
    start = state.get("start_head")
    if start:
        changed.update(git_lines(root, "diff", "--name-only", f"{start}..HEAD"))
    for line in git_lines(root, "status", "--porcelain", "--untracked-files=all"):
        path = line[3:].split(" -> ")[-1].strip('"')
        changed.add(path)

    memory_changed = [p for p in changed if p.startswith(MEMORY_PREFIX)]
    code_changed = [p for p in changed if not p.startswith(MEMORY_PREFIX)]
    if memory_changed or len(code_changed) < threshold:
        return 0

    state["nudged"] = True
    try:
        marker.write_text(json.dumps(state))
    except OSError:
        return 0  # without a marker we could nudge repeatedly; fail open instead

    reason = (
        f"{len(code_changed)} file(s) changed during this session and nothing under "
        f".claude/memory/ changed. If this task reached a milestone, ask the user whether "
        f"to run /update-memory-bank. If the work is mid-flight or trivial, finish normally "
        f"without updating memory."
    )
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
