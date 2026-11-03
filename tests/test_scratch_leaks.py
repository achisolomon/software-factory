"""Factory subagents keep every file inside the project.

Replays two leaks from 2026-11-02: Test Automation Engineer runs left 76 `sf-tverify-*` folders, then
`.sf-verify-probe.py`, `.sf-verify-T-010` and friends, in the folder that holds the project, and never deleted them.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from test_hooks import GOOD_REPLY, run

TEST = "software-factory:test-automation-engineer"


class LeakTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.parent = Path(os.path.realpath(self.tmp.name))  # the folder that holds the project, like Git-Achi-gmail/
        self.project = self.parent / "software-factory"
        (self.project / "docs" / "reports").mkdir(parents=True)
        (self.project / "docs" / "reports" / "T-1.md").write_text("report\n")  # GOOD_REPLY lists it
        self.env = {"CLAUDE_PROJECT_DIR": str(self.project)}


class WriteOutsideProjectTests(LeakTestCase):
    def write(self, path, agent=TEST, agent_id="a1", tool="Write"):
        payload = {"tool_name": tool, "tool_input": {"file_path": str(path)}, "cwd": str(self.project),
                   "agent_type": agent, "agent_id": agent_id}
        result = run("project_bounds.py", payload, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"] if result.stdout.strip() else None

    def test_denies_the_probe_script_beside_the_project(self):
        out = self.write(self.parent / ".sf-verify-probe.py")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("FACTORY_TMP", out["permissionDecisionReason"])

    def test_denies_edit_and_relative_escape(self):
        self.assertIsNotNone(self.write("../.sf-verify-issue-minor.md", tool="Edit"))
        self.assertIsNotNone(self.write(Path.home() / "notes.md"))
        self.assertIsNotNone(self.write(self.parent / "software-factory-other" / "x.py"))  # same prefix, other folder

    def test_allows_project_and_scratch_folder(self):
        self.assertIsNone(self.write(self.project / "src" / "app.py"))
        self.assertIsNone(self.write(self.project / ".software-factory-tmp" / "s1" / "probe.py"))
        self.assertIsNone(self.write(self.project / ".claude" / "worktrees" / "t1" / "a.py"))

    def test_main_session_and_other_agents_are_not_limited(self):
        self.assertIsNone(self.write(self.parent / "x.md", agent_id=""))
        self.assertIsNone(self.write(self.parent / "x.md", agent="Explore"))


class LeftoversAtSubagentStopTests(LeakTestCase):
    def stop(self, started_at):
        transcript = self.parent / "transcript.jsonl"
        stamp = datetime.fromtimestamp(started_at, timezone.utc).isoformat().replace("+00:00", "Z")
        transcript.write_text(json.dumps({"timestamp": stamp}) + "\n")
        os.utime(transcript, (0, 0))  # the transcript itself is old, so it is not reported
        payload = {"agent_type": TEST, "last_assistant_message": GOOD_REPLY, "cwd": str(self.project),
                   "agent_transcript_path": str(transcript)}
        result = run("check_reply.py", payload, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def test_blocks_when_folders_appear_beside_the_project(self):
        started_at = time.time() - 5
        (self.parent / ".sf-verify-T-010").mkdir()
        (self.parent / "sf-tverify-home-0qh1mkvr").mkdir()
        out = self.stop(started_at)
        self.assertEqual(out["decision"], "block")
        self.assertIn(".sf-verify-T-010", out["reason"])
        self.assertIn("sf-tverify-home-0qh1mkvr", out["reason"])

    def test_passes_when_nothing_new_appeared(self):
        (self.parent / "older-repo").mkdir()
        self.assertIsNone(self.stop(time.time() + 60))  # everything beside the project predates the run

    def test_files_inside_the_project_are_fine(self):
        started_at = time.time() - 5
        (self.project / ".software-factory-tmp" / "s1").mkdir(parents=True)
        self.assertIsNone(self.stop(started_at))


class RulesPointAtTheProjectScratchFolderTests(unittest.TestCase):
    def test_no_agent_or_contract_sends_scratch_outside_the_project(self):
        root = Path(__file__).resolve().parents[1] / "plugin"
        for path in [*root.glob("agents/*.md"), root / "reference" / "handoff-contract.md"]:
            text = path.read_text()
            for bad in ('"$TMPDIR/', "$TMPDIR/mut", "dir=BASE", "../"):
                self.assertNotIn(bad + "sf-", text, path)
            self.assertNotIn('worktree add "$TMPDIR', text, path)
        self.assertIn("$FACTORY_TMP", (root / "reference" / "handoff-contract.md").read_text())


if __name__ == "__main__":
    unittest.main()
