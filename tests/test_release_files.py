"""The release files must agree with the plugin: version, agent count, eval count."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class ReleaseFilesTests(unittest.TestCase):
    def test_plugin_version_matches_newest_changelog_heading(self):
        version = json.loads(read(".claude-plugin/plugin.json"))["version"]
        newest = re.search(r"^## (\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(version, newest)

    def test_readme_current_version_matches_plugin(self):
        version = json.loads(read(".claude-plugin/plugin.json"))["version"]
        self.assertIn(f"Current version: {version}.", read("README.md"))

    def test_readme_agent_count_matches_agent_files(self):
        count = len(list((ROOT / "agents").glob("*.md")))
        self.assertIn(f"{count} agents, what each one does", read("README.md"))

    def test_readme_eval_count_matches_eval_prompts(self):
        count = len(list((ROOT / "evals").glob("*/prompt.md")))
        self.assertIn(f"{count} behavior evals", read("README.md"))

    def test_readme_lists_every_agent_in_team_table(self):
        readme = read("README.md")
        self.assertIn("**Exploratory QA Engineer**", readme)

    def test_provenance_records_tester_army_e2e(self):
        provenance = read("docs/provenance.md")
        for needle in ("tester-army/e2e", "2026-11-02", "Apache-2.0"):
            self.assertIn(needle, provenance)

    def test_release_files_contain_no_em_dash(self):
        for name in ("CHANGELOG.md", "README.md", "docs/provenance.md", "docs/index.html"):
            self.assertNotIn("—", read(name), name)


if __name__ == "__main__":
    unittest.main()
