"""Key Team Lead rules must appear in both the Claude Code agent and the Codex role playbook.

The playbook is a hand-kept copy; this catches a rule added to one and forgotten in the other.
Add a phrase here whenever a rule must hold on both runtimes.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_LEAD = ROOT / "agents" / "team-lead.md"
PLAYBOOK = ROOT / "skills" / "factory-protocol" / "references" / "role-playbook.md"

SHARED_RULES = [
    "Status | Agent | Agent ID | Model | Worktree | Issue | Task | Since / last update",
    "none (coordinator)",
    "inherited from the session",
    "+N more",
    "is never an Issue value",
    "Background processes",
    "completed-unreported",
    "sent-unverified",
    "local-ci-lock.sh",
    "`health` skill",
    "needs-you",
    "never approves a gated action",
    "review-route",
    "A lane summary (Lane | Tasks) never replaces this table",
    "needs no hand-written compact message",
    "the factory project is the repo below it with `docs/factory/status.md`",
    "naming the environment and the load ceiling",
]


class PromptSyncTests(unittest.TestCase):
    def test_shared_rules_in_both_runtimes(self):
        texts = {path.name: " ".join(path.read_text(encoding="utf-8").split()) for path in (TEAM_LEAD, PLAYBOOK)}
        for rule in SHARED_RULES:
            for name, text in texts.items():
                self.assertIn(rule, text, f"{rule!r} missing from {name}")

    def test_health_skill_exists(self):
        self.assertTrue((ROOT / "skills" / "health" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
