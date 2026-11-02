"""SessionStart / SessionEnd hook: give each session one scratch folder inside the project and delete it
when the session ends.

  python3 scratch.py start   SessionStart: export FACTORY_TMP=<project>/.software-factory-tmp/<session_id> to Bash,
                             keep .software-factory-tmp out of git, and delete folders crashed sessions left behind.
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


def scratch_paths(payload):
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    base = project / ".software-factory-tmp"
    session = "".join(c for c in str(payload.get("session_id") or "") if c.isalnum() or c in "-_")
    return project, base, (base / session if session else None)


def remove(folder, project):
    shutil.rmtree(folder, ignore_errors=True)
    # a worktree made inside the folder leaves a registration behind
    subprocess.run(["git", "-C", str(project), "worktree", "prune"], capture_output=True, timeout=5)


def start(payload):
    project, base, folder = scratch_paths(payload)
    if folder is None:
        return
    folder.mkdir(parents=True, exist_ok=True)
    (base / ".gitignore").write_text("*\n")  # ignores itself, so no project .gitignore edit is needed
    now = time.time()
    for old in base.iterdir():
        if old.is_dir() and old != folder and now - old.stat().st_mtime > STALE_SECONDS:
            remove(old, project)
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"export FACTORY_TMP={shlex.quote(str(folder))}\n")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": (
        f"Scratch folder for this session: {folder} (also $FACTORY_TMP in Bash). Put every scratch file, "
        f"export, fake HOME and throwaway worktree there, never outside the project; it is deleted when the "
        f"session ends.")}}))


def end(payload):
    project, base, folder = scratch_paths(payload)
    if folder is not None and folder.is_dir():
        remove(folder, project)
    if base.is_dir() and {p.name for p in base.iterdir()} <= {".gitignore"}:
        shutil.rmtree(base, ignore_errors=True)


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
