#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# Every task of epic 2 is Done; T-30 belongs to epic 3 and stays open.
perl -pi -e 's/\| (In progress|In review|To do) \|$/| Done |/ unless /^\| T-30 /' docs/architecture/tasks.md
git -c user.name=eval -c user.email=eval@example.com commit -qam "tasks: epic 2 done"
