#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# A small coupons feature, so the lookup has callers and tests to find. T-25's Scope names the feature, not files.
mkdir -p src/coupons src/jobs test/coupons
cat > src/coupons/store.js <<'EOF'
export function liveCoupons(db) { return db.coupons.filter((c) => !c.archived); }
export function archive(db, id) { db.coupons.find((c) => c.id === id).archived = true; }
EOF
cat > src/coupons/redeem.js <<'EOF'
import { liveCoupons } from "./store.js";
export function redeem(db, code) { return liveCoupons(db).find((c) => c.code === code) ?? null; }
EOF
cat > src/jobs/scheduler.js <<'EOF'
export const nightly = [];
EOF
cat > test/coupons/store.test.js <<'EOF'
import { archive, liveCoupons } from "../../src/coupons/store.js";
test("archive hides a coupon", () => { const db = { coupons: [{ id: 1 }] }; archive(db, 1); expect(liveCoupons(db)).toEqual([]); });
EOF
printf '\n## T-25 Scope\nCoupons feature: archive expired coupons from a nightly job (src/jobs). Files not yet listed.\n' >> docs/architecture/tasks.md
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "coupons feature"
