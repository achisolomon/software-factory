"""The scratch hook gives each session a git-ignored folder inside the project and deletes it at session end."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOOK = Path(__file__).resolve().parents[1] / "plugin" / "hooks" / "scratch.py"


class ScratchHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "project"
        self.project.mkdir()
        self.env_file = Path(self.tmp.name) / "env"
        self.base = self.project / ".software-factory-tmp"

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, mode, session="abc-123"):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.project), "CLAUDE_ENV_FILE": str(self.env_file)}
        payload = json.dumps({"session_id": session, "cwd": str(self.project)})
        return subprocess.run([sys.executable, str(HOOK), mode], input=payload, env=env,
                              capture_output=True, text=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.project), *args], capture_output=True, text=True, check=True)

    def test_a_session_that_needs_no_scratch_leaves_the_project_untouched(self):
        self.git("init", "-q")
        (self.project / "app.py").write_text("print(1)\n")
        before = sorted(p.name for p in self.project.iterdir())
        for _ in range(2):  # every new session
            result = self.run_hook("start")
            self.run_hook("end")
        self.assertEqual(sorted(p.name for p in self.project.iterdir()), before)
        self.assertEqual(self.git("status", "--porcelain").stdout, "?? app.py\n")
        folder = self.base / "abc-123"
        self.assertIn(f"export FACTORY_TMP={folder}", self.env_file.read_text())
        self.assertIn(str(folder), json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_scratch_an_agent_makes_is_hidden_from_git_and_gone_at_end(self):
        self.git("init", "-q")
        self.run_hook("start")
        self.run_hook("start")  # the exclude line is written once
        (self.base / "abc-123" / "export").mkdir(parents=True)
        (self.base / "abc-123" / "export" / "x.py").write_text("x\n")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        exclude = (self.project / ".git" / "info" / "exclude").read_text()
        self.assertEqual(exclude.count(".software-factory-tmp/"), 1)
        self.run_hook("end")
        self.assertFalse(self.base.exists())

    def test_end_keeps_other_live_sessions(self):
        for session in ("one", "two"):
            (self.base / session).mkdir(parents=True)
        self.run_hook("end", "one")
        self.assertFalse((self.base / "one").exists())
        self.assertTrue((self.base / "two").is_dir())

    def test_start_sweeps_crash_leftovers_and_the_empty_parent(self):
        stale = self.base / "crashed"
        stale.mkdir(parents=True)
        (self.base / ".gitignore").write_text("*\n")  # left by 0.7.3 / 0.7.4
        os.utime(stale, (0, 0))
        self.run_hook("start")
        self.assertFalse(self.base.exists())

    def test_start_keeps_a_running_session(self):
        (self.base / "running").mkdir(parents=True)
        self.run_hook("start")
        self.assertTrue((self.base / "running").is_dir())

    def test_not_a_git_repo_is_fine(self):
        self.run_hook("start")
        self.assertEqual(list(self.project.iterdir()), [])

    def test_unsafe_session_id_cannot_escape_base(self):
        self.run_hook("start", "../../evil")
        self.assertIn(f"FACTORY_TMP={self.base / 'evil'}", self.env_file.read_text())


if __name__ == "__main__":
    unittest.main()
