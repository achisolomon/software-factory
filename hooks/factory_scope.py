"""Find the Software Factory projects a session can reach: folders with docs/factory/status.md.

A session may start in the project, below it, or in a workspace folder that holds several repos (for example
pushapp/ with Projects/pushapp project/ inside). The hooks use this so they still act in that last case.
"""

import os
from pathlib import Path

MARKER = Path("docs") / "factory" / "status.md"
MAX_DEPTH = 3  # workspace/Projects/<repo> is depth 2; one more level of grouping is allowed
MAX_DIRS = 600  # shortcut: bounds the scan (it runs on every Bash call) when a session starts in a huge folder such as $HOME
# Fixture folders hold sample factory projects (this plugin's own evals), not the user's project.
SKIP = {"node_modules", "vendor", "build", "dist", "target", "Pods", "venv", "__pycache__", "fixtures", "testdata"}


def factory_roots(cwd):
    """Factory projects for a session started in cwd: the nearest one at or above cwd, else those below it."""
    cwd = Path(cwd)
    for folder in [cwd, *cwd.parents]:
        if (folder / MARKER).is_file():
            return [folder]
    found, budget = [], [MAX_DIRS]

    def walk(folder, depth):
        try:
            entries = sorted(os.scandir(folder), key=lambda e: e.name)
        except OSError:
            return
        for entry in entries:
            if budget[0] <= 0:
                return
            # Hidden folders hold worktrees and tool state, not the projects themselves.
            if entry.name.startswith(".") or entry.name in SKIP or not entry.is_dir(follow_symlinks=False):
                continue
            budget[0] -= 1
            path = Path(entry.path)
            if (path / ".git").is_file():
                continue  # a git worktree: a copy of a project, not another project
            if (path / MARKER).is_file():
                found.append(path)
            elif depth < MAX_DEPTH:
                walk(path, depth + 1)

    walk(cwd, 1)
    return found
