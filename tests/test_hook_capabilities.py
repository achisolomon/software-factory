"""Tripwire: a new network, process or dynamic-code capability in hooks/ must fail CI until allowlisted on purpose.

Also checks that every registered hook is a scanned top-level hooks/*.py script.
"""

import ast
import json
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
FLAGGED_MODULES = {
    "socket", "subprocess", "urllib", "http", "requests", "ctypes",
    "asyncio", "ftplib", "importlib", "multiprocessing", "pty", "runpy", "smtplib", "ssl", "webbrowser", "xmlrpc",
}
FLAGGED_CALLS = {"eval", "exec", "compile", "__import__"}
OS_PROCESS_CALLS = {
    "system", "popen", "fork", "forkpty",
    "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
    "posix_spawn", "posix_spawnp",
}
# (hook file, capability) pairs that were reviewed and accepted. Edit only after reading the diff.
ALLOWLIST = {("version_check.py", "urllib")}
# shortcut: AST name matching only; getattr, string-built names and rebinding (e = eval) evade it. Full-diff review is the real control; widen the lists if a hook ever needs one of these.
HOOK_COMMAND = re.compile(r'^python3 "\$\{CLAUDE_PLUGIN_ROOT\}/hooks/([a-z_]+\.py)"$')
FRONTMATTER_HOOKS = re.compile(r"^hooks:", re.MULTILINE)


def capabilities(source):
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
            if node.module == "os":
                found.update(f"os.{alias.name}" for alias in node.names if alias.name in OS_PROCESS_CALLS)
        elif isinstance(node, ast.Call):
            found.update(called_capability(node.func))
    return found & (FLAGGED_MODULES | FLAGGED_CALLS | {f"os.{name}" for name in OS_PROCESS_CALLS})


def called_capability(func):
    if isinstance(func, ast.Name):
        return {func.id}
    if isinstance(func, ast.Attribute) and func.attr in OS_PROCESS_CALLS:
        return {f"os.{func.attr}"}
    return set()


def violations(hooks_dir, allowlist):
    hooks_dir = Path(hooks_dir)
    return sorted(
        (path.relative_to(hooks_dir).as_posix(), capability)
        for path in hooks_dir.rglob("*.py")
        for capability in capabilities(path.read_text(encoding="utf-8"))
        if (path.relative_to(hooks_dir).as_posix(), capability) not in allowlist
    )


def failure_message(found):
    listing = ", ".join(f"{name} uses {capability}" for name, capability in found)
    return (
        f"New hook capability: {listing}. Review the diff of this hook. "
        "If the capability is intended, edit ALLOWLIST in tests/test_hook_capabilities.py deliberately."
    )


def registration_message(where):
    return (
        f"Hook registration outside the scanned shape: {where}. "
        'Review the diff; hooks must be `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<file>.py"`.'
    )


def registered_hooks(hooks_json):
    return [
        hook
        for groups in hooks_json["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]


def frontmatter(path):
    parts = path.read_text(encoding="utf-8").split("---", 2)
    return parts[1] if len(parts) == 3 else ""


class HookCapabilityTests(unittest.TestCase):
    def test_current_hooks_use_only_allowlisted_capabilities(self):
        found = violations(HOOKS, ALLOWLIST)
        self.assertEqual([], found, failure_message(found))

    def test_every_allowlist_entry_is_still_needed(self):
        stale = ALLOWLIST - set(violations(HOOKS, set()))
        self.assertEqual(set(), stale, f"Stale ALLOWLIST entries are pre-approved holes; remove them: {sorted(stale)}")


class HookRegistrationTests(unittest.TestCase):
    def test_every_registered_hook_is_a_scanned_python_script(self):
        hooks_json = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
        for hook in registered_hooks(hooks_json):
            with self.subTest(hook=hook):
                self.assertEqual("command", hook.get("type"), registration_message(hook))
                match = HOOK_COMMAND.match(hook.get("command", ""))
                self.assertIsNotNone(match, registration_message(hook))
                self.assertTrue((HOOKS / match.group(1)).is_file(), registration_message(hook))

    def test_manifest_does_not_register_hooks(self):
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifest, registration_message(".claude-plugin/plugin.json"))

    def test_agents_and_skills_do_not_register_hooks_in_frontmatter(self):
        for path in [*ROOT.glob("agents/*.md"), *ROOT.glob("skills/*/SKILL.md")]:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(FRONTMATTER_HOOKS.search(frontmatter(path)), registration_message(path.name))


class ScannerTests(unittest.TestCase):
    def scan(self, source, name="hook.py"):
        with tempfile.TemporaryDirectory(prefix="hookcap-") as folder:
            target = Path(folder) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
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

    def test_flags_from_os_import_of_process_call(self):
        self.assertEqual([("hook.py", "os.system")], self.scan("from os import system\n"))

    def test_flags_process_call_on_aliased_os(self):
        self.assertEqual([("hook.py", "os.popen")], self.scan("import os as o\no.popen('x')\n"))

    def test_flags_os_exec_family(self):
        self.assertEqual([("hook.py", "os.execv")], self.scan("import os\nos.execv('/bin/sh', [])\n"))

    def test_flags_newly_listed_module(self):
        self.assertEqual([("hook.py", "pty")], self.scan("import pty\n"))

    def test_flags_dynamic_import(self):
        self.assertEqual([("hook.py", "__import__")], self.scan("__import__('socket')\n"))

    def test_flags_bare_compile(self):
        self.assertEqual([("hook.py", "compile")], self.scan("compile('1', 'f', 'eval')\n"))

    def test_does_not_flag_re_compile(self):
        self.assertEqual([], self.scan("import re\nre.compile('x')\n"))

    def test_does_not_flag_unrelated_exec_prefixed_call(self):
        self.assertEqual([], self.scan("cursor.execute('x')\n"))

    def test_scans_subfolders_with_relative_path_keys(self):
        self.assertEqual([("sub/x.py", "socket")], self.scan("import socket\n", name="sub/x.py"))

    def test_ignores_harmless_code(self):
        self.assertEqual([], self.scan("import json\nimport os\nos.getcwd()\n"))

    def test_failure_message_tells_reviewer_what_to_do(self):
        message = failure_message([("gate.py", "subprocess")])
        self.assertIn("gate.py uses subprocess", message)
        self.assertIn("Review the diff", message)
        self.assertIn("edit ALLOWLIST", message)


if __name__ == "__main__":
    unittest.main()
