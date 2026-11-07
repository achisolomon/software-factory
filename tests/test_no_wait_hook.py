"""hooks/no_wait.py: factory subagents may not block their turn waiting on CI or polling loops.

Replays the waits seen in two runs of 2026-11-03 to 06: `gh pr checks --watch` (9 hours over 4 calls) and
`until grep ...; do sleep` loops.
"""

import json
import unittest

from test_hooks import DEV, run


def decide(command, agent=DEV, agent_id="a1", background=False):
    payload = {"tool_name": "Bash", "tool_input": {"command": command, "run_in_background": background},
               "agent_type": agent, "agent_id": agent_id}
    result = run("no_wait.py", payload)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] if result.stdout.strip() else None


class NoWaitTests(unittest.TestCase):
    def test_denies_foreground_waits(self):
        for command in ("gh pr checks 41 --watch --fail-fast",
                        "gh run watch 123456 --exit-status",
                        "until grep -q ready emu.log; do sleep 2; done",
                        "while ! curl -s localhost:8080; do sleep 5; done",
                        "for i in $(seq 1 60); do gh run view 1 && break; sleep 10; done",
                        "sleep 120",
                        "npm test; sleep 2m"):
            with self.subTest(command=command):
                self.assertEqual(decide(command), "deny")

    def test_allows_short_sleeps_plain_loops_and_background_jobs(self):
        for command in ("sleep 3", "gh pr checks 41", "gh run view 123 --log-failed",
                        "for f in a b; do echo $f; done", 'echo "waiting for x"; sleep 5'):
            with self.subTest(command=command):
                self.assertIsNone(decide(command))
        self.assertIsNone(decide("gh pr checks 41 --watch", background=True))

    def test_main_session_and_other_agents_are_not_limited(self):
        self.assertIsNone(decide("gh run watch 1", agent_id=""))
        self.assertIsNone(decide("gh run watch 1", agent="Explore"))

    def test_bad_input_never_blocks(self):
        result = run("no_wait.py", None, raw="not json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
