#!/usr/bin/env python3
"""Lint the project memory bank. Usable locally, in pre-commit, or in CI.

  python3 scripts/memory-lint.py            # errors → exit 1, warnings → exit 0
  python3 scripts/memory-lint.py --strict   # warnings also → exit 1
  python3 scripts/memory-lint.py --quiet    # print only problems

Budgets count lines after stripping HTML comments, because Claude Code strips
those comments before injecting CLAUDE.md into context.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / ".claude" / "memory"

# path (relative to ROOT) → max content lines
BUDGETS = {
    "CLAUDE.md": 100,
    ".claude/memory/active.md": 40,
    ".claude/memory/decisions.md": 150,
    ".claude/memory/troubleshooting.md": 150,
    ".claude/memory/patterns.md": 150,
}
ALWAYS_LOADED_RULES_BUDGET = 150  # total lines across .claude/rules/*.md without `paths`
PLACEHOLDER_RE = re.compile(r"<\.\.\.>")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def content_lines(path: Path) -> int:
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    return sum(1 for line in text.splitlines() if line.strip())


def git(*args: str) -> list[str] | None:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.splitlines() if out.returncode == 0 else None


def has_paths_frontmatter(text: str) -> bool:
    m = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
    return bool(m and re.search(r"^paths\s*:", m.group(1), flags=re.M))


def check_budgets(r: Report) -> None:
    for rel, limit in BUDGETS.items():
        p = ROOT / rel
        if not p.is_file():
            continue
        n = content_lines(p)
        if n > limit:
            r.error(f"{rel}: {n} content lines > budget {limit}. Merge or remove stale entries.")


def check_rules(r: Report) -> None:
    rules_dir = ROOT / ".claude" / "rules"
    total = 0
    for p in sorted(rules_dir.rglob("*.md")) if rules_dir.is_dir() else []:
        if not has_paths_frontmatter(p.read_text(encoding="utf-8")):
            total += content_lines(p)
    if total > ALWAYS_LOADED_RULES_BUDGET:
        r.warn(f".claude/rules: {total} always-loaded lines > {ALWAYS_LOADED_RULES_BUDGET}. "
               "Scope rules with `paths:` or move procedures into skills.")

    claude_md = ROOT / "CLAUDE.md"
    if claude_md.is_file():
        text = re.sub(r"<!--.*?-->", "", claude_md.read_text(encoding="utf-8"), flags=re.S)
        for m in re.finditer(r"(?<![`\w])@(\.claude/rules/\S+\.md)", text):
            r.error(f"CLAUDE.md imports {m.group(1)}, but .claude/rules/ loads automatically. "
                    "The rule is injected twice; remove the @import.")
        if PLACEHOLDER_RE.search(text):
            r.warn("CLAUDE.md still contains template placeholders (<...>).")


def check_active_ignored(r: Report) -> None:
    if git("rev-parse", "--git-dir") is None:
        return  # not a git repo
    if git("check-ignore", "-q", ".claude/memory/active.md") is None:
        r.warn(".claude/memory/active.md is not gitignored. It is a local snapshot per checkout; "
               "add it to .gitignore.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--quiet", action="store_true", help="print only problems")
    args = ap.parse_args()

    if not MEM.is_dir():
        print(f"memory-lint: {MEM.relative_to(ROOT)} not found; nothing to check.")
        return 0

    r = Report()
    for check in (check_budgets, check_rules, check_active_ignored):
        check(r)

    for msg in r.errors:
        print(f"ERROR  {msg}")
    for msg in r.warnings:
        print(f"WARN   {msg}")
    if not args.quiet and not (r.errors or r.warnings):
        print("memory-lint: OK")
    failed = bool(r.errors) or (args.strict and bool(r.warnings))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
