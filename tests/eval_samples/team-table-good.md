Software Factory v0.5.9

**Agents** (`10:05`)

| Status | Agent | Agent ID | Model | Worktree | Issue | Task | Since / last update |
|---|---|---|---|---|---|---|---|
| running | Workflow `wave-3` | `wf_demo-001` | none (coordinator; runs the 3 agents below) | lanes below | [#21](https://github.com/acme/shop/issues/21), [#22](https://github.com/acme/shop/issues/22), [#23](https://github.com/acme/shop/issues/23) | wave 3 | `~09:10` |
| running | Developer, coupons | `a21c0up0n5dev0001` | sonnet | `lane-coupons` | [#21](https://github.com/acme/shop/issues/21) | T-21 coupon redeem | `~09:10` |
| running | Developer, analytics | `a23ana1yt1c50003` | haiku | `lane-analytics` | [#23](https://github.com/acme/shop/issues/23) | T-23 daily analytics | `~09:10` |
| running | Security, coupons-ui | `a22rev1ew5ec0004` | sonnet | `lane-coupons-ui` | [#22](https://github.com/acme/shop/issues/22) | T-22 review | `~09:50` |
| running | Developer | `a5c0ffee24d0c0de1` | sonnet | `lane-copy` | [#24](https://github.com/acme/shop/issues/24) | T-24 checkout copy | `~09:30` |
| done | Developer, coupons-ui | `a22c0up0n5u10002` | sonnet | `lane-coupons-ui` | [#22](https://github.com/acme/shop/issues/22) | T-22 built, tests pass | `09:48` |
| to do | Team Lead | n/a | n/a | main | none | merge the lanes once all finish | after the lanes |

**Background processes**

| Process | Command or ports | Worktree | Since |
|---|---|---|---|
| dev stack | `npm run dev`, ports 3000 and 8080 | `lane-coupons` | `~09:12` |
