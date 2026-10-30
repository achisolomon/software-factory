#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
mkdir -p docs/reviews
cat > docs/reviews/T-22-security.md <<'EOF'
# Security review: T-22 coupon list screen
Verdict: changes requested

| # | Severity | Finding | Where |
|---|---|---|---|
| S1 | Blocker | SQL injection: the coupon search term is concatenated into the query | app/api/coupons/route.ts:27 |
| S2 | Minor | Missing Cache-Control header on the list response | app/api/coupons/route.ts:41 |
EOF
