"""PreToolUse hook: block Software Factory dispatches that omit an explicit model.

Without `model`, a subagent silently runs on its frontmatter fallback, which
hides the Team Lead's per-delegation model choice and inflates Opus usage.

In a factory project it also blocks a read-only Explore search on a bigger
model than haiku, unless the prompt says why ("Why not haiku: ..."). The model
table puts lookups on haiku, yet Team Leads sent 172 of them to sonnet in one week.
"""

import json
import os
from pathlib import Path
import re
import sys

from factory_scope import factory_roots

FACTORY_AGENTS = {path.stem for path in (Path(__file__).resolve().parents[1] / "agents").glob("*.md")}
LOOKUP_AGENTS = {"Explore"}
WHY_NOT_HAIKU = re.compile(r"why not haiku\s*:\s*\S", re.I)


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0  # not our call to judge malformed input; let the harness handle it
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    if not isinstance(tool_input, dict):
        return 0
    agent = str(tool_input.get("subagent_type") or "")
    model = str(tool_input.get("model") or "").strip()
    if agent in LOOKUP_AGENTS:
        # A missing model counts as not haiku: it inherits the session's model, often opus.
        if ("haiku" not in model.lower() and not WHY_NOT_HAIKU.search(str(tool_input.get("prompt") or ""))
                and factory_roots(str(payload.get("cwd") or os.getcwd()))):
            print(
                f"Blocked: {agent} is a read-only lookup and runs on `haiku` in the Team Lead model policy "
                "(agents/team-lead.md, 'Choose the model for each delegation'). Retry with model `haiku`. "
                "If this search needs judgment haiku lacks, keep the model and add a line "
                "'Why not haiku: <reason>' to the prompt.",
                file=sys.stderr,
            )
            return 2
        return 0
    prefix, _, name = agent.rpartition(":")
    if prefix not in ("", "software-factory") or name not in FACTORY_AGENTS:
        return 0
    if model:
        return 0
    print(
        f"Blocked: dispatch of {agent} has no explicit `model`. Set `model` on the Agent call "
        "(haiku | sonnet | opus | fable) per the Team Lead model policy in agents/team-lead.md "
        "('Choose the model for each delegation') and the project's Model policy, then retry. "
        "Opus is only for the rows that table lists.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
