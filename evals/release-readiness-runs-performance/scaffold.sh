#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
cat >> docs/factory/status.md <<'EOF'
- 2026-10-30 11:40 — Wave 3 and T-24 merged to main after review. Staging: https://staging.shop.example.com (shared with the design team). Production: https://shop.example.com.
EOF
git -c user.name=eval -c user.email=eval@example.com commit -qam "status: wave 3 merged"
