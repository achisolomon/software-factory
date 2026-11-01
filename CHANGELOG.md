# Release notes

What changed in each release of the Software Factory plugin, newest first. Back to the [README](README.md). To update, see [Updating](README.md#updating).

## 0.7.0 (2026-11-01)

- **Claude Code only.** Codex support was never tested end to end, so it is removed: the Codex plugin and marketplace manifests, the portable `plugin.json`, the Codex installers and role runner, the Codex model routing, the `factory-protocol` role playbook, their tests, and every "in Codex" line in the agents, skills, contract and docs. Agent instruction files under `.codex/` in a project diff still route to Security.
- **Open source.** AGPL-3.0 license, `CONTRIBUTING.md`, starter issues, and a new README (hero image, demo video, bring-your-own-spec, three-step setup).
- **Bring your own spec.** A spec from Superpowers, BMAD, OpenSpec, Spec Kit or similar is the PRD; the Product Manager reviews it for gaps and never rewrites it.

## 0.6.4 (2026-11-01)

- **Links before approval.** At Gate 1 the Team Lead makes sure the Product Manager names each file it wrote, sends it back if not, and links the vision, PRD, backlog and flows before asking you to approve. At every gate, each document you are asked to approve is linked, and the links are repeated in the question itself. New eval `gate-1-links-first`.

## 0.6.3 (2026-11-01)

- **One-line terminal install.** The README installs with one `claude plugin` line in a terminal, with first-run checks and fixes for common install errors. The `/plugin` chat command is not available in the VS Code extension.
- The Team Lead gives the terminal update command (not `/plugin marketplace update`) when it tells you how a plugin change reaches a project.
- Release notes moved from the README to this page.

## 0.6.2 (2026-10-31)

- **Pace: speed.** Say "I want speed" (or set the speed preference) and the Team Lead runs a lighter loop: the skeptic pass only for Security findings and for auth, payments or data deletion; only the required reviewers plus Test and Architect; the Architect's fast check in parallel with tests; independent tasks in parallel, up to three Developers. Gates, approvals, Security and a deep review route are unchanged.
- **Long jobs go to the background.** Any wait over about three minutes runs in the background and hands back `in-progress`. No sleep or polling loops.
- **Status table by default.** A status every 15 minutes is on by default; `Status cadence: off` turns it off. New `/software-factory:status` command shows the team table on demand.
- **Opus again for the Team Lead and Architect.** The model hook blocks Fable in a factory project unless the prompt says `Fable requested by user: ...`.

## 0.6.1 (2026-10-31)

- **Load ceiling with any shared load target.** When the Team Lead asks to run load against a shared environment such as staging, it asks for the environment and the load ceiling together, in both Claude Code and Codex.
- **Explore lookups run on Haiku.** The model hook blocks an Explore dispatch that is not on Haiku in a factory project, unless the prompt says `Why not haiku: <reason>`.
- Eval fixes: fixtures use the run's date, and the triage eval accepts inline triage.

## 0.6.0 (2026-10-31)

- **Performance Engineer (new agent, Opus).** Finds what breaks under load (missing indexes, N+1 queries, locks, pool limits, unbounded work), sizes the system against the NFRs, plans and runs load tests, and reports each bottleneck with its cause and fix. Runs at release readiness and on request, never per task, and never against production.
- **Test Engineer as devil's advocate.** Hunts for where the code breaks. Test-first is the preferred practice (test-after is a Nit, a missing test is a finding). Anything not testable by automation is a Major for the Architect and Developer. The Definition of Done gains an API-first item.
- Team Lead and Architect tried Fable first with an Opus fallback (reverted in 0.6.2).

## 0.5.9 (2026-10-30)

- The team table survives compaction, and Workflow agents are read from the run folder.
- Hooks find the factory project inside a multi-repo workspace folder. Session start flags a missing auto-compact threshold (default 30).
- `evals/`: 20 behavior cases plus offline suite checks.

## 0.5.8 (2026-10-29)

- `health` skill: a read-only health check of a factory project.
- Changes to agent instruction files are routed to Security review.
- Prompt drift test, and the GitHub Project works as the dashboard.

## 0.5.7 (2026-10-29)

- Machine-wide local CI lock template, so parallel worktrees don't run CI over each other.

## 0.5.6 (2026-10-28)

- The team table keeps the IDs of finished agents. The Issue column is always a link or none.

## 0.5.5 (2026-10-27)

- One-line update command for the VS Code terminal, or ask Claude to update the factory.

## 0.5.4 (2026-10-27)

- One team table with running, blocked, done and to do rows.

## 0.5.3 (2026-10-27)

- Session start shows the running version and offers an update when a newer one is published.

## 0.5.2 (2026-10-27)

- The team table and In flight table show each agent's own ID and the task's issue link.

## 0.5.1 (2026-10-27)

- Version bump so installed 0.5.0 copies update.

## 0.5.0 (2026-10-27)

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

## 0.4.0 (2026-10-21)

- Codex support: the factory runs as a Codex plugin, published to a Codex marketplace.
- Economical QA: the Test Engineer uses the bundled `frontend-testing` skill for web UI work, with no extra QA agent.

## 0.3.0 (2026-10-19)

- Triage, a factory brain per repo, by-reference handoffs, model routing and bounded fix loops.

## 0.2.0 (2026-10-16)

- First published version.
