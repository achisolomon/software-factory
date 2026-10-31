"""The PreToolUse hook blocks factory dispatches that omit an explicit model."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "require_agent_model.py"


def run_hook(tool_input, cwd=None):
    payload = json.dumps({"tool_name": "Agent", "tool_input": tool_input, "cwd": cwd or str(HOOK.parent)})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


class LookupOnHaikuTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        (self.project / "docs" / "factory").mkdir(parents=True)
        (self.project / "docs" / "factory" / "status.md").write_text("# Status\n")

    def tearDown(self):
        self.tmp.cleanup()

    def explore(self, model=None, prompt="List the files T-24 touches; paths only", cwd=None):
        tool_input = {"subagent_type": "Explore", "prompt": prompt}
        if model is not None:
            tool_input["model"] = model
        return run_hook(tool_input, cwd or str(self.project))

    def test_blocks_explore_on_bigger_model_in_factory_project(self):
        for model in ("sonnet", "opus", None):
            result = self.explore(model)
            self.assertEqual(result.returncode, 2, model)
            self.assertIn("Why not haiku:", result.stderr)

    def test_allows_explore_on_haiku(self):
        for model in ("haiku", "claude-haiku-5-5"):
            self.assertEqual(self.explore(model).returncode, 0, model)

    def test_allows_bigger_model_with_reason(self):
        result = self.explore("sonnet", "Trace why installs count 0.\nWhy not haiku: needs debugging judgment")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_reason_does_not_count(self):
        self.assertEqual(self.explore("sonnet", "Find splash.\nWhy not haiku:").returncode, 2)

    def test_multi_repo_workspace_counts(self):
        workspace = Path(self.tmp.name) / "ws"
        (workspace / "repo" / "docs" / "factory").mkdir(parents=True)
        (workspace / "repo" / "docs" / "factory" / "status.md").write_text("# Status\n")
        self.assertEqual(self.explore("sonnet", cwd=str(workspace)).returncode, 2)

    def test_ignores_explore_outside_factory_projects(self):
        with tempfile.TemporaryDirectory() as plain:
            self.assertEqual(self.explore("sonnet", cwd=plain).returncode, 0)


class AgentModelHookTests(unittest.TestCase):
    def test_blocks_factory_agent_without_model(self):
        for agent in ("software-factory:software-architect", "software-architect"):
            result = run_hook({"subagent_type": agent, "prompt": "Review T-1"})
            self.assertEqual(result.returncode, 2, agent)
            self.assertIn("explicit `model`", result.stderr)

    def test_blocks_blank_model(self):
        result = run_hook({"subagent_type": "software-factory:triage-classifier", "model": " "})
        self.assertEqual(result.returncode, 2)

    def test_allows_factory_agent_with_model(self):
        result = run_hook({"subagent_type": "software-factory:software-architect", "model": "sonnet"})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ignores_other_agents(self):
        for agent in ("Explore", "general-purpose", "other-plugin:software-architect", ""):
            self.assertEqual(run_hook({"subagent_type": agent}).returncode, 0, agent)

    def test_ignores_malformed_input(self):
        result = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_ignores_non_object_json(self):
        for raw in ("null", "[1]", '"x"', '{"tool_input": [1]}'):
            result = subprocess.run([sys.executable, str(HOOK)], input=raw, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, raw)


if __name__ == "__main__":
    unittest.main()
