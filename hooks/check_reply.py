"""SubagentStop hook: send a factory specialist back when its reply breaks the contract reply format.

Checks the required lines of contract section 10 and that every docs/ report the
reply lists in Files: is on disk (rule 9.8). Blocks at most once per stop: when
stop_hook_active is set the agent is already fixing its reply, so it passes.
"""

import json
import os
from pathlib import Path
import re
import sys

from factory_scope import factory_roots

FACTORY_AGENTS = {path.stem for path in (Path(__file__).resolve().parents[1] / "agents").glob("*.md")}
STATUSES = ("done", "needs-input", "blocked", "in-progress")
REQUIRED = ("Summary", "Files", "Claims", "Revision", "Logs", "Checks run")
LABELS = ("Status", "Summary", "Verdict", "Files", "Issues", "Top issues", "Claims", "Revision", "Logs", "Job",
          "Questions for the user", "Handoffs", "Brain notes", "Checks run")
EMPTY = {"", "n/a", "na", "none", "-"}
DOCS_PATH = re.compile(r"(?<![\w/.-])(?:\./)?(docs/[^\s,;:)\]`'\"*#]+)")


def label_re(label):
    # Case-sensitive label at line start; markdown bullets, numbering, bold or backticks may come before it.
    return re.compile(r"^[ \t>*\-+_`#\d.]*" + re.escape(label) + r"[*_`]*:[*_`]*[ \t]*(.*)$")


LABEL_RES = {label: label_re(label) for label in LABELS}


def section(lines, label):
    """The text after `label:` plus following lines up to the next label, or None when the label is missing."""
    for k, line in enumerate(lines):
        m = LABEL_RES[label].match(line)
        if m:
            out = [m.group(1)]
            for rest in lines[k + 1:]:
                if any(r.match(rest) for r in LABEL_RES.values()):
                    break
                out.append(rest)
            return "\n".join(out).strip()
    return None


def clean(value):
    return value.strip().strip("*`_").strip()


def problems(message, cwd):
    lines = message.splitlines()
    found = []
    status_text = section(lines, "Status")
    status = None
    if status_text is None:
        found.append("missing `Status:` line")
    else:
        m = re.fullmatch(r"(done|needs-input|blocked|in-progress)\b[^|]*", clean((status_text.splitlines() or [""])[0]), re.I)
        if m:
            status = m.group(1).lower()
        else:
            found.append(f"`Status:` must be exactly one of {', '.join(STATUSES)}")
    for label in REQUIRED:
        if section(lines, label) is None:
            found.append(f"missing `{label}:` line")
    if status == "in-progress":
        job = section(lines, "Job")
        if job is None or clean(job).lower().rstrip(".") in EMPTY:
            found.append("`Job:` must name the job id, command, how to check it and expected finish when Status is in-progress")
    if status == "needs-input" and section(lines, "Questions for the user") is None:
        found.append("missing `Questions for the user:` when Status is needs-input")
    if status == "done":
        # docs/ paths are relative to the factory project, which may sit below a multi-repo workspace cwd.
        bases = [cwd, *map(str, factory_roots(cwd))]
        files = section(lines, "Files") or ""
        for item in re.split(r"[\n,]", files):
            if "(deleted)" in item:
                continue
            for path in re.findall(r"`(docs/[^`]+)`", item) or DOCS_PATH.findall(item):
                path = path.split("#", 1)[0].rstrip(".")
                if not any(os.path.exists(os.path.join(base, path)) for base in bases):
                    found.append(f"`{path}` is listed in Files: but is not on disk (write reports before replying, rule 9.8)")
    return found


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("stop_hook_active"):
            return 0
        prefix, _, name = str(payload.get("agent_type") or "").rpartition(":")
        if prefix not in ("", "software-factory") or name not in FACTORY_AGENTS or name == "triage-classifier":
            return 0
        message = payload.get("last_assistant_message")
        if not isinstance(message, str):
            return 0  # this Claude Code version does not send the reply; nothing to judge
        found = problems(message, str(payload.get("cwd") or os.getcwd()))
    except Exception:
        return 0  # never break the session over a checker fault
    if found:
        bullets = "\n".join(f"- {p}" for p in found)
        print(json.dumps({
            "decision": "block",
            "reason": f"Software Factory reply check:\n{bullets}.\nFix your reply (contract section 10) and finish again.",
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
