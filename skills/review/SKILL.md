---
name: review
description: Run a full team review of the current changes, a branch, a task or the whole codebase — architecture and clean-code review, security review, test verification, and cost review when infrastructure changed — and consolidate one verdict.
argument-hint: "[task ID | branch | path | 'all']"
disable-model-invocation: true
---

# Team review

Act as the Team Lead. In Claude Code, read `${CLAUDE_PLUGIN_ROOT}/agents/team-lead.md` and apply `${CLAUDE_PLUGIN_ROOT}/reference/handoff-contract.md`. In Codex, read `../factory-protocol/references/role-playbook.md`, resolved relative to this skill's `SKILL.md`.

Use the review scope in the user's request that invoked this skill.

1. **Resolve the scope.** Empty → uncommitted changes plus the current branch versus the main branch (`git diff main...HEAD` and `git status`). A task ID → its branch. A path → that module. `all` → the whole codebase.
2. **Check the baseline.** If `docs/architecture/repo-map.md` is missing for an existing codebase, the Architect runs Map mode first.
3. **Route.** For a diff scope, run `${CLAUDE_PLUGIN_ROOT}/scripts/review-route [base]` (default base `main`; Codex: `scripts/review-route` from the plugin root). It can add reviewers and raise depth to `deep`, never drop one; if it fails or its output is unclear, add more review, not less. Every reviewer the route marks `required` runs, DevOps included. `deep` means: Architect on `fable` (`opus` once Fable is exhausted; Codex: per its routing) and Security on `opus`, Security always runs, and the skeptic pass uses `opus`. Use its `reviewers` list and `depth` below.
4. **Run in parallel**, each writing its report per the contract, with the model set per the Team Lead's model policy, and given the report paths and diff range by reference (never pasted):
   - Software Architect — Review mode (architecture conformance, clean code, OO design, DRY, patterns, scalability, standards).
   - Security Engineer — Review mode.
   - Test Automation Engineer — Verify mode for a task; for other scopes, run the suites and assess coverage and test quality.
   - FinOps Engineer, Review mode, only if infrastructure, scaling, retention, paid third-party APIs or CI workflows (GitHub Actions minutes) changed (or the route marks it required).
   One runner per shared worktree: the Test Engineer holds the runner slot while the others review statically; the Architect's fast check runs after the Test Engineer returns.
   In Claude Code, delegate with the `software-factory:` agent names. In Codex, use native Codex delegation and include the matching Specialist procedure from `../factory-protocol/references/role-playbook.md` in each delegation.
5. **Skeptic pass.** For each Blocker or Major, run one read-only skeptic agent (same role type as the reviewer, `sonnet`; `opus` for Security Blockers and auth, payments or data deletion) whose only job is to refute the finding with evidence (`file:line`, command output). A refuted or downgraded finding gets a comment with that evidence on its issue (in the report when Tracking is local); never a silent drop. A finding the skeptic cannot refute stands. A Security Blocker is downgraded only with the Security Engineer's agreement. Skeptic runs are not fix rounds.
6. **Consolidate** for the user: one overall verdict (the strictest of the reviewers), a single table of Blocker and Major findings across reviewers (deduplicated, each with its report link, noting any skeptic outcome), counts of Minor/Nit, and the recommended next step (e.g. hand the findings to the Developer in Fix mode).
7. Do not fix anything in this command; ask the user whether to send the findings to the Developer.
