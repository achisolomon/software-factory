#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
git checkout -q -b lane-copy
mkdir -p app/checkout
cat > app/checkout/copy.ts <<'EOF'
export const checkoutCopy = {
  title: "Review your order",
  payButton: "Pay now",
  couponHint: "Have a coupon? Enter it below.",
};
EOF
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "T-24: checkout copy"
git checkout -q main
