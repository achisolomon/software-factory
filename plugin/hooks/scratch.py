"""SessionStart / SessionEnd hook: give each session one scratch folder inside the project and delete it
when the session ends.

  python3 scratch.py start   SessionStart: export FACTORY_TMP=<project>/.software-factory-tmp/<session_id> to Bash,
                             keep .software-factory-tmp out of git, and delete folders crashed sessions left behind.
                             It creates no folder: a session that never needs scratch leaves the project untouched.
  python3 scratch.py end     SessionEnd: delete this session's folder (and .software-factory-tmp once it is empty).

Never blocks the session: any error is swallowed.
"""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

STALE_SECONDS = 24 * 3600  # a folder untouched this long belongs to a session that ended without SessionEnd
IGNORE = ".software-factory-tmp/"


def scratch_paths(payload):
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    base = project / ".software-factory-tmp"
    session = "".join(c for c in str(payload.get("session_id") or "") if c.isalnum() or c in "-_")
    return project, base, (base / session if session else None)


def remove(folder, project):
    shutil.rmtree(folder, ignore_errors=True)
    # a worktree made inside the folder leaves a registration behind
    subprocess.run(["git", "-C", str(project), "worktree", "prune"], capture_output=True, timeout=5)


def remove_if_empty(base):
    # .gitignore is what 0.7.3 and 0.7.4 wrote there; nothing else is left once the session folders are gone
    if base.is_dir() and {p.name for p in base.iterdir()} <= {".gitignore"}:
        shutil.rmtree(base, ignore_errors=True)


def ignore_in_git(project):
    """Keep .software-factory-tmp out of git through .git/info/exclude, which is never shown or committed."""
    found = subprocess.run(["git", "-C", str(project), "rev-parse", "--git-path", "info/exclude"],
                           capture_output=True, text=True, timeout=5)
    if found.returncode:
        return  # not a git repo: nothing to keep out
    exclude = project / found.stdout.strip()  # an absolute path stays absolute
    text = exclude.read_text() if exclude.is_file() else ""
    if IGNORE not in text.splitlines():
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with open(exclude, "a") as f:
            f.write(("" if not text or text.endswith("\n") else "\n") + IGNORE + "\n")


def start(payload):
    project, base, folder = scratch_paths(payload)
    if folder is None:
        return
    if base.is_dir():
        now = time.time()
        for old in base.iterdir():
            if old.is_dir() and old != folder and now - old.stat().st_mtime > STALE_SECONDS:
                remove(old, project)
        remove_if_empty(base)
    ignore_in_git(project)
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"export FACTORY_TMP={shlex.quote(str(folder))}\n")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": (
        f"Scratch folder for this session: {folder} (also $FACTORY_TMP in Bash). It does not exist until you "
        f"need it: create it then (mkdir -p \"$FACTORY_TMP\"). Put every scratch file, export, fake HOME and "
        f"throwaway worktree there, never outside the project; it is deleted when the session ends.")}}))


def end(payload):
    project, base, folder = scratch_paths(payload)
    if folder is not None and folder.is_dir():
        remove(folder, project)
    remove_if_empty(base)


def main():
    try:
        payload = json.load(sys.stdin)
        payload = payload if isinstance(payload, dict) else {}
        {"start": start, "end": end}[sys.argv[1]](payload)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
