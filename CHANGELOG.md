# Release notes

What changed in each release of the Software Factory plugin, newest first. Back to the [README](README.md). To update, see [Updating](README.md#updating).

## 0.8.4 (2026-11-14)

- **Repeat commands stop asking for approval every time.** A week of traces showed about 3,000 sandbox-off Bash calls, most of them build-and-test runs sent as inline chains (`eval "$(...)"; ...; for s in ...; do ...; done`) or as scripts in a scratch folder. Neither can match an allow rule, and a scratch path changes every session, so the user approved the same run again and again. Contract rule 9.15 now says: a command you run more than once becomes a script in the project's `scripts/` folder, committed with the task and run as one plain command by absolute path. The agent hands the Team Lead `allowlist: Bash(<absolute path> *)`; the Team Lead asks the user once and adds it to the project settings (`session-setup` step 2).
- **Subagents may write to Claude Code's own session scratchpad.** The project-bounds hook blocked `/private/tmp/claude-<uid>/<project>/<session>/scratchpad`, which Claude Code itself tells subagents to use (96+ wasted turns in a week). Loose files elsewhere in the temp folder are still blocked.
- **Shell form, in three lines.** Rule 9.15 now spells out one command per call, literal absolute paths in directory flags (never `git -C "$W"`), and scripts for tools without a directory flag. These blocks cost about 700 turns in a week.
- **Sandbox off only after a sandbox error.** Agents run every command in the sandbox first and never turn it off up front, never for `gh` or `git push`.
- **No more calls to tools that are not there.** Agents check their tool list and search with `grep`/`rg` through Bash when Grep or Glob is missing; no subagent role has Monitor.
- **Background processes are stopped by ID.** Agents record the shell ID or PID of every server or emulator they start and stop it with TaskStop or `kill <pid>`, never `pkill -f`, which the auto-mode classifier denies.
- **Smaller tasks.** Developer tasks averaged about 225 tool calls against a target of 80. The Architect now splits any task over about 5 production files, 2 acceptance criteria, or one that spans UI and backend; the Team Lead sends the rest of a story back for splitting when a Developer dispatch passes about 120 calls.
- **Flaky tests are quarantined at once.** A test that passes on an unchanged rerun is quarantined with an issue in the same turn, with no debugging rounds, and the user is told which test and what it failed on.
- **Mock parity.** In Review mode the UX Designer screenshots the local build and compares it with the mock the user approved; a visible difference is at least Major.
- **Pushing a task branch no longer asks.** The gate hook flags a push only when it goes to a shared branch (`main`, `master`, `dev`, `develop`, `staging`, `prod`, `production`, `gh-pages`, `release/*`), or when it is a bare or `HEAD` push, a plain force push, a delete, or a push of tags, `--all` or `--mirror`. `git push -u origin feature/x` and `--force-with-lease` to a task branch pass. Merges stay gated. The hook still never answers "allow", so your own permission settings decide whether you are prompted.
- **Repeat bugs get a regression test.** When the user says a bug came back, the Developer finds why the earlier fix did not hold and adds a test that fails without the fix.

## 0.8.3 (2026-11-11)

- **New repo name: `achisolomon/open-software-factory`.** The install line, links, homepage and the version check now use the new name. GitHub redirects the old URL, so existing installs keep working. The plugin and marketplace names (`software-factory@software-factory-marketplace`) are unchanged.

## 0.8.2 (2026-11-08)

- **Fewer wasted turns in subagents.** Contract rule 9.15 lists the tool failures that repeated most in real traces (missing Grep and Monitor tools, bad `--jq` quoting, missing labels) with the working form for each, and points to 9.12 for shell file writes and scratch.
- **No chained commands.** Rule 9.15 now tells agents to run each command on its own (no `cd X && cmd` or `cd X; cmd`) and to use absolute paths and directory flags (`git -C`, `npm --prefix`, `terraform -chdir`, `gh -R`), because permission hooks can block chains. A tool with no directory flag gets absolute paths or a short script under `$FACTORY_TMP`.
- **Cloud reads stay at project scope.** Rule 9.15 also tells agents that org- or billing-level reads (billing budgets, org IAM, org policies) are usually denied; a denied read is reported as a gap, not retried or routed around.
- **Subagents end the run on the reply block.** With a handback tool (for example `SubagentHandback`) the whole block goes in that call; otherwise it is the final text message. A run that ended on any other tool call was recorded as a failed subagent.

## 0.8.1 (2026-11-07)

Faster runs, fewer tokens, and you choose who is on the team. Measured on two real runs of 41 and 48 hours: the Developer averaged 65 minutes and 249 tool calls per task, Security reviewed almost every task, four foreground CI watches held Developers for 9 hours, and the Team Lead's context sat at a median of 187K tokens per turn.

- **Choose who is on the team.** A new `- Team:` line in `project-facts.md` sets Security, UX, FinOps and DevOps each to `per-task`, `per-epic` or `off`. Init asks once; say "skip UX for this epic" any time. With no line, Security runs per epic and the rest per task.
- **Security per epic by default, per task only on hard triggers.** `review-route` now splits security triggers in two. Hard (auth code, security rules files, secrets, new or changed dependencies, payments, migrations, agent instruction files, a deleted guard, a deep route) always run Security on the task, whatever the roster says. Soft (the words auth, token or session in new code, HTTP calls, models and storage folders) follow the roster, by default one Security review of the whole epic's diff at epic end. Tests, docs and generated code-graph output (`graphify-out/`) no longer trigger Security or UX. Reviewers the route marks `epic-end` are queued in `status.md` and run once when the epic's last task is done.
- **No more waiting in the foreground.** A new hook, `hooks/no_wait.py`, refuses `gh pr checks --watch`, `gh run watch`, polling loops with `sleep` and sleeps over 30 seconds in factory subagents. The agent returns `in-progress` with the CI run in `Job:` instead. The Team Lead watches CI with one background command rather than polling.
- **Smaller tasks, fewer fix rounds.** The Architect sizes tasks at about 80 Developer tool calls and splits bigger ones. A Developer past about 120 calls stops and proposes a split. Before handing back, it checks its diff against the new `reference/review-checklist.md` and the brain's recurring findings. A fix round must change what the reviewer objected to.
- **A lighter Team Lead.** Init, Discovery, Architecture, design reviews, Release readiness, Deploy, the infrastructure gate, the templates and lesson promotion moved to `reference/team-lead-phases.md`, read only at that step: `agents/team-lead.md` went from 54 KB to 42 KB, though this release also adds rules to it. The Team Lead batches its `status.md` edits per wave, sends long command output to a file, and leaves issue work to the Project Manager.
- **Cheaper reading.** Every agent reads code with Read, Grep and Glob instead of `cat`, `sed -n` and `grep` in Bash. When a project has a code graph (`graphify-out/graph.json`), agents ask it first and read only the lines it points to.
- **Per-agent effort.** The Developer, Test Automation Engineer, UX/UI Designer and FinOps Engineer run at `effort: medium`. The Architect, Security and the Team Lead keep their default effort.
- **Upgrade note.** Projects without a `- Team:` line now get Security per epic instead of on most tasks. Add `- Team: security=per-task` under Preferences in `project-facts.md` to keep the old behavior.

## 0.8.0 (2026-11-03)

- **New agent: the Exploratory QA Engineer.** A black-box bug hunter that uses the running app like a user, at the end of an epic and whenever you ask. It works only in local or disposable environments, never shared or production ones. Before it reads any code it writes a failing repro test for each bug, and it marks that test with a quarantine marker so the suite stays green until the bug is fixed. Method adapted, in our own words, from tester-army/e2e (see [provenance](docs/provenance.md)); the tool is neither bundled nor pinned.
- **Team Lead and Test Engineer wiring.** The Team Lead calls the explorer at epic end and on request. The Test Automation Engineer owns the repro tests from un-quarantine on and allows the explorer to quarantine its own.
- **The gate hook asks before more risky commands.** It now asks first for remote database clients, docker volume removal, firebase deletes and `gh` writes to other repositories.
- **Four new evals** cover the explorer's rules, for 29 in total. The README now also carries the real agent, eval and test counts, and `tests/test_release_files.py` keeps them honest.
- **Upgrade note.** Add `.software-factory-withheld/` to your project's `.gitignore`. Without it, the explorer stops with `needs-input` when it finds a security issue in a public repository, because it will not write the details where they could be committed.

## 0.7.6 (2026-11-03)

- **A Project Manager keeps GitHub current, and the Product Manager files its own story issues.** Before, the Product Manager had no shell, so it could only draft story issues and the Team Lead had to file them by hand. Now the Product Manager opens and updates one issue per story (`S-NNN`) as it writes the backlog. A new Project Manager agent (Haiku) sets up the board, opens any missing story, task or finding issue, and moves each issue's status and posts its comments as the Team Lead reports events. It also audits the board against the files before each gate, at each epic end and on resume. The gate hook lets both agents run only `gh` from the shell.
- **Choose how they reach GitHub: `gh` or the GitHub MCP server.** Init now asks (`GitHub access` in `project-facts.md`), with pros and cons. `gh` is recommended: it uses your existing login, and every agent can file its own findings. With `mcp`, the Product Manager and Project Manager use the GitHub MCP tools and no shell. You add the server once with a personal access token, the board is created once in the GitHub web UI, and the Project Manager files the other agents' findings at its next audit.

## 0.7.5 (2026-11-02)

- **No folders in your project unless an agent needs scratch space.** 0.7.3 and 0.7.4 created `.software-factory-tmp/` (with a `.gitignore`) in every project at every session start. Now the session start only sets `$FACTORY_TMP`; the folder appears only when an agent creates it for scratch work, and is deleted when the session ends. Git ignores it through one line in `.git/info/exclude` (never shown or committed), not a file in your project. The first session after updating also removes the empty `.software-factory-tmp/` that 0.7.3 and 0.7.4 left behind.

## 0.7.4 (2026-11-02)

- **Factory agents can no longer leave files outside the project.** A new hook, `hooks/project_bounds.py`, refuses a factory subagent's Write, Edit or NotebookEdit outside the project folder and points it at `$FACTORY_TMP`. The reply check (`hooks/check_reply.py`) now also sends a subagent back when new files or folders appeared beside the project while it ran (for example from a script), and lists them so it deletes them before it finishes. `tests/test_scratch_leaks.py` replays both leaks seen on 2026-11-02.

## 0.7.3 (2026-11-02)

- **Scratch files stay inside the project and are cleaned up.** Agents had left dozens of test copies and fake home folders next to the project, outside it, and never deleted them. Each session now gets its own git-ignored scratch folder, `<project>/.software-factory-tmp/<session id>/` (`$FACTORY_TMP` in Bash). A new hook, `hooks/scratch.py`, creates it when the session starts and deletes it when the session ends. At each start it also deletes `.software-factory-tmp/` folders left by crashed sessions (untouched for 24 hours). Contract rule 9.12 and the Developer, Test and Performance agents now require every scratch file to go there, and to be removed before the agent replies.

## 0.7.2 (2026-11-02)

- **Plugin icon and links.** A square plugin icon, and `homepage` and `repository` in `plugin.json`, ready for the claude.ai plugin directory.

## 0.7.1 (2026-11-02)

- **New setup option: Expensive + max models (not recommended).** `Model policy: max` runs the Team Lead and the Architect's design and reviews on Fable, and every Sonnet row on Opus. Very expensive: it can burn through your Claude limits very fast. The Team Lead confirms the choice once, shows it at the top of each status, and drops to Opus if you hit a usage limit. Say "use default models" to leave it.

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
