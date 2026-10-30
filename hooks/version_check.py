"""SessionStart hook (startup, resume, clear): show which Software Factory version is running
and whether a newer one is published on GitHub main.

The latest version is fetched at most every 6 hours (cached), with a 2-second timeout. Offline or
on any error it still shows the installed version and never blocks the session.
"""

import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request

from factory_scope import factory_roots

LATEST_URL = "https://raw.githubusercontent.com/achisolomon/software-factory/main/.claude-plugin/plugin.json"
CACHE_SECONDS = 6 * 3600
VERSION = re.compile(r"^\d+(\.\d+){1,3}$")
UPDATE = ("claude plugin marketplace update software-factory-marketplace && "
          "claude plugin update software-factory@software-factory-marketplace --scope user")


def version_of(text):
    """The version string from plugin.json text, or None if it is missing or not a plain version."""
    try:
        version = json.loads(text).get("version")
    except (ValueError, AttributeError):
        return None
    return version if isinstance(version, str) and VERSION.match(version) else None


def installed():
    root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[1])
    try:
        return version_of((root / ".claude-plugin" / "plugin.json").read_text())
    except OSError:
        return None


def latest():
    data_dir = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".cache" / "software-factory")
    cache = data_dir / "latest-version.json"
    try:
        cached = json.loads(cache.read_text())
        if time.time() - cached["checked"] < CACHE_SECONDS:
            return cached.get("latest")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    try:
        url = os.environ.get("SOFTWARE_FACTORY_LATEST_URL", LATEST_URL)
        with urllib.request.urlopen(url, timeout=2) as response:
            found = version_of(response.read(65536).decode("utf-8", "replace"))
    except Exception:
        found = None
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"checked": time.time(), "latest": found}))
    except OSError:
        pass
    return found


def as_tuple(version):
    return tuple(int(part) for part in version.split("."))


def compact_note(cwd):
    """Context for the Team Lead when a factory session starts without an auto-compact threshold, else ''."""
    if os.environ.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE") or not factory_roots(cwd):
        return ""
    settings = Path(cwd) / ".claude" / "settings.json"
    return (f" No auto-compact threshold is set for sessions started in {cwd}, so compaction waits until the "
            f"context is nearly full. If you act as the Team Lead, tell the user once and offer "
            f"/software-factory:session-setup, which writes env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE to {settings} "
            f"(the folder sessions start from, which covers every repo below it).")


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = None
    cwd = str((payload.get("cwd") if isinstance(payload, dict) else None) or os.getcwd())
    current = installed()
    if not current:
        return 0
    newest = latest()
    if newest and as_tuple(newest) > as_tuple(current):
        message = (f"Software Factory v{current} is running. v{newest} is available. To update, ask Claude to "
                   f"\"update the software factory\", or paste this in the VS Code terminal (Terminal > New "
                   f"Terminal): {UPDATE}. Then run Developer: Reload Window and start a new chat.")
        context = (f"Software Factory plugin v{current} is loaded; v{newest} is available. If you act as the "
                   f"Team Lead, start your first status this session with \"Software Factory v{current}\" and tell "
                   f"the user once that v{newest} is available. If the user asks to update the Software Factory, "
                   f"run this with Bash (the user approves it): {UPDATE}. Then tell them to run Developer: Reload "
                   f"Window (or restart Claude Code) and start a new chat.")
    else:
        message = f"Software Factory v{current}" + (" (latest)." if newest else ".")
        context = (f"Software Factory plugin v{current} is loaded. If you act as the Team Lead, start your first "
                   f"status this session with \"Software Factory v{current}\". If the user asks to update the "
                   f"Software Factory, run this with Bash (the user approves it): {UPDATE}. Then tell them to run "
                   f"Developer: Reload Window (or restart Claude Code) and start a new chat.")
    try:
        note = compact_note(cwd)
    except Exception:  # never block the session start over this check
        note = ""
    if note:
        context += note
        message += " Auto-compact threshold not set for this folder: run /software-factory:session-setup."
    print(json.dumps({"systemMessage": message,
                      "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
