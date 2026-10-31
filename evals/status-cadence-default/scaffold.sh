#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# No preference set: the default applies.
perl -ni -e 'print unless /^- Status cadence:/' docs/architecture/project-facts.md
git -c user.name=eval -c user.email=eval@example.com commit -qam "no status cadence preference"
