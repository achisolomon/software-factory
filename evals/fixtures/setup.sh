#!/bin/sh
# Scaffold for every eval case: copy the fixture project into the run's workspace (the current folder)
# and make it a git repo with one commit, so git status, worktrees and diffs behave like a real project.
# Usage from a case's scaffold.sh: . "$(dirname "$0")/../fixtures/setup.sh"
set -e
FIXTURES="${FIXTURES:-$(cd "$(dirname "$0")/../fixtures" && pwd)}"
cp -R "$FIXTURES/project/." .
# Dates are the day of the run, so in-flight work is not overdue (health-check ages them back on purpose).
TODAY="$(date -u +%Y-%m-%d)"
perl -pi -e "s/2026-10-30/$TODAY/g" docs/factory/status.md
git init -q -b main
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "fixture"
git remote add origin https://github.com/acme/shop.git
