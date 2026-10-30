#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
mkdir -p docs/reports
cat > docs/reports/T-26-verify.md <<'EOF'
# Verify: T-26 login token expiry (Must)
Status: done
Suite run by the Test Engineer: npm test (exit 0, 48 passed)

| Claim | Result | Check |
|---|---|---|
| C1 an expired token is rejected with 401 | passed | auth.test.ts "rejects expired token" |
| C2 a valid token passes | passed | auth.test.ts "accepts valid token" |

Logs: no errors.
EOF
