"""Tests for scripts/review-route (stdin JSON mode and a real git repo)."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review-route"


def route_json(changes=None, raw=None):
    data = raw if raw is not None else json.dumps({"changes": changes})
    result = subprocess.run([sys.executable, str(SCRIPT), "--changes-json"], input=data, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def required(out):
    return {name for name, level in out["reviewers"].items() if level == "required"}


class ReviewRouteTests(unittest.TestCase):
    def assert_routes(self, change, reviewers, depth="standard"):
        out = route_json([change])
        self.assertEqual(required(out), {"architect", "test"} | set(reviewers), change)
        self.assertEqual(out["depth"], depth, change)
        self.assertEqual(out["action"], "route-only")
        return out

    def test_plain_change_needs_only_the_fixed_reviewers(self):
        out = self.assert_routes({"path": "src/util.py", "added": ["def add(a, b):", "    return a + b"]}, [])
        self.assertEqual(out["reviewers"]["security"], "optional")
        self.assertEqual(out["reasons"], [])

    def test_security_rules(self):
        cases = [
            {"path": "src/api.py", "removed": ["    require_auth(request)"], "added": []},  # deleted guard
            {"path": "src/api.py", "added": ["if (!user.isAdmin) throw new Forbidden()"]},
            {"path": "src/userAcl.ts", "added": ["x"]},
            {"path": "src/client.ts", "added": ["const r = await fetch(url)"]},
            {"path": "app/hooks.py", "added": ["requests.post(WEBHOOK_URL)"]},
            {"path": "package-lock.json", "added": ["x"]},
            {"path": "requirements-dev.txt", "added": ["x"]},
            {"path": "db/migrations/001_init.sql", "added": ["create table t ();"]},
            {"path": "prisma/schema.prisma", "added": ["model User {}"]},
            {"path": "src/new_name.py", "old_path": "src/session_store.py", "added": [], "removed": []},
        ]
        for change in cases:
            out = self.assert_routes(change, ["security"])
            self.assertTrue(any(r.startswith("security: ") for r in out["reasons"]), change)

    def test_security_words_need_a_boundary_for_short_terms(self):
        self.assert_routes({"path": "src/processor.py", "added": ["miracle = oracle_like"]}, [])

    def test_ux_rules(self):
        for change in ({"path": "web/src/components/Button.tsx", "added": ["<button/>"]},
                       {"path": "styles/site.scss", "added": ["a {}"]},
                       {"path": "android/app/src/main/res/values/strings.xml", "added": ["<string/>"]},
                       {"path": "ios/App/Home.swift", "added": ["struct Home: View {"]}):
            self.assert_routes(change, ["ux"])
        self.assert_routes({"path": "ios/App/Math.swift", "added": ["func add() {}"]}, [])

    def test_finops_and_devops_rules(self):
        self.assert_routes({"path": "infra/main.tf", "added": ["x = 1"]}, ["finops", "devops"])
        self.assert_routes({"path": "Dockerfile", "added": ["FROM python"]}, ["finops", "devops"])
        self.assert_routes({"path": "wrangler.toml", "added": ["name = 'x'"]}, ["finops"])
        self.assert_routes({"path": "config/app.yaml", "added": ["log_retention_days: 30"]}, ["finops"])
        self.assert_routes({"path": "manifests/api.yaml", "added": ["apiVersion: apps/v1", "kind: Deployment"]},
                           ["finops"])
        self.assert_routes({"path": ".github/workflows/ci.yml", "added": ["on: push"]}, ["finops", "devops"], "deep")

    def test_deep_rules(self):
        for path in ("agents/team-lead.md", "reference/handoff-contract.md", "hooks/gate.py",
                     "skills/build/SKILL.md", "CLAUDE.md", "pkg/AGENTS.md", ".claude/settings.json",
                     "tests/fixtures/expected.json", "src/__snapshots__/a.snap", ".husky/pre-commit"):
            out = route_json([{"path": path, "added": ["x"]}])
            self.assertEqual(out["depth"], "deep", path)
            self.assertIn(f"deep: {path}", out["reasons"])

    def test_incomplete_evidence_is_deep_and_unresolved(self):
        out = route_json([{"path": "assets/logo.png", "binary": True}])
        self.assertEqual(out["depth"], "deep")
        self.assertIn("unresolved: assets/logo.png", out["reasons"])
        out = route_json([{"path": "src/a.py"}])
        self.assertIn("unresolved: src/a.py", out["reasons"])
        out = route_json([])
        self.assertEqual(out["depth"], "deep")
        self.assertIn("unresolved: (empty diff)", out["reasons"])

    def test_unreadable_input_requires_every_reviewer(self):
        for raw in ("not json", "{}", json.dumps({"changes": [{"added": ["x"]}]}),
                    json.dumps({"changes": [{"path": "a", "added": 3}]})):
            out = route_json(raw=raw)
            self.assertEqual(set(out["reviewers"].values()), {"required"}, raw)
            self.assertEqual(out["depth"], "deep")
            self.assertTrue(out["reasons"][0].startswith("unresolved: "))


class ReviewRouteGitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("symbolic-ref", "HEAD", "refs/heads/main")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "api.py").write_text("def handler(request):\n    check_token(request)\n    return 1\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "init")
        self.git("checkout", "-q", "-b", "feature")

    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
                        *args], cwd=self.repo, check=True, capture_output=True)

    def route(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_removed_guard_and_untracked_ui_file(self):
        (self.repo / "src" / "api.py").write_text("def handler(request):\n    return 1\n")
        (self.repo / "src" / "components").mkdir()
        (self.repo / "src" / "components" / "Card.tsx").write_text("export const Card = () => null\n")
        out = self.route()
        self.assertEqual(required(out), {"architect", "test", "security", "ux"})
        self.assertIn("security: src/api.py", out["reasons"])
        self.assertIn("ux: src/components/Card.tsx", out["reasons"])
        self.assertEqual(out["depth"], "standard")

    def test_committed_change_on_branch(self):
        (self.repo / "Dockerfile").write_text("FROM python:3.12\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "docker")
        out = self.route("main")
        self.assertIn("devops: Dockerfile", out["reasons"])

    def test_empty_diff_and_bad_base(self):
        out = self.route()
        self.assertIn("unresolved: (empty diff)", out["reasons"])
        out = self.route("no-such-branch")
        self.assertEqual(set(out["reviewers"].values()), {"required"})
        self.assertEqual(out["depth"], "deep")

    def test_is_executable(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK))


if __name__ == "__main__":
    unittest.main()
