"""End-to-end tests for the template: installer, hooks, memory-lint.

Run from the repo root:  python3 -m unittest discover -s tests -v
Stdlib only. Each test builds a throwaway git repo, installs the template with
the real init_agent.sh, and feeds hooks the same JSON Claude Code sends on stdin.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent


class Project:
    """A temp git repo with the template installed."""

    def __init__(self, root: Path, tmpdir: Path) -> None:
        self.root = root
        self.env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root), "TMPDIR": str(tmpdir)}
        self.env.pop("MEMORY_NUDGE_MIN_FILES", None)

    def sh(self, *cmd: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, cwd=self.root, env=self.env, capture_output=True, text=True, check=check)

    def git(self, *args: str) -> str:
        return self.sh("git", *args).stdout.strip()

    def write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def commit(self, msg: str = "wip") -> None:
        self.git("add", "-A")
        self.git("commit", "-qm", msg)

    def hook(self, name: str, payload: dict, extra_env: dict | None = None) -> subprocess.CompletedProcess:
        env = {**self.env, **(extra_env or {})}
        return subprocess.run(
            ["python3", str(self.root / ".claude" / "hooks" / name)],
            cwd=self.root, env=env, input=json.dumps(payload), capture_output=True, text=True,
        )

    def lint(self, *args: str) -> subprocess.CompletedProcess:
        return self.sh("python3", "scripts/memory-lint.py", *args, check=False)


class TemplateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="cis-test-"))
        (self._tmp / "tmp").mkdir()
        root = self._tmp / "proj"
        root.mkdir()
        self.p = Project(root, self._tmp / "tmp")
        self.p.git("init", "-q", "-b", "main")
        self.p.git("config", "user.email", "t@example.com")
        self.p.git("config", "user.name", "test")
        self.p.env["INIT_AGENT_TEMPLATE"] = str(TEMPLATE)
        self.install = self.p.sh("bash", str(TEMPLATE / "init_agent.sh"), str(root), check=False)
        self.assertEqual(self.install.returncode, 0, self.install.stderr)
        self.p.write("app.py", "print('hi')\n")
        self.p.commit("init")
        self.sid = str(uuid.uuid4())

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def start(self, source: str = "startup") -> str:
        res = self.p.hook("session_start.py", {"session_id": self.sid, "source": source})
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"] if res.stdout else ""

    def stop(self, **kw) -> str:
        payload = {"session_id": self.sid, "stop_hook_active": False, **kw}
        res = self.p.hook("stop_memory_nudge.py", payload)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout

    def add_task_file(self, branch: str) -> None:
        tpl = (self.p.root / ".claude/memory/tasks/_TEMPLATE.md").read_text()
        text = (tpl.replace("<branch name>", branch)
                   .replace("<short sha at time of writing>", self.p.git("rev-parse", "--short", "HEAD"))
                   .replace("<one-line description>", "demo task"))
        self.p.write(f".claude/memory/tasks/{branch.replace('/', '__')}.md", text)


class TestInstaller(TemplateTestCase):
    def test_fresh_install_creates_everything(self):
        for rel in (".claude/settings.json", ".claude/hooks/session_start.py",
                    ".claude/skills/project-memory/SKILL.md", "scripts/memory-lint.py"):
            self.assertTrue((self.p.root / rel).is_file(), rel)
        json.loads((self.p.root / ".claude/settings.json").read_text())

    def test_existing_files_are_never_overwritten(self):
        self.p.write("CLAUDE.md", "# mine\n")
        self.p.write(".claude/settings.json", '{"model": "opus"}\n')
        res = subprocess.run(["bash", str(TEMPLATE / "init_agent.sh"), str(self.p.root)],
                             env=self.p.env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual((self.p.root / "CLAUDE.md").read_text(), "# mine\n")
        self.assertTrue((self.p.root / "CLAUDE.md.template").is_file())
        self.assertTrue((self.p.root / ".claude/settings.json.template").is_file())

    def test_v1_layout_is_detected(self):
        self.p.write("CLAUDE-activeContext.md", "# old\n")
        res = subprocess.run(["bash", str(TEMPLATE / "init_agent.sh"), str(self.p.root)],
                             env=self.p.env, capture_output=True, text=True)
        self.assertIn("Detected a v1 memory bank", res.stdout)
        self.assertTrue((self.p.root / "CLAUDE-activeContext.md").is_file(), "v1 files must not be moved")


class TestSessionStart(TemplateTestCase):
    def test_injects_branch_task_file_with_staleness(self):
        self.p.git("checkout", "-qb", "feat/login")
        self.add_task_file("feat/login")
        self.p.commit("task")
        self.p.write("app.py", "print('changed')\n")
        self.p.commit("more")
        ctx = self.start()
        self.assertIn("branch 'feat/login'", ctx)
        self.assertIn("2 commit(s) have landed", ctx)
        self.assertNotIn("<!--", ctx, "HTML comments must be stripped")
        self.assertNotIn("git_commit:", ctx, "frontmatter must be stripped")

    def test_reports_missing_task_file(self):
        self.p.git("checkout", "-qb", "feat/x")
        self.assertIn("No task file exists for branch 'feat/x'", self.start())

    def test_skips_unfilled_project_state(self):
        self.assertIn("has not been filled in yet", self.start())

    def test_compact_reinjects_and_says_so(self):
        self.assertIn("just compacted", self.start("compact"))

    def test_silent_in_uninitialised_project(self):
        shutil.rmtree(self.p.root / ".claude" / "memory")
        res = self.p.hook("session_start.py", {"session_id": self.sid, "source": "startup"})
        self.assertEqual((res.returncode, res.stdout), (0, ""))

    def test_output_is_capped(self):
        self.p.git("checkout", "-qb", "big")
        self.add_task_file("big")
        with open(self.p.root / ".claude/memory/tasks/big.md", "a") as f:
            f.write("- filler line for size\n" * 2000)
        self.assertLess(len(self.start()), 10_000)


class TestStopNudge(TemplateTestCase):
    def touch(self, n: int) -> None:
        for i in range(n):
            self.p.write(f"src/f{i}.py", f"x = {i}\n")

    def test_below_threshold_is_silent(self):
        self.start()
        self.touch(2)
        self.assertEqual(self.stop(), "")

    def test_nudges_exactly_once(self):
        self.start()
        self.touch(3)
        out = json.loads(self.stop())
        self.assertEqual(out["decision"], "block")
        self.assertEqual(self.stop(), "")

    def test_resume_and_clear_do_not_reset_the_nudge(self):
        self.start()
        self.touch(3)
        self.assertTrue(self.stop())
        self.start("resume")
        self.start("clear")
        self.assertEqual(self.stop(), "", "must not nudge again after resume/clear")

    def test_memory_change_suppresses_nudge(self):
        self.start()
        self.touch(3)
        self.p.write(".claude/memory/patterns.md", "# Patterns\n- x\n")
        self.assertEqual(self.stop(), "")

    def test_counts_commits_made_during_session(self):
        self.start()
        self.touch(3)
        self.p.commit("session work")
        self.assertTrue(self.stop(), "committed changes must count")

    def test_counts_files_in_untracked_directories(self):
        self.start()
        self.touch(3)  # all inside a new, untracked src/ directory
        self.assertIn("3 file(s)", self.stop())

    def test_stop_hook_active_never_blocks(self):
        self.start()
        self.touch(5)
        self.assertEqual(self.stop(stop_hook_active=True), "")

    def test_can_be_disabled(self):
        self.start()
        self.touch(5)
        res = self.p.hook("stop_memory_nudge.py", {"session_id": self.sid, "stop_hook_active": False},
                          {"MEMORY_NUDGE_MIN_FILES": "0"})
        self.assertEqual(res.stdout, "")

    def test_session_end_removes_marker(self):
        self.start()
        tmp = Path(self.p.env["TMPDIR"])
        self.assertTrue(list(tmp.glob("claude-memory-*.json")))
        self.p.hook("session_end.py", {"session_id": self.sid, "reason": "prompt_input_exit"})
        self.assertFalse(list(tmp.glob("claude-memory-*.json")))

    def test_hostile_session_id_stays_in_tmpdir(self):
        self.sid = "../../evil"
        self.start()
        tmp = Path(self.p.env["TMPDIR"])
        self.assertTrue(list(tmp.glob("claude-memory-*evil.json")))
        self.assertFalse((self.p.root.parent / "evil.json").exists())


class TestPostEditCheck(TemplateTestCase):
    def edit(self, rel: str) -> subprocess.CompletedProcess:
        return self.p.hook("post_edit_check.py", {"tool_name": "Edit",
                                                  "tool_input": {"file_path": str(self.p.root / rel)}})

    def configure(self) -> None:
        self.p.write(".claude/checks.json", json.dumps({"checks": [
            {"glob": "**/*.py", "command": "python3 -m py_compile {file}"},
            {"glob": ".claude/memory/**", "command": "python3 scripts/memory-lint.py --quiet"},
        ]}))

    def test_noop_without_config(self):
        self.p.write("bad.py", "def f(:\n")
        self.assertEqual(self.edit("bad.py").returncode, 0)

    def test_failure_exits_2_with_output_for_claude(self):
        self.configure()
        self.p.write("src/bad.py", "def f(:\n")
        res = self.edit("src/bad.py")
        self.assertEqual(res.returncode, 2)
        self.assertIn("SyntaxError", res.stderr)

    def test_passing_file_and_outside_project(self):
        self.configure()
        self.assertEqual(self.edit("app.py").returncode, 0)
        res = self.p.hook("post_edit_check.py", {"tool_input": {"file_path": "/etc/hosts"}})
        self.assertEqual(res.returncode, 0)

    def test_bad_memory_edit_is_caught(self):
        self.configure()
        self.p.write(".claude/memory/decisions/ADR-001-x.md", "# ADR-001: x\n- Status: active\n")
        res = self.edit(".claude/memory/decisions/ADR-001-x.md")
        self.assertEqual(res.returncode, 2)
        self.assertIn("not listed in decisions/INDEX.md", res.stderr)


class TestMemoryLint(TemplateTestCase):
    def test_fresh_install_has_no_errors(self):
        self.assertEqual(self.p.lint().returncode, 0)

    def test_strict_fails_on_placeholders(self):
        self.assertEqual(self.p.lint("--strict").returncode, 1)

    def test_duplicate_rule_import(self):
        with open(self.p.root / "CLAUDE.md", "a") as f:
            f.write("\n@.claude/rules/core-rules.md\n")
        res = self.p.lint()
        self.assertEqual(res.returncode, 1)
        self.assertIn("injected twice", res.stdout)

    def test_import_inside_backticks_is_not_flagged(self):
        with open(self.p.root / "CLAUDE.md", "a") as f:
            f.write("\nRules live in `@.claude/rules/core-rules.md`.\n")
        self.assertNotIn("injected twice", self.p.lint().stdout)

    def test_over_budget(self):
        self.p.write(".claude/memory/patterns.md", "".join(f"- p{i}\n" for i in range(200)))
        self.assertIn("patterns.md: 200 content lines > budget 150", self.p.lint().stdout)

    def test_adr_index_consistency_and_duplicates(self):
        d = ".claude/memory/decisions/"
        self.p.write(d + "ADR-001-a.md", "# a\n- Status: active\n")
        self.p.write(d + "ADR-001-b.md", "# b\n- Status: active\n")
        self.p.write(d + "ADR-002-c.md", "# c\n")
        with open(self.p.root / d / "INDEX.md", "a") as f:
            f.write("| [ADR-009](ADR-009-gone.md) | gone | active | x |\n")
        out = self.p.lint().stdout
        self.assertIn("Duplicate ADR number 001", out)
        self.assertIn("ADR-002-c.md: missing 'Status", out)
        self.assertIn("ADR-009-gone.md, which does not exist", out)

    def test_orphaned_and_done_task_files(self):
        self.p.write(".claude/memory/tasks/feat__gone.md", "---\nstatus: in-progress\n---\n")
        self.add_task_file("main")
        f = self.p.root / ".claude/memory/tasks/main.md"
        f.write_text(f.read_text().replace("status: in-progress", "status: done"))
        out = self.p.lint().stdout
        self.assertIn("branch 'feat/gone' no longer exists", out)
        self.assertIn("tasks/main.md: status is done", out)


if __name__ == "__main__":
    unittest.main()
