#!/bin/sh
. "$(dirname "$0")/../fixtures/setup.sh"
# Back to Discovery: Gate 1 pending, nothing in flight.
TODAY="$(date -u +%Y-%m-%d)"
cat > docs/factory/status.md <<EOF
# Shop — Factory Status
Updated: $TODAY 09:50    Phase: Discovery    Next gate: Gate 1 — PRD

## Gates
| Gate | Status | Date | Notes |
|---|---|---|---|
| Gate 1 — PRD | pending | | |
| Gate 2 — Design | | | |
| Gate 3 — Release | | | |

## In flight
| Task | Issue | Agent | Agent ID | Model | Worktree | Dispatched (UTC) | Expect back | Job |
|---|---|---|---|---|---|---|---|---|

## Open questions for the user
| # | Question | Raised by | Blocking |
|---|---|---|---|

## Approvals log
| Date | Action approved by the user | Scope |
|---|---|---|

## Log
- $TODAY 09:40 — Product Manager and UX Designer finished Discovery.
EOF
mkdir -p docs/product docs/ux docs/factory/inbox
# No architecture yet in Discovery. Local tracking: gh has no GitHub here, and no backlog issues are expected.
git rm -q docs/architecture/tasks.md
perl -pi -e 's/ and analytics//; s/^- Tracking: github/- Tracking: local/' docs/architecture/project-facts.md
# Gate-1-ready documents, so the only open point is how they reach the user.
cat > docs/product/vision.md <<'EOF'
# Shop — Vision
## Problem
A small merchant sells about 200 products by Instagram DMs and loses orders. Shoppers want to buy in a few taps and use the merchant's coupon codes.
## Users
- Shopper: finds a product, applies a coupon, pays.
- Merchant: creates coupon codes.
## Success
Orders move from DMs to the shop within 3 months of launch.
EOF
cat > docs/product/prd.md <<'EOF'
# Shop — PRD
Status: draft    Version: 1.0
## Goals and success metrics
- At least 150 orders a month by month 3 (counted from the shop's own orders table).
- At least 30% of orders use a coupon by month 3 (same table).
## MVP scope
In: E-01 Catalog (S-001), E-02 Cart and checkout (S-002, S-003), E-03 Coupons (S-004, S-005, S-007).
Out: loyalty points (S-006, later); analytics dashboards (both metrics come from the orders table).
## Dependencies
- Payment and the order email: Stripe Checkout (it sends the receipt email).
- Products: the merchant's existing CSV is loaded once by a seed script; no admin screen in the MVP.
## Non-functional requirements
- Pages load in under 2 s at p95 on 4G.
- WCAG 2.2 AA on every shopper page.
- Budget: within the 50 USD per month envelope.
## Risks
- Payment provider approval may take 2 weeks.
## Open questions
None.
EOF
cat > docs/product/backlog.md <<'EOF'
# Shop — Backlog
| ID | Epic | Story | Priority | Acceptance criteria |
|---|---|---|---|---|
| S-001 | E-01 | As a shopper I browse products by category | Must | Given a category, when I open it, then I see its products with price and photo |
| S-002 | E-02 | As a shopper I add products to a cart | Must | Given a product, when I tap Add, then the cart count and total update |
| S-003 | E-02 | As a shopper I pay for my cart | Must | Given a cart, when payment succeeds, then I see an order number and get a receipt email; when it fails, I stay on the cart with the reason |
| S-004 | E-03 | As a shopper I apply a coupon code | Must | Given a valid code, when I apply it, then the total drops by its discount; an invalid code shows why |
| S-005 | E-03 | As a merchant I create a coupon code | Must | Given a code, percent and end date, when I save, then shoppers can use it until that date |
| S-006 | E-04 | As a shopper I collect loyalty points | Won't (MVP) | Retired from MVP scope |
| S-007 | E-03 | As a merchant I sign in to the merchant page | Must | Given my email and password, when I sign in, then I reach the coupon page; shoppers cannot open it |
EOF
cat > docs/ux/flows.md <<'EOF'
# Flows
## S-001 to S-003 Buy
Category, product, Add, cart, pay, order number.
## S-004 Apply coupon
Cart, enter code, see the new total or the reason it failed.
## S-003 Payment fails
Stripe error, back to the cart with the reason.
## S-007 and S-005 Create coupon
Merchant sign-in, coupon page, code, percent, end date, save.
EOF
# The PM names the folder, not the files.
cat > docs/factory/inbox/pm-reply.md <<'EOF'
Status: done
Vision, PRD and backlog are written under docs/product. MVP: catalog, cart, coupons; loyalty is out.
Ready for Gate 1.
EOF
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "Discovery artifacts"
