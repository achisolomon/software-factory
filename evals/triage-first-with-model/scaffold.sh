#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# Nothing in flight: earlier-session work makes the Team Lead (rightly) hold new dispatches, which is not this case.
perl -ni -e 'print unless /^\| (Wave 3|T-24|dev stack) / or /^- .*(Wave 3|T-24) (started|dispatched)/' docs/factory/status.md
rm -r .factory-run
git -c user.name=eval -c user.email=eval@example.com commit -qam "wave 3 and T-24 closed"
