# Shop — Factory Status
Updated: 2026-10-30 09:50    Phase: Build    Next gate: Gate 3 — Release
GitHub Project: [Shop board](https://github.com/users/acme-owner/projects/3)

## Gates
| Gate | Status | Date | Notes |
|---|---|---|---|
| Gate 1 — PRD | approved | 2026-10-20 | |
| Gate 2 — Design | approved | 2026-10-22 | |
| Gate 3 — Release | pending | | |

## In flight
| Task | Issue | Agent | Agent ID | Model | Worktree | Dispatched (UTC) | Expect back | Job |
|---|---|---|---|---|---|---|---|---|
| Wave 3 (T-21, T-22, T-23) | [#21](https://github.com/acme/shop/issues/21), [#22](https://github.com/acme/shop/issues/22), [#23](https://github.com/acme/shop/issues/23) | Workflow `wave-3` | `wf_demo-001` | none (coordinator) | lanes below | 2026-10-30 09:10 | 23:50 | run folder `.factory-run/wf_demo-001/` |
| T-24 checkout copy | [#24](https://github.com/acme/shop/issues/24) | Developer | `a5c0ffee24d0c0de1` | sonnet | `lane-copy` | 2026-10-30 09:30 | 23:40 | |

## Background processes
| Process | Command or ports | Worktree | Started (UTC) | Shell id |
|---|---|---|---|---|
| dev stack | `npm run dev`, ports 3000 and 8080 | `lane-coupons` | 2026-10-30 09:12 | `bg7k2` |

## Open questions for the user
| # | Question | Raised by | Blocking |
|---|---|---|---|

## Approvals log
| Date | Action approved by the user | Scope |
|---|---|---|
| 2026-10-22 | Gate 2 design | design v2 |

## Log
- 2026-10-30 09:10 — Wave 3 started as Workflow `wf_demo-001` (lanes coupons, coupons-ui, analytics).
- 2026-10-30 09:30 — T-24 dispatched to Developer `a5c0ffee24d0c0de1`.
- 2026-10-30 09:45 — Last status sent to the user.
