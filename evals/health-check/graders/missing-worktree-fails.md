---
# The worktree whose folder is gone (prunable) is a fail row: its uncommitted work is lost.
type: regex
flags: i
pattern: '(lane-coupons[^\n]*\bfail\b|\bfail\b[^\n]*lane-coupons)'
match: contains
---
