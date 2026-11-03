#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# Every task of epic 2 is Done; T-30 belongs to epic 3 and stays open.
perl -pi -e 's/\| (In progress|In review|To do) \|$/| Done |/ unless /^\| T-30 /' docs/architecture/tasks.md
# Nothing of epic 2 is in flight any more, so the board does not tell the Team Lead to wait.
perl -ni -e 'print unless /^\| (Wave 3|T-24 checkout copy) /' docs/factory/status.md
echo "- $(date -u +%Y-%m-%d) 12:00 Epic 2 (coupons): T-21 to T-26 merged and Done, no task in flight." >> docs/factory/status.md
git -c user.name=eval -c user.email=eval@example.com commit -qam "tasks: epic 2 done"
