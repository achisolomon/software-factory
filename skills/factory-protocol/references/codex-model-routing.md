# Codex model routing

Use this policy for the CLI runner and native Codex delegation. Claude agent frontmatter does not select a Codex model. The main chat's model picker is separate: the policy cannot switch an already-running chat.

## Economical defaults

| Work | Model / runner mode |
|---|---|
| Team Lead coordination, triage, routine test execution, report summaries, routine UX and cost checks | `gpt-6-luna` / `--mode routine` |
| Small, clearly specified implementation or mechanical work in any role | `gpt-6-luna` / `--mode routine` |
| Substantial implementation, independent architecture/code review, product planning, security, infrastructure design | `gpt-6.1-sol` / `--mode quality` |
| Difficult unresolved architecture, security or debugging decision after Sol evidence | Explicit `--model gpt-6-astra` |

The runner defaults Team Lead, Triage, Test, UX and FinOps to Luna; other roles to Sol. Use quality mode for test strategy, difficult diagnosis, substantial UX design, unfamiliar code analysis and complex cost models. Use routine mode for a small well-specified Developer task. A role's task complexity can override its default. Check account availability before using a model; if unavailable, report it and select an available model deliberately, never silently fall back. Terra remains available through an explicit override where supported.

Prefer Standard speed in the app. Do not enable Fast/Ultrafast or increase reasoning globally as part of installation. Use low reasoning for mechanical tasks and medium for routine implementation where the selected runtime supports it; increase only for a demonstrated need. These are operator settings, not settings enforced by this runner.

## Delegation and context

- Classify simple requests inline in the Team Lead where the runtime permits; use a separate triage agent for ambiguous or substantial requests. Status and answer-only requests need no specialist sessions.
- Keep all required reviewers and approval gates. Scope conditional reviewers to the actual diff. Full-team lifecycle work is for substantial features and releases; small changes use the existing fast path.
- Give each specialist one objective, acceptance criteria, exact input paths/sections, base commit, output paths and approval constraints. Use fresh focused context when supported; do not forward the full conversation or entire product documents.
- Read the role and shared contract, then only task-relevant project facts, brain notes, stories and ADRs. Expand context for concrete dependencies or uncertainty.
- Search named directories first. Exclude dependencies, generated output, duplicate/nested checkouts and archived reports unless relevant. Filter repository API responses before printing; save large logs and return only failure excerpts and paths.
- Run the targeted checks first, then the required task checks. Repeat only for a change, failure, stability requirement or unresolved risk. Preserve independent QA execution; avoid repeated successful runs with no purpose.
- Load frontend-testing only for UI testing. Repeat new/changed browser tests with retries disabled; reserve mutation testing for selected critical behavior in disposable checkouts.

## Escalation and measurement

After two unsuccessful Luna attempts on the same problem, stop that delegation and return the failing command, relevant output, files examined and what was tried. The Team Lead resumes the task on Sol with that evidence; this is not an additional fix-round allowance. Reserve Astra for a particular unresolved decision after a Sol pass. Never remove a required check or gate to save quota.

Record the model, attempts, checks, elapsed time and usage when the runtime exposes it. Mark unavailable usage as unknown; never estimate account quota from output length. Compare allowance per successfully completed task on representative work before claiming savings.

## CLI examples

Run from the target repository, or supply `--project-dir`. Team Lead is interactive and requires a Git repository; specialist roles use `codex exec` and support non-Git targets.

```bash
/path/to/software-factory/scripts/run-codex-agent software-developer --mode routine -- 'Implement the small, specified task T-027.'
/path/to/software-factory/scripts/run-codex-agent test-automation-engineer --mode quality -- 'Diagnose the reproducible failure in T-027.'
/path/to/software-factory/scripts/run-codex-agent team-lead --dry-run -- 'Plan T-027.'
```

For native delegation, explicitly select the supported model where the tool allows it. If model overrides are unavailable, report that limitation; role labels and skills alone do not change the executing model.
