"""Tripwire: a new network, process or dynamic-code capability in hooks/ must fail CI until allowlisted on purpose."""

import ast
from pathlib import Path
import tempfile
import unittest


HOOKS = Path(__file__).resolve().parents[1] / "hooks"
FLAGGED_MODULES = {"socket", "subprocess", "urllib", "http", "requests", "ctypes"}
FLAGGED_CALLS = {"os.system", "eval", "exec"}
# (hook file, capability) pairs that were reviewed and accepted. Edit only after reading the diff.
ALLOWLIST = {("version_check.py", "urllib")}
# shortcut: __import__ and importlib are not caught, so a dynamic import slips through; upgrade if hooks ever need them.


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def capabilities(source):
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            found.add(dotted_name(node.func))
    return found & (FLAGGED_MODULES | FLAGGED_CALLS)


def violations(hooks_dir, allowlist):
    return sorted(
        (path.name, capability)
        for path in Path(hooks_dir).glob("*.py")
        for capability in capabilities(path.read_text(encoding="utf-8"))
        if (path.name, capability) not in allowlist
    )


def failure_message(found):
    listing = ", ".join(f"{name} uses {capability}" for name, capability in found)
    return (
        f"New hook capability: {listing}. Review the diff of this hook. "
        "If the capability is intended, edit ALLOWLIST in tests/test_hook_capabilities.py deliberately."
    )


class HookCapabilityTests(unittest.TestCase):
    def test_current_hooks_use_only_allowlisted_capabilities(self):
        found = violations(HOOKS, ALLOWLIST)
        self.assertEqual([], found, failure_message(found))

    def test_allowlist_entry_is_still_needed(self):
        self.assertIn(("version_check.py", "urllib"), violations(HOOKS, set()))


class ScannerTests(unittest.TestCase):
    def scan(self, source):
        with tempfile.TemporaryDirectory(prefix="hookcap-") as folder:
            (Path(folder) / "hook.py").write_text(source, encoding="utf-8")
            return violations(folder, set())

    def test_flags_module_imports(self):
        self.assertEqual([("hook.py", "subprocess")], self.scan("import subprocess\n"))

    def test_flags_from_imports_by_root_module(self):
        self.assertEqual([("hook.py", "urllib")], self.scan("from urllib.request import urlopen\n"))

    def test_flags_dynamic_code_and_os_system(self):
        self.assertEqual(
            [("hook.py", "eval"), ("hook.py", "exec"), ("hook.py", "os.system")],
            self.scan("import os\neval('1')\nexec('x=1')\nos.system('ls')\n"),
        )

    def test_ignores_harmless_code(self):
        self.assertEqual([], self.scan("import json\nimport os\nos.getcwd()\n"))

    def test_failure_message_tells_reviewer_what_to_do(self):
        message = failure_message([("gate.py", "subprocess")])
        self.assertIn("gate.py uses subprocess", message)
        self.assertIn("Review the diff", message)
        self.assertIn("edit ALLOWLIST", message)


if __name__ == "__main__":
    unittest.main()
