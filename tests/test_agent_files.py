"""Phrase checks for the exploratory-QA wiring in the agent files and the contract."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class QuarantineWiring(unittest.TestCase):
    def test_test_engineer_defines_quarantine_marker(self):
        self.assertIn("QUARANTINE: <issue url>", text("agents/test-automation-engineer.md"))

    def test_test_engineer_requires_skip_unless_stack_guard(self):
        self.assertIn("skip-unless-stack guard", text("agents/test-automation-engineer.md"))

    def test_quarantine_is_carved_out_of_never_skip_rule(self):
        self.assertIn("is not a skip", text("agents/test-automation-engineer.md"))


class ExplorerWiring(unittest.TestCase):
    def test_contract_lists_explorer_and_untrusted_app_output(self):
        contract = text("reference/handoff-contract.md")
        self.assertIn("software-factory:exploratory-qa-engineer", contract)
        self.assertIn("output of the application under test", contract)

    def test_team_lead_triggers_explorer_at_epic_end_only(self):
        lead = text("agents/team-lead.md")
        self.assertIn("Run the Exploratory QA Engineer on the epic's stories", lead)
        self.assertIn("any review or exploratory session touching auth", lead)


if __name__ == "__main__":
    unittest.main()
