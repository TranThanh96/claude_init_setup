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
        res = subprocess.run(
            ["bash", str(ORCHESTRATOR / "init_agent.sh"), *args, str(self.root)],
            env=self.env, capture_output=True, text=True,
        )
        print("DEBUG STDOUT:\n" + res.stdout)
        print("DEBUG STDERR:\n" + res.stderr)
        return res


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


if __name__ == "__main__":
    unittest.main()
