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

    def test_start_makes_ignored_folder_in_project_and_exports_it(self):
        result = self.run_hook("start")
        folder = self.base / "abc-123"
        self.assertTrue(folder.is_dir())
        self.assertEqual((self.base / ".gitignore").read_text(), "*\n")
        self.assertIn(f"export FACTORY_TMP={folder}", self.env_file.read_text())
        self.assertIn(str(folder), json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_end_deletes_session_folder_and_empty_base(self):
        self.run_hook("start")
        (self.base / "abc-123" / "export").mkdir()
        self.run_hook("end")
        self.assertFalse(self.base.exists())

    def test_end_keeps_other_live_sessions(self):
        self.run_hook("start", "one")
        self.run_hook("start", "two")
        self.run_hook("end", "one")
        self.assertFalse((self.base / "one").exists())
        self.assertTrue((self.base / "two").is_dir())

    def test_start_sweeps_stale_folders_only(self):
        stale, fresh = self.base / "crashed", self.base / "running"
        stale.mkdir(parents=True)
        fresh.mkdir()
        os.utime(stale, (0, 0))
        self.run_hook("start")
        self.assertFalse(stale.exists())
        self.assertTrue(fresh.is_dir())

    def test_unsafe_session_id_cannot_escape_base(self):
        self.run_hook("start", "../../evil")
        self.assertFalse((Path(self.tmp.name) / "evil").exists())
        self.assertTrue((self.base / "evil").is_dir())


if __name__ == "__main__":
    unittest.main()
