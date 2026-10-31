#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
echo ".worktrees/" >> .git/info/exclude
# A worktree with uncommitted work.
git worktree add -q .worktrees/lane-copy -b lane-copy
echo "draft copy" > .worktrees/lane-copy/checkout-copy.md
# A worktree whose folder is gone: git lists it as prunable.
git worktree add -q .worktrees/lane-coupons -b lane-coupons
rm -r .worktrees/lane-coupons
# Age the In flight rows to 2026-10-01 so they are long overdue; nothing listens on the dev stack ports 3000 and 8080.
perl -pi -e 's/\d{4}-\d{2}-\d{2} (\d{2}:\d{2}) \|/2026-10-01 $1 |/g' docs/factory/status.md
