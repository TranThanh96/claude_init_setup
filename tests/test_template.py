"""End-to-end tests for the orchestrator: init_agent.sh delegating to the two source repos.

Run from the repo root:  python3 -m unittest discover -s tests -v
Stdlib only. Points INIT_AGENT_MEMORY_BANK_REPO / INIT_AGENT_TICKET_WORKFLOW_REPO at local
sibling checkouts (../claude_memory_bank, ../claude_ticket_workflow) so tests never hit the
network. Skipped entirely if those checkouts aren't present (e.g. a plain clone of just this
repo) -- clone them next to this repo to run these tests locally.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ORCHESTRATOR = Path(__file__).resolve().parent.parent
MEMORY_BANK = ORCHESTRATOR.parent / "claude_memory_bank"
TICKET_WORKFLOW = ORCHESTRATOR.parent / "claude_ticket_workflow"

SOURCES_PRESENT = MEMORY_BANK.is_dir() and TICKET_WORKFLOW.is_dir()
SKIP_REASON = (
    f"needs sibling checkouts at {MEMORY_BANK} and {TICKET_WORKFLOW} "
    "(clone claude_memory_bank and claude_ticket_workflow next to this repo)"
)


@unittest.skipUnless(SOURCES_PRESENT, SKIP_REASON)
class OrchestratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="cis-test-"))
        self.root = self._tmp / "proj"
        self.root.mkdir()
        self.env = {
            **os.environ,
            "INIT_AGENT_MEMORY_BANK_REPO": str(MEMORY_BANK),
            "INIT_AGENT_TICKET_WORKFLOW_REPO": str(TICKET_WORKFLOW),
        }
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def run_orchestrator(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(ORCHESTRATOR / "init_agent.sh"), *args, str(self.root)],
            env=self.env, capture_output=True, text=True,
        )


class TestCoreOnly(OrchestratorTestCase):
    def test_installs_memory_bank_files_only(self):
        res = self.run_orchestrator()
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((self.root / "CLAUDE.md").is_file())
        self.assertTrue((self.root / ".claude/hooks/session_start.py").is_file())
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / ".claude/rules/workflow.md").exists())
        self.assertIn("claude_memory_bank", res.stdout)
        self.assertIn("not installed", res.stdout)

    def test_local_repo_paths_are_used_without_cloning(self):
        res = self.run_orchestrator()
        self.assertNotIn("cloning", res.stderr)


class TestWithWorkflow(OrchestratorTestCase):
    def test_installs_both_layers(self):
        res = self.run_orchestrator("--with-workflow")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((self.root / "CLAUDE.md").is_file())
        self.assertTrue((self.root / ".claude/memory/decisions.md").is_file())
        self.assertTrue((self.root / "AGENTS.md").is_file())
        self.assertTrue((self.root / ".claude/rules/workflow.md").is_file())
        self.assertTrue((self.root / ".claude/skills/to-tickets/SKILL.md").is_file())

    def test_upgrade_flag_is_forwarded_to_both_installers(self):
        self.run_orchestrator("--with-workflow")
        hook = self.root / ".claude/hooks/session_start.py"
        skill = self.root / ".claude/skills/to-tickets/SKILL.md"
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.root, check=True)
        hook.write_text("# old\n")
        skill.write_text("# old\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "outdated"], cwd=self.root, check=True)
        res = self.run_orchestrator("--with-workflow", "--upgrade")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(hook.read_text(), (MEMORY_BANK / ".claude/hooks/session_start.py").read_text())
        self.assertEqual(skill.read_text(), (TICKET_WORKFLOW / ".claude/skills/to-tickets/SKILL.md").read_text())


class TestWorkflowTierIsSticky(OrchestratorTestCase):
    def test_existing_workflow_tier_is_kept_without_the_flag(self):
        self.run_orchestrator("--with-workflow")
        res = self.run_orchestrator("--upgrade")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("claude_ticket_workflow", res.stdout)


class TestSelfTargetGuard(unittest.TestCase):
    """No sibling checkouts needed -- the guard must fire before either repo is resolved."""

    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="cis-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_refuses_a_target_that_looks_like_this_repo(self):
        target = self._tmp / "looks-like-orchestrator"
        target.mkdir()
        (target / "init_agent.sh").write_text("#!/usr/bin/env bash\n")
        (target / "init-agent.md").write_text("---\n---\n")
        res = subprocess.run(
            ["bash", str(ORCHESTRATOR / "init_agent.sh"), str(target)],
            capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("looks like claude_init_setup itself", res.stderr)
        self.assertFalse((target / "CLAUDE.md").exists())

    def test_ordinary_target_is_unaffected(self):
        # Point both repo env vars at an empty local dir so this stays network-free -- the
        # guard runs before either repo is resolved, so it doesn't matter that install.sh
        # itself will then fail against an empty "repo".
        empty_repo = self._tmp / "empty-repo"
        empty_repo.mkdir()
        target = self._tmp / "ordinary-project"
        target.mkdir()
        env = {
            **os.environ,
            "INIT_AGENT_MEMORY_BANK_REPO": str(empty_repo),
            "INIT_AGENT_TICKET_WORKFLOW_REPO": str(empty_repo),
        }
        res = subprocess.run(
            ["bash", str(ORCHESTRATOR / "init_agent.sh"), str(target)],
            env=env, capture_output=True, text=True,
        )
        self.assertNotIn("looks like claude_init_setup itself", res.stderr)


if __name__ == "__main__":
    unittest.main()
