#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# 0.8.1: the roster turns Security and UX off, but the diff changes auth code (a hard trigger), so Security still
# reviews this task. The UI change follows the roster, so UX does not.
perl -pi -e 's/^- Delegation rules: none$/- Delegation rules: none\n- Team: security=off, ux=off/' docs/architecture/project-facts.md
git -c user.name=eval -c user.email=eval@example.com commit -qam "facts: team roster"
git checkout -q -b lane-copy
mkdir -p app/auth app/checkout
cat > app/auth/login.ts <<'EOF'
export function isLoggedIn(cookie: string | undefined): boolean {
  return Boolean(cookie && cookie.length > 10);
}
EOF
cat > app/checkout/PayButton.tsx <<'EOF'
export function PayButton({ onPay }: { onPay: () => void }) {
  return <button onClick={onPay}>Pay now</button>;
}
EOF
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "T-24: login check and pay button"
git checkout -q main
