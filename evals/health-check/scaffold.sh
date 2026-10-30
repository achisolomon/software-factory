#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
echo ".worktrees/" >> .git/info/exclude
# A worktree with uncommitted work.
git worktree add -q .worktrees/lane-copy -b lane-copy
echo "draft copy" > .worktrees/lane-copy/checkout-copy.md
# A worktree whose folder is gone: git lists it as prunable.
git worktree add -q .worktrees/lane-coupons -b lane-coupons
rm -r .worktrees/lane-coupons
# The fixture's In flight rows were dispatched 2026-10-30 09:10-09:30 UTC with Expect back 10:15-10:30, so they are
# overdue now, and nothing listens on the dev stack ports 3000 and 8080.
