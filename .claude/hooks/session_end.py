#!/usr/bin/env python3
"""SessionEnd hook: remove this session's temp marker (written by session_start.py).

Runs within Claude Code's short SessionEnd budget, so it only deletes one file.
Skips cleanup when the session ends because it is being resumed elsewhere.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    session_id = payload.get("session_id")
    if not session_id or payload.get("reason") == "resume":
        return 0
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:128]
    try:
        (Path(tempfile.gettempdir()) / f"claude-memory-{safe}.json").unlink(missing_ok=True)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
