"""PreToolUse hook (Bash): a factory subagent never blocks its turn waiting on CI or a polling loop.

On 2026-11-03 to 06, four Developer calls to `gh pr checks --watch` held their agents for 9 hours in total
(contract section 2, "Long jobs"). A wait belongs in the background: start the job with
`run_in_background`, return `Status: in-progress` with `Job:` filled, and the Team Lead resumes the agent.
"""

import json
from pathlib import Path
import re
import sys

FACTORY_AGENTS = {path.stem for path in (Path(__file__).resolve().parents[1] / "agents").glob("*.md")}

WATCH = re.compile(r"\bgh\s+(pr\s+checks\b[^\n;&|]*--watch|run\s+watch)\b")
LOOP_WITH_SLEEP = re.compile(r"\b(while|until|for)\b[\s\S]*\bdo\b[\s\S]*\bsleep\b")
SLEEP = re.compile(r"\bsleep\s+(\d+(?:\.\d+)?)([smhd]?)\b")
MAX_SLEEP_SECONDS = 30  # shortcut: a fixed limit, raise it if a real 30-60 s settle wait shows up in the traces


def blocking(command):
    """Why the command blocks the agent's turn, or None."""
    if WATCH.search(command):
        return "it watches CI until the checks finish"
    if LOOP_WITH_SLEEP.search(command):
        return "it polls in a loop with sleep"
    for amount, unit in SLEEP.findall(command):
        seconds = float(amount) * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        if seconds > MAX_SLEEP_SECONDS:
            return f"it sleeps {amount}{unit or 's'}"
    return None


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not payload.get("agent_id"):
            return 0  # the Team Lead (main session) watches in the background itself
        prefix, _, name = str(payload.get("agent_type") or "").rpartition(":")
        if prefix not in ("", "software-factory") or name not in FACTORY_AGENTS:
            return 0
        tool_input = payload.get("tool_input") or {}
        if tool_input.get("run_in_background"):
            return 0
        why = blocking(str(tool_input.get("command") or ""))
        if not why:
            return 0
    except Exception:
        return 0  # never break the session over a checker fault
    reason = (f"Software Factory: this command blocks your turn ({why}). Do not wait in the foreground. Start "
              f"long jobs with run_in_background, or return `Status: in-progress` with `Job:` naming what to wait "
              f"for (CI run URL, build, emulator); the Team Lead resumes you when it finishes (contract section 2, Long jobs).")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
