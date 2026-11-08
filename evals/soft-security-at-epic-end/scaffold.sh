#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# 0.8.1: a soft security trigger (an HTTP call) with no Team line waits for the epic-end Security review. The call
# loads public, static copy: no user data, auth path, rules file, secret, dependency, payment or migration.
git checkout -q -b lane-copy
mkdir -p app/content
cat > app/content/copy.ts <<'EOF'
const fallback = { title: "Review your order", couponHint: "Have a coupon? Enter it below." };

export async function loadCopy(locale: string) {
  const res = await fetch(`/static/copy/${locale === "fr" ? "fr" : "en"}.json`);
  return res.ok ? res.json() : fallback;
}
EOF
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "T-24: checkout copy loads from static JSON"
git checkout -q main
