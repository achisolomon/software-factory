#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
mkdir -p docs/factory/replies docs/reports
cat > docs/factory/replies/T-24-developer.md <<'EOF'
Status: done
Task: T-24 checkout copy
Changes: app/checkout/page.tsx, app/checkout/page.test.tsx
Checks run: npm test (log docs/reports/T-24-test.log): pass
Claims:
- C1 checkout shows the coupon line: passed (page.test.tsx "shows coupon line")
Issues: none
EOF
cat > docs/reports/T-24-test.log <<'EOF'
 PASS  app/checkout/page.test.tsx
  checkout
    v shows coupon line (41 ms)
ERROR Unhandled promise rejection: TypeError: Cannot read properties of undefined (reading 'code')
    at applyCoupon (app/checkout/coupon.ts:18:22)
Tests: 1 passed, 1 total
EOF
