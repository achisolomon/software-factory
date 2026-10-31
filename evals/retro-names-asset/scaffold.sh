#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# Epic 2 is finished: every task done, nothing in flight, and review notes give the retro material.
perl -pi -e 's/\| (In progress|In review|To do) \|$/| Done |/ unless /T-30/' docs/architecture/tasks.md
perl -ni -e 'print unless /^\| (Wave 3|T-24)/' docs/factory/status.md
echo "- 2026-10-31 08:00 — Epic 2 (coupons) finished: T-21 to T-26 Done. Gate 3 next." >> docs/factory/status.md
mkdir -p docs/reviews
cat > docs/reviews/epic-2-notes.md <<'EOF'
# Epic 2 review notes (collected by the Team Lead)
- T-22 needed 3 fix rounds: its brief had no empty-state claim, so UX found it late each round.
- T-24 Developer reported done twice without running lint; the Architect caught it both times.
- T-26 auth tests passed but no mutation check was run until the Test Engineer was asked.
EOF
