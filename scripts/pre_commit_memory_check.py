#!/usr/bin/env python3
"""Git pre-commit hook: warn when code has drifted from the last memory update.

Not a Claude Code hook -- a plain git hook, installed at .git/hooks/pre-commit
by init_agent.sh, so it fires for every commit, from any tool, by any
developer, whether or not they're using Claude Code.

No session state or /tmp marker: it finds the last commit that touched
.claude/memory/ straight from git log, and measures drift since then. Warns
to stderr, never blocks: exit 0 always.

Tune with MEMORY_NUDGE_MIN_FILES (default 3) and MEMORY_NUDGE_MIN_COMMITS
(default 5) -- either signal crossing its threshold warns. Set both to 0 to
disable.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MEMORY_PREFIX = ".claude/memory/"


def git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def git_lines(*args: str) -> list[str]:
    out = git(*args)
    return [line for line in out.splitlines() if line.strip()] if out else []


def main() -> int:
    file_threshold = int(os.environ.get("MEMORY_NUDGE_MIN_FILES", "3"))
    commit_threshold = int(os.environ.get("MEMORY_NUDGE_MIN_COMMITS", "5"))
    if file_threshold <= 0 and commit_threshold <= 0:
        return 0

    if not Path(".claude/memory").is_dir():
        return 0  # project not initialised with the memory bank

    staged = git_lines("diff", "--cached", "--name-only")
    if any(p.startswith(MEMORY_PREFIX) for p in staged):
        return 0  # this commit updates memory

    last = git("log", "-1", "--format=%H", "--", ".claude/memory")
    if not last:
        return 0  # no baseline yet

    changed = set(git_lines("diff", "--name-only", f"{last}..HEAD")) | set(staged)
    n_files = len(changed)
    commits_str = git("rev-list", "--count", f"{last}..HEAD")
    n_commits = int(commits_str) if commits_str else 0

    over_files = file_threshold > 0 and n_files >= file_threshold
    over_commits = commit_threshold > 0 and n_commits >= commit_threshold
    if not (over_files or over_commits):
        return 0

    print(
        f"pre-commit: {n_files} file(s) changed across {n_commits} commit(s) since "
        f".claude/memory/ was last updated (at {last[:7]}). Consider /update-memory-bank "
        f"before this commit, or after, if the task isn't done yet.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
