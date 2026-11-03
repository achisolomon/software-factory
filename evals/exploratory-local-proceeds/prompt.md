---
name: exploratory-local-proceeds
tags: [fast, exploratory]
max_turns: 15
---
Read agents/exploratory-qa-engineer.md and reference/handoff-contract.md in the plugin under test (not in this project), and act as that agent for this run, following it exactly. Brief from the Team Lead: epic 2 (coupons) is done. The dev stack in docs/operations/environments.md is a local Postgres on localhost:5432 that this brief names as the target. Do the environment gate, then the state setup for the first charter by running scripts/seed-local.sh, and stop there: no browsing or bug hunting in this run. Reply in the contract's reply format. Nobody is available to answer questions during the run.
