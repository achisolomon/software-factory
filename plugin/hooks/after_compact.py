"""SessionStart hook (matcher compact): remind a compacted Team Lead to resume safely.

Only speaks in projects that run the factory (docs/factory/status.md exists).
Also injects the Team table section itself: a reminder to re-read was ignored after compaction.
"""

import json
import os
from pathlib import Path
import sys

from factory_scope import factory_roots


def main():
    try:
        payload = json.load(sys.stdin)
        cwd = str((payload.get("cwd") if isinstance(payload, dict) else None) or os.getcwd())
        projects = factory_roots(cwd)
        if not projects:
            return 0
        root = os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).resolve().parents[1])
        lead = f"{root}/agents/team-lead.md"
        contract = f"{root}/reference/handoff-contract.md"
        text = (
            "This session was compacted. If you are the Software Factory Team Lead, re-read "
            f"{lead} and {contract} now with the Read tool (the compaction summary is not a substitute), "
            "then run \"Resume after compaction or restart\" (or /software-factory:resume) before any "
            "new dispatch. Never re-dispatch work that already has a report on disk. Your next status "
            "starts with the Team table below. Factory project status: "
            + ", ".join(str(p / "docs" / "factory" / "status.md") for p in projects) + "."
        )
        try:
            lead_text = Path(lead).read_text(encoding="utf-8")
        except OSError:
            lead_text = ""
        start = lead_text.find("# Team table")
        end = lead_text.find("\n# ", start + 1)
        if start != -1:
            text += "\n\n" + lead_text[start:end if end != -1 else None].strip()
    except Exception:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
