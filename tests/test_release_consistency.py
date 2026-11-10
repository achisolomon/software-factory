"""Release consistency: plugin.json version, CHANGELOG top entry and marketplace.json agree."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"
CHANGELOG = ROOT / "CHANGELOG.md"

# Same shape as VERSION in hooks/version_check.py.
VERSION = re.compile(r"^\d+(\.\d+){1,3}$")
# Release headings look like "## 0.7.0 (2026-11-01)".
CHANGELOG_HEADING = re.compile(r"^## (\d+(?:\.\d+){1,3})\b", re.MULTILINE)


class ReleaseConsistencyTests(unittest.TestCase):
    def test_plugin_version_is_a_plain_version(self):
        version = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]

        self.assertRegex(version, VERSION)

    def test_plugin_version_matches_first_changelog_heading(self):
        version = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]
        first = CHANGELOG_HEADING.search(CHANGELOG.read_text(encoding="utf-8"))

        self.assertIsNotNone(first, "CHANGELOG.md has no '## X.Y.Z' heading")
        self.assertEqual(version, first.group(1), "plugin.json version and newest CHANGELOG heading differ")

    def test_marketplace_json_carries_no_version(self):
        marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))

        self.assertNotIn("version", marketplace)
        for plugin in marketplace.get("plugins", []):
            self.assertNotIn("version", plugin)


if __name__ == "__main__":
    unittest.main()
