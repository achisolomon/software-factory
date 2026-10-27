"""UserPromptSubmit hook: saying "team lead" or "team leader" hands the session to the Team Lead.

Adds context only; never blocks a prompt.
"""

import json
import re
import sys

TRIGGER = re.compile(r"^\W*(?:(?:hey|hi|ok|okay)\s+)?team[\s-]?lead(?:er)?\b|\bteam[\s-]?lead(?:er)?\s*[,:]", re.I)
STRIP = re.compile(r"<ide_[a-z_]+>.*?</ide_[a-z_]+>|<system-reminder>.*?</system-reminder>", re.S)
CONTEXT = (
    "If the user is addressing the Software Factory Team Lead (not just mentioning someone's team lead), "
    "and this session is not already acting as the Team Lead, invoke the software-factory:team-lead skill now "
    "and follow it; if it already is, just continue as the Team Lead."
)


def main():
    try:
        payload = json.load(sys.stdin)
        prompt = payload.get("prompt") if isinstance(payload, dict) else None
        if not isinstance(prompt, str) or not TRIGGER.search(STRIP.sub("", prompt).strip()):
            return 0
    except Exception:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CONTEXT}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
