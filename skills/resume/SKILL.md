---
name: resume
description: Resume the Software Factory Team Lead after a context compaction or a session restart. Reconciles every in-flight dispatch against the reports on disk before any new work is sent.
disable-model-invocation: true
---

# Resume after compaction or restart

Act as the Team Lead. Read, in full, before anything else:
- In Claude Code: `${CLAUDE_PLUGIN_ROOT}/agents/team-lead.md` and `${CLAUDE_PLUGIN_ROOT}/reference/handoff-contract.md`.
- In Codex: `../factory-protocol/references/role-playbook.md`, resolved relative to this skill's `SKILL.md`.

Then follow "Resume after compaction or restart" in the Team Lead instructions:
1. Read `docs/factory/status.md` (phase, gates, approvals, `## In flight`), `docs/factory/brain.md` and `docs/architecture/project-facts.md`. If `status.md` is missing, the project is not initialized: say so and stop.
2. Classify every `## In flight` row and reconcile all of them before any new dispatch:
   - `completed-and-reported`: reply processed. Verify it still holds.
   - `completed-unreported`: report on disk at the named revision, reply never processed. Verify the report and its evidence, accept once, never dispatch again.
   - `sent-unverified`: dispatched, no report. Inspect once (branch log; SendMessage the agent if its id is recorded), then hold or mark `stalled`. No automatic re-dispatch.
   - `never-sent`: row written, nothing started. Dispatch.
   - `ambiguous`: anything inconsistent. Hold and ask the user.
3. Check `git worktree list` for a leftover mutation worktree and note it. Read-only: never commit, stash, push or clean to tidy up.
4. Check that each `## Background processes` row is still running; remove the rows that are not, and restart a process only if the current task needs it.
5. If `Status cadence` is on, re-create the status cron (cron is session-scoped).
6. Tell the user the result per row, show the Team table (Team Lead instructions, "Team table"), and say what you will do next. Then continue from the Build loop or the current phase.
