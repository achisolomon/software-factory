#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
perl -pi -e 's/^- Tracking: github/- Tracking: local/; s/^- GitHub Project:.*\n//' docs/architecture/project-facts.md
perl -pi -e 's/\[#(\d+)\]\(https:\/\/github\.com\/acme\/shop\/issues\/\d+\)/T-$1 (local)/g; s/^GitHub Project:.*/GitHub Project: none, Tracking: local (docs\/architecture\/tasks.md)/' docs/factory/status.md docs/architecture/tasks.md
perl -pi -e 's/"issue":"https:\/\/github\.com\/acme\/shop\/issues\/(\d+)"/"issue":"T-$1 (local)"/g' .factory-run/wf_demo-001/journal.jsonl
