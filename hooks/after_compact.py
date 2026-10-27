"""SessionStart hook (matcher compact): remind a compacted Team Lead to resume safely.

Only speaks in projects that run the factory (docs/factory/status.md exists).
"""

import json
import os
from pathlib import Path
import sys


def main():
    try:
        payload = json.load(sys.stdin)
        cwd = str((payload.get("cwd") if isinstance(payload, dict) else None) or os.getcwd())
        if not any(os.path.isfile(os.path.join(p, "docs", "factory", "status.md"))
                   for p in [cwd, *map(str, Path(cwd).parents)]):
            return 0
        root = os.environ.get("CLAUDE_PLUGIN_ROOT")
        lead = f"{root}/agents/team-lead.md" if root else "the plugin's agents/team-lead.md"
        contract = f"{root}/reference/handoff-contract.md" if root else "the plugin's reference/handoff-contract.md"
        text = (
            "This session was compacted. If you are the Software Factory Team Lead, re-read "
            f"{lead} and {contract}, then run \"Resume after compaction or restart\" "
            "(or /software-factory:resume) before any new dispatch. Never re-dispatch work that "
            "already has a report on disk."
        )
    except Exception:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
