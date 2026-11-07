"""PreToolUse hook (Write|Edit|NotebookEdit): a factory subagent may only write inside the project folder.

Scratch files belong in $FACTORY_TMP (<project>/.software-factory-tmp/<session id>), which scratch.py deletes when
the session ends. Writing next to the project, in its parent folder or in the user's home leaves files nobody
cleans up (contract rule 9.12).
"""

import json
import os
from pathlib import Path
import sys

from factory_scope import project_root

FACTORY_AGENTS = {path.stem for path in (Path(__file__).resolve().parents[1] / "agents").glob("*.md")}


def outside(path, root, cwd):
    real = Path(os.path.realpath(os.path.join(cwd, os.path.expanduser(path))))
    return real != root and root not in real.parents


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not payload.get("agent_id"):
            return 0  # the main session (the user or the Team Lead) is not limited
        prefix, _, name = str(payload.get("agent_type") or "").rpartition(":")
        if prefix not in ("", "software-factory") or name not in FACTORY_AGENTS:
            return 0
        tool_input = payload.get("tool_input") or {}
        path = tool_input.get("file_path") or tool_input.get("notebook_path")
        if not isinstance(path, str) or not path:
            return 0
        root = project_root(payload)
        if not outside(path, root, str(payload.get("cwd") or root)):
            return 0
    except Exception:
        return 0  # never break the session over a checker fault
    reason = (f"Software Factory: `{path}` is outside the project folder {root}. Factory agents write only inside "
              f"the project. Put scratch files in $FACTORY_TMP ({root}/.software-factory-tmp/<session id>), which is "
              f"deleted when the session ends (contract rule 9.12).")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
