# Behavior evals

The unit tests in `tests/` check the scripts and that the rules are written down. These evals check that the agents actually follow the rules. Each case copies a small fixture project (`fixtures/project`, a shop with a running wave), sets up one situation from a real finding, and grades the reply and the tool calls.

## Run

```sh
scripts/behavior-check --tag fast                    # every fast case, with the no-plugin baseline
scripts/behavior-check lookup-on-haiku team-table-status   # named cases, no baseline
scripts/behavior-check team-table-status -- --keep-temp --runs 3   # extra runner flags after --
```

The script wraps `claude plugin eval . --scaffold --trust-plugin --no-publish --allow-tools Bash Edit Write Grep Glob CronCreate "Read(/$PWD/**)" --runs 1 --max-cost-usd 5`, and runs named cases one call each (the runner keeps only the last `--case`). From Claude Code, run it outside the Bash sandbox (`dangerouslyDisableSandbox`); its name has no "eval" in it, so worktree guards that refuse that word let it through.

- `--scaffold` is required: without it the fixture project is never built.
- `--allow-tools` is required: a case's `allowed_tools` only takes effect for tools granted on the command line. Without it the agent has no shell and cannot write, and those cases fail for the wrong reason. Grep and Glob are needed for search subagents. `"Read(/$PWD/**)"` lets the agents read the plugin's own instruction files (run it from the plugin folder); without it the Team Lead cannot read `agents/team-lead.md` and improvises.
- Inside Claude Code's Bash sandbox, Bash in the eval sessions fails to start its own sandbox (`EPERM ... srt-mux ... sock`), and every case that needs a shell fails for the wrong reason. Run the script unsandboxed, or from a terminal.
- Each case also runs once without the plugin, as a baseline (the report's Δ column). `--ablation none` skips the baseline and halves the cost.
- `--keep-temp` keeps each run's sandbox and `trace.jsonl`, so you can read the full reply when a grader fails.
- `--tag fast` covers one-decision cases. `triage-first-with-model` is tagged `slow` because it dispatches real subagents.
- `--runs 1` is a smoke run. Before a release, use the default 3 runs: the agents are not deterministic, so one pass proves little.
- `--model` picks the model under test. The pushapp failures happened on Opus, so run on Opus before a release.
- Results go to `evals/results/<timestamp>/` (git-ignored). Exit code 0 means every case met the threshold.

The free offline checks in `tests/test_evals.py` run with the normal suite. They check that:
- every case is well formed;
- every scaffold builds its situation;
- the team-table graders accept a correct table (`tests/eval_samples/team-table-good.md`) and reject the real pushapp reply that started this suite (`tests/eval_samples/team-table-bad-pushapp.md`).

## Limits

- The runner cannot compact a session. `team-table-after-compaction` replays a compacted continuation in the prompt instead: the summary with its Lane | Tasks table, plus the after-compact hook text.
- A running Workflow cannot be mocked. The fixture puts the workflow's run folder (`.factory-run/wf_demo-001/`: `journal.jsonl` and `agent-<id>.meta.json`) on disk, and `status.md` points to it.
- `gh` has no GitHub to reach here. Board and issue activity comes from a file (`board-is-not-approval`).
- The runner's `regex`, `tool_used` and `target` fields come from its built-in reference, not from public docs. If a grader errors on the first run, check `claude plugin eval --help`.

## Coverage: findings of 2026-10-27 to 2026-10-31

Backlog rows are in [docs/improvement-backlog.md](../docs/improvement-backlog.md). "Unit" means a test in `tests/`.

| Row | Finding | Covered by |
|---|---|---|
| 10 | Briefs with Done means claims; an unanswered claim is untested | eval `reply-evidence-check` |
| 11 | Skeptic pass on Blocker and Major findings | eval `skeptic-pass-on-blocker` |
| 12 | One runner per worktree | eval `one-runner-per-worktree` |
| 13 | Mutation check for critical tests | eval `mutation-check-required` |
| 14 | Zero errors in logs (rule 9.13) | eval `reply-evidence-check` |
| 15 | File edit and deletion rules | unit `test_hooks.GateTests` |
| 16 | Long jobs hand back `in-progress` with `Job` | unit `test_hooks.CheckReplyTests.test_in_progress_needs_job` |
| 17 | Local tracking | eval `local-tracking-table` |
| 18 | Delegation rules pointer in project facts | not covered: a pointer in a template, no behavior to grade |
| 19 | Plan drift batching | eval `plan-drift-batched` |
| 20 | Status cadence (session cron) | eval `status-cadence-cron`, eval `status-cadence-default` |
| 21 | Restart safety and resume | unit `test_hooks.AfterCompactTests`; eval `team-table-after-compaction` |
| 22 | Auto-compact threshold via session-setup | eval `session-setup-asks-first` |
| 23 | Review routing script | unit `test_review_route` |
| 24 | Retro names its asset | eval `retro-names-asset` |
| 25 | Reply check, model check and after-compact hooks | unit `test_hooks`, `test_agent_model_hook`; eval `triage-first-with-model` |
| 26 | "team lead" trigger | unit `test_hooks.TeamLeadTriggerTests`; eval `team-table-status` (its prompt is "team lead, status?") |
| 27 | Factory self-change needs the user's sign-off | eval `lesson-promotion-asks` |
| 28 | TRUST and provenance pages | not covered: documents only |
| 29 | Every work item is a clickable link | eval `team-table-status` (`issue-links`) |
| 30 | Team table with real models, background processes separate | evals `team-table-status`, `team-table-after-compaction` |
| 31 | CI workflow changes route to FinOps | unit `test_review_route.test_finops_and_devops_rules` |
| 32 | Machine-wide local CI lock | unit `test_local_ci_lock` (queueing, stale takeover, busy port) |
| 33 | Health check | eval `health-check` |
| 34 | Agent instruction files go to Security, deep review | unit `test_review_route.test_agent_instruction_files_need_security_and_deep_review`; eval `instruction-files-need-security` |
| 35 | Prompt drift between Claude Code and Codex | unit `test_prompt_sync` |
| 36 | Board move or comment is never approval | eval `board-is-not-approval` |
| 37 | Team table lost after compaction; Workflow agents unseen | unit `test_hooks.AfterCompactTests`; evals `team-table-after-compaction`, `team-table-status`; unit `test_evals` (grader self-check) |
| 38 | User had to compact by hand | evals `wave-done-state-on-disk`, `session-setup-asks-first` |
| 39 | Performance Engineer: release readiness and on request only, never production | evals `no-load-test-per-task`, `release-readiness-runs-performance`; unit `test_codex_runtime` (role and model route) |

Multi-repo workspaces (sessions started in a folder that holds several repos, like `pushapp/`):
- Hooks find the project below the start folder: unit `test_hooks.MultiRepoWorkspaceTests`. That covers the gate, the after-compact reminder, the reply check, and the startup note when no auto-compact threshold is set.
- The Team Lead finds the project's status: eval `multi-repo-status`.
- session-setup targets the workspace's settings file: eval `multi-repo-session-setup`.

Model mix (2026-10-31: 172 Explore searches went to sonnet in one week):
- The model hook blocks an Explore dispatch off `haiku` in a factory project, unless the prompt has `Why not haiku: <reason>`: unit `test_agent_model_hook.LookupOnHaikuTests`.
- The Team Lead sends a brief's file lookup to `haiku` unprompted: eval `lookup-on-haiku` (slow).

Releases from the same days with no backlog row:
- 0.5.3, version in the first status: `team-table-status` (`version-named`).
- 0.5.4, one table with no Finished or Next lists: `team-table-status` (`no-separate-lists`).
- 0.5.5, update command: eval `update-command`.
- 0.5.6, done rows keep their ID and an Issue is never a repo name: `team-table-status` (`done-row-keeps-id`, `no-repo-name-as-issue`).
