# Changelog

Release notes for the Software Factory plugin. Back to the [README](README.md).

## 0.5.0

- **Say "team lead".** Typing "team lead, <request>" (or "team leader") hands the session to the Team Lead. No slash command needed.
- **Code-enforced gates (Claude Code).** Hooks ask before pushes, merges, deploys, infrastructure changes, publishes and recursive force deletes, refuse shell-written file edits from subagents, check that every subagent reply has the required fields, and remind the Team Lead to resume after compaction. See [docs/TRUST.md](docs/TRUST.md) for what is enforced and what is still a prompt.
- **Briefs with claims.** Every delegation says what "done" means (named claims, each with the check that decides it) and what the sender is least sure of. Replies answer each claim.
- **Skeptic pass.** A Blocker or Major finding gets one read-only agent whose only job is to refute it with evidence. Nothing is dropped silently.
- **Review routing.** `scripts/review-route` reads the diff (paths, added lines and removed lines) and says which reviewers are required and whether the review is standard or deep. It can add reviewers, never drop one.
- **One runner per worktree, mutation checks, zero errors in logs.** Only one agent runs tests or builds in a shared worktree. Critical tests are proven by a one-line mutation in a disposable worktree. Logs must be clean, and noisy logs are fixed, not muted.
- **Long jobs, local tracking, restart safety.** Agents hand back `in-progress` with a job to check. `Tracking: local` keeps work out of GitHub. A `## In flight` table plus the `resume` skill and a compaction hook make restarts safe.
- **Session settings.** `session-setup` writes auto-compact and exact-command permissions to the project's `.claude/settings.json`, after you approve the diff.
- **Links, not numbers.** Every issue, PR, commit, CI run or work item (GitHub, Jira, any tracker) the factory mentions is a clickable link, so you never have to look one up (contract rule 9.14).
- **Team table.** Every status while work is running starts with one table: what is running, what finished since the last status, and the next steps to do (status, agent ID, model, worktree, issue link, task, last update) and a separate table of background processes. Inherited models and coordinators that run no model are labelled as such.
- **GitHub Actions budget.** FinOps forecasts CI minutes and storage, reads actual Actions usage (read-only), flags waste in workflows, and reviews every CI workflow change.
- **Retro asset and plan drift batching.** Each epic ends with a retro that must name the asset it produced. Plan-text fixes are batched into one Architect pass.
- Where ideas came from: [docs/provenance.md](docs/provenance.md). Backlog: [docs/improvement-backlog.md](docs/improvement-backlog.md).
