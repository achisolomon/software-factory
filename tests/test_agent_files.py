"""Structure checks for agents/exploratory-qa-engineer.md (frontmatter, required phrases, report order)."""

from pathlib import Path
import unittest

AGENT = Path(__file__).resolve().parents[1] / "agents" / "exploratory-qa-engineer.md"

REQUIRED_PHRASES = [
    "QUARANTINE: <issue url>",
    "expectedFailure",
    "3 of 3",
    "intent unverified",
    "direct-write state",
    "first code read",
    "skills/frontend-testing",
    "id, title and severity only",
    "FIRESTORE_EMULATOR_HOST",
    "docker compose down -v",
    "30 actions",
]

REPORT_ORDER = [
    "Confirmed bugs by severity",
    "Environment risks",
    "Rejected findings",
    "Warnings, flaky results",
    "Charters run",
    "Environment and commit",
    "State setups",
    "Log error counts",
    "Secret-scan result",
    "Repro tests added",
    "First code read",
]


def split_agent():
    text = AGENT.read_text(encoding="utf-8")
    _, front, body = text.split("---\n", 2)
    fields = dict(line.split(": ", 1) for line in front.strip().splitlines())
    return fields, body


class ExploratoryQaAgentFileTests(unittest.TestCase):
    def setUp(self):
        self.fields, self.body = split_agent()

    def test_frontmatter_fields(self):
        self.assertEqual(self.fields["name"], "exploratory-qa-engineer")
        self.assertEqual(self.fields["model"], "sonnet")
        self.assertEqual(self.fields["color"], "yellow")
        self.assertEqual(self.fields["memory"], "project")
        self.assertEqual(self.fields["tools"], "Read, Grep, Glob, Write, Edit, Bash, WebSearch, WebFetch")
        self.assertTrue(self.fields["description"])

    def test_color_is_not_orange(self):
        self.assertNotEqual(self.fields["color"].lower(), "orange")

    def test_required_phrases_present(self):
        lowered = self.body.lower()
        for phrase in REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), lowered)

    def test_report_sections_in_order(self):
        report = self.body.split("# Report", 1)[1].split("# Hard rules", 1)[0]
        positions = [report.find(title) for title in REPORT_ORDER]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

    def test_no_em_dash(self):
        self.assertNotIn(chr(0x2014), AGENT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
