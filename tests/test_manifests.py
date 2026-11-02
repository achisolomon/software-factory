"""The plugin lives in plugin/; the marketplace and the old-install version pointer stay at the root."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


class ManifestTests(unittest.TestCase):
    def test_marketplace_points_at_the_plugin_folder(self):
        entry = load(".claude-plugin/marketplace.json")["plugins"][0]
        plugin = load("plugin/.claude-plugin/plugin.json")
        self.assertEqual(entry["source"], "./plugin")
        self.assertEqual(entry["name"], plugin["name"])

    def test_root_version_pointer_matches_the_plugin(self):
        # Installs before 0.8.0 read the root file to learn about updates.
        self.assertEqual(load(".claude-plugin/plugin.json")["version"],
                         load("plugin/.claude-plugin/plugin.json")["version"])

    def test_update_check_reads_the_plugin_manifest(self):
        hook = (ROOT / "plugin/hooks/version_check.py").read_text()
        self.assertIn("/main/plugin/.claude-plugin/plugin.json", hook)

    def test_dev_folders_stay_out_of_the_plugin(self):
        for name in ("evals", "tests", "docs", "assets"):
            self.assertFalse((ROOT / "plugin" / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
