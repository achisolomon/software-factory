"""The PreToolUse hook blocks factory dispatches that omit an explicit model."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "require_agent_model.py"


def run_hook(tool_input):
    payload = json.dumps({"tool_name": "Agent", "tool_input": tool_input})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


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
