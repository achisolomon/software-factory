"""Exercise routing and installation without running model inference."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLES = [path.stem for path in (ROOT / "agents").glob("*.md")]
LUNA_DEFAULTS = {
    "team-lead",
    "triage-classifier",
    "test-automation-engineer",
    "ux-ui-designer",
    "finops-engineer",
}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="factory-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project with spaces"
        self.project.mkdir()

    def run_script(self, name, *args, env=None):
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / name), *args],
            cwd=self.project,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_all_roles_and_modes(self):
        for role in ROLES:
            for mode in ("default", "routine", "quality"):
                with self.subTest(role=role, mode=mode):
                    result = self.run_script(
                        "run-codex-agent",
                        role,
                        "--mode",
                        mode,
                        "--dry-run",
                        "--",
                        "Verify routing",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    expected = "gpt-6.1-sol"
                    if mode == "routine" or (
                        mode == "default" and role in LUNA_DEFAULTS
                    ):
                        expected = "gpt-6-luna"
                    self.assertIn(f"model={expected}\n", result.stdout)

    def test_explicit_override_and_invalid_inputs(self):
        result = self.run_script(
            "run-codex-agent",
            "software-developer",
            "--mode",
            "routine",
            "--model",
            "gpt-6-astra",
            "--dry-run",
            "--",
            "Review evidence",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("model=gpt-6-astra\n", result.stdout)
        for args in [
            ("unknown", "--", "x"),
            ("team-lead", "--mode", "bad", "--", "x"),
            ("team-lead", "--"),
            ("team-lead", "missing separator"),
        ]:
            self.assertEqual(self.run_script("run-codex-agent", *args).returncode, 2)

    def test_actual_dispatch_uses_selected_model_and_literal_task(self):
        binary_dir = Path(self.temp.name) / "bin"
        binary_dir.mkdir()
        fake = binary_dir / "codex"
        fake.write_text(
            "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n"
        )
        fake.chmod(0o755)
        env = dict(os.environ, PATH=f"{binary_dir}{os.pathsep}{os.environ['PATH']}")
        for role in ("team-lead", "software-developer"):
            result = self.run_script(
                "run-codex-agent",
                role,
                "--mode",
                "routine",
                "--",
                "Keep $(touch SHOULD_NOT_EXIST) and `literal` text",
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads(result.stdout)
            self.assertEqual(args[args.index("--model") + 1], "gpt-6-luna")
            self.assertEqual(args[args.index("--cd") + 1], str(self.project.resolve()))
            self.assertEqual(args[0] == "exec", role != "team-lead")
            self.assertIn("$(touch SHOULD_NOT_EXIST)", args[-1])
        self.assertFalse((self.project / "SHOULD_NOT_EXIST").exists())

    def install(self, *args):
        return self.run_script(
            "install-codex-factory", "--project-dir", str(self.project), *args
        )

    def test_update_preserves_customizations_and_project_files(self):
        (self.project / "AGENTS.md").write_text("project instructions")
        docs = self.project / "docs"
        docs.mkdir()
        (docs / "facts.md").write_text("project facts")
        self.assertEqual(self.install().returncode, 0)
        installed = self.project / ".codex/software-factory"
        self.assertTrue((installed / "skills/frontend-testing/SKILL.md").is_file())
        custom = installed / "agents/team-lead.md"
        custom.write_text("local customization")
        self.assertEqual(self.install().returncode, 2)
        result = self.install("--update")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.project / ".codex").glob("software-factory-backup.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(
            (backups[0] / "agents/team-lead.md").read_text(), "local customization"
        )
        self.assertEqual(
            custom.read_bytes(), (ROOT / "agents/team-lead.md").read_bytes()
        )
        self.assertEqual(
            (self.project / "AGENTS.md").read_text(), "project instructions"
        )
        self.assertEqual((docs / "facts.md").read_text(), "project facts")
        self.assertFalse(
            list((self.project / ".codex").glob("software-factory-stage.*"))
        )

    def test_refuses_unknown_installation_and_symlink(self):
        config = self.project / ".codex"
        config.mkdir()
        installed = config / "software-factory"
        installed.mkdir()
        sentinel = installed / "keep.txt"
        sentinel.write_text("keep")
        self.assertEqual(self.install("--update").returncode, 2)
        self.assertEqual(sentinel.read_text(), "keep")

        linked_project = Path(self.temp.name) / "linked-project"
        linked_project.mkdir()
        (linked_project / ".codex").symlink_to(config, target_is_directory=True)
        result = self.run_script(
            "install-codex-factory", "--project-dir", str(linked_project), "--update"
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(sentinel.read_text(), "keep")

    def test_failed_replacement_restores_previous_runtime(self):
        self.assertEqual(self.install().returncode, 0)
        installed = self.project / ".codex/software-factory"
        sentinel = installed / "local.txt"
        sentinel.write_text("keep this runtime")
        binary_dir = Path(self.temp.name) / "failing-bin"
        binary_dir.mkdir()
        fake_mv = binary_dir / "mv"
        real_mv = shutil.which("mv")
        self.assertIsNotNone(real_mv)
        fake_mv.write_text(
            "#!/usr/bin/env python3\nimport os, sys\n"
            "if 'software-factory-stage.' in sys.argv[1]: sys.exit(1)\n"
            f"os.execv({real_mv!r}, [{real_mv!r}, *sys.argv[1:]])\n"
        )
        fake_mv.chmod(0o755)
        env = dict(os.environ, PATH=f"{binary_dir}{os.pathsep}{os.environ['PATH']}")
        result = self.run_script(
            "install-codex-factory",
            "--project-dir",
            str(self.project),
            "--update",
            env=env,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(sentinel.read_text(), "keep this runtime")
        self.assertFalse(
            list((self.project / ".codex").glob("software-factory-stage.*"))
        )

    def test_refuses_updating_from_the_runtime_being_replaced(self):
        self.assertEqual(self.install().returncode, 0)
        installer = (
            self.project / ".codex/software-factory/scripts/install-codex-factory"
        )
        result = subprocess.run(
            ["bash", str(installer), "--project-dir", str(self.project), "--update"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertTrue(installer.is_file())


if __name__ == "__main__":
    unittest.main()
