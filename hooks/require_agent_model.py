"""PreToolUse hook: block Software Factory dispatches that omit an explicit model.

Without `model`, a subagent silently runs on its frontmatter fallback, which
hides the Team Lead's per-delegation model choice and inflates Opus usage.
"""

import json
from pathlib import Path
import sys

FACTORY_AGENTS = {path.stem for path in (Path(__file__).resolve().parents[1] / "agents").glob("*.md")}


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0  # not our call to judge malformed input; let the harness handle it
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    if not isinstance(tool_input, dict):
        return 0
    agent = str(tool_input.get("subagent_type") or "")
    prefix, _, name = agent.rpartition(":")
    if prefix not in ("", "software-factory") or name not in FACTORY_AGENTS:
        return 0
    if str(tool_input.get("model") or "").strip():
        return 0
    print(
        f"Blocked: dispatch of {agent} has no explicit `model`. Set `model` on the Agent call "
        "(haiku | sonnet | opus) per the Team Lead model policy in agents/team-lead.md "
        "('Choose the model for each delegation') and the project's Model policy, then retry. "
        "Opus is only for the rows that table lists.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
