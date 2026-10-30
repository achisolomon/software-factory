"""Offline checks of the behavior eval suite in evals/ (run for real with `claude plugin eval`).

These cost nothing: every case is well formed, every scaffold builds its situation, and the regex graders accept a
correct team table and reject the real pushapp reply that started this suite (backlog 37).
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # shortcut: PyYAML is only needed here; install it to run these checks
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
SAMPLES = Path(__file__).resolve().parent / "eval_samples"
CASES = sorted(p for p in EVALS.iterdir() if (p / "prompt.md").is_file())
GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}


def front_matter(path):
    _, front, body = path.read_text(encoding="utf-8").split("---\n", 2)
    return yaml.safe_load(front) or {}, body


def regex_of(grader):
    flags = re.I if "i" in grader.get("flags", "") else 0
    flags |= re.M if "m" in grader.get("flags", "") else 0
    return re.compile(grader["pattern"], flags)


def passes(grader, text):
    found = bool(regex_of(grader).search(text))
    return found if grader.get("match", "contains") == "contains" else not found


@unittest.skipUnless(yaml, "needs PyYAML")
class EvalSuiteTests(unittest.TestCase):
    def test_cases_are_well_formed(self):
        self.assertGreaterEqual(len(CASES), 8)
        for case in CASES:
            meta, body = front_matter(case / "prompt.md")
            self.assertEqual(meta.get("name"), case.name, case)
            self.assertTrue(body.strip(), f"{case.name}: empty prompt")
            self.assertTrue(set(meta.get("tags", [])) & {"fast", "slow"}, f"{case.name}: tag fast or slow")
            graders = list((case / "graders").glob("*.md"))
            self.assertTrue(graders, f"{case.name}: no graders")
            for g in graders:
                grader, body = front_matter(g)
                self.assertIn(grader.get("type"), GRADER_TYPES, g)
                if grader["type"] == "regex":
                    self.assertNotIn("(?", grader["pattern"].replace("(?=", ""), f"{g}: inline flags; use flags:")
                    regex_of(grader)
                    self.assertFalse(body.strip(), f"{g}: a regex body may be read as the pattern")
                if grader["type"] == "llm":
                    self.assertTrue(grader.get("criteria"), g)
            if (case / "case.yaml").is_file():
                spec = yaml.safe_load((case / "case.yaml").read_text())
                self.assertEqual(spec["schema_version"], "1.1")
                self.assertEqual(spec["name"], case.name)
                script = case / spec["context"]["scaffold_script"]
                self.assertTrue(os.access(script, os.X_OK), f"{script} not executable")

    @unittest.skipUnless(shutil.which("git"), "needs git")
    def test_scaffolds_build_their_situation(self):
        expected = {
            "health-check": lambda w: ("prunable" in git(w, "worktree", "list", "--porcelain")
                                      and (w / ".worktrees/lane-copy/checkout-copy.md").is_file()),
            "board-is-not-approval": lambda w: "helpful-bot" in (w / "docs/factory/inbox/github-activity.md").read_text(),
            "instruction-files-need-security": lambda w: {"CLAUDE.md", ".cursorrules"} <= set(
                git(w, "diff", "--name-only", "main...lane-docs").split()) and not (w / "CLAUDE.md").exists(),
            "wave-done-state-on-disk": lambda w: '"finished"' in (w / ".factory-run/wf_demo-001/journal.jsonl").read_text(),
            "local-tracking-table": lambda w: "T-21 (local)" in (w / "docs/factory/status.md").read_text() and not any(
                "github.com/acme/shop/issues" in p.read_text() for p in w.rglob("*") if p.is_file() and ".git" not in p.parts),
        }
        for case in CASES:
            if not (case / "case.yaml").is_file():
                continue
            spec = yaml.safe_load((case / "case.yaml").read_text())
            with tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                result = subprocess.run(["sh", str(case / spec["context"]["scaffold_script"])], cwd=work,
                                        capture_output=True, text=True,
                                        env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull})
                self.assertEqual(result.returncode, 0, f"{case.name}: {result.stderr}")
                if case.name.startswith("multi-repo"):
                    # The session starts in the workspace; the project is two levels down, next to a plain repo.
                    self.assertFalse((work / "docs").exists(), case.name)
                    self.assertTrue((work / "Projects/shop project/docs/factory/status.md").is_file(), case.name)
                    self.assertTrue((work / "Projects/infra/.git").is_dir(), case.name)
                else:
                    self.assertTrue((work / "docs/factory/status.md").is_file(), case.name)
                if case.name in expected:
                    self.assertTrue(expected[case.name](work), f"{case.name}: situation not built")

    def test_team_table_graders_tell_good_from_bad(self):
        good = (SAMPLES / "team-table-good.md").read_text()
        bad = (SAMPLES / "team-table-bad-pushapp.md").read_text()
        for name in ("team-table-status", "team-table-after-compaction"):
            for g in (EVALS / name / "graders").glob("*.md"):
                grader, _ = front_matter(g)
                if grader["type"] != "regex" or "target" in grader:
                    continue
                self.assertTrue(passes(grader, good), f"{g.name} rejects the correct table")
            failed = [g.name for g in (EVALS / name / "graders").glob("*.md")
                      if front_matter(g)[0]["type"] == "regex" and not passes(front_matter(g)[0], bad)]
            self.assertIn("table-header.md", failed, name)
            self.assertIn("no-lane-summary.md", failed, name)
        compact = front_matter(EVALS / "wave-done-state-on-disk/graders/never-asks-for-compact.md")[0]
        self.assertFalse(passes(compact, bad), "the pushapp reply asked for /compact")

    def test_grader_ids_exist_in_the_fixture(self):
        fixture = "".join(p.read_text() for p in (EVALS / "fixtures/project").rglob("*") if p.is_file())
        for g in EVALS.glob("*/graders/*.md"):
            for agent_id in re.findall(r"a[0-9a-z]{16}", g.read_text()):
                self.assertIn(agent_id, fixture, f"{g}: {agent_id} not in the fixture")

    def test_every_recent_finding_is_covered(self):
        readme = (EVALS / "README.md").read_text()
        for row in range(10, 39):
            self.assertRegex(readme, rf"\|\s*{row}\s*\|", f"backlog row {row} has no line in evals/README.md")


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout


if __name__ == "__main__":
    unittest.main()
