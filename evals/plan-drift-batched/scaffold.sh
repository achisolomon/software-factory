#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
mkdir -p docs/reviews
cat > docs/reviews/T-22-architect.md <<'EOF'
# Architect review: T-22 coupon list screen
Verdict: pass (checks re-run: npm test, npm run lint)

Findings: none blocking.

Plan-text corrections (no code change):
- tasks.md T-30 says "export to XLSX"; ADR-07 settled on CSV.
- tasks.md links "ADR-05 caching"; the file is now ADR-05-http-caching.md.
EOF
