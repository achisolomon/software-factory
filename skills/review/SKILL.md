---
name: review
description: Run a full team review of the current changes, a branch, a task or the whole codebase — architecture and clean-code review, security review, test verification, and cost review when infrastructure changed — and consolidate one verdict.
argument-hint: "[task ID | branch | path | 'all']"
disable-model-invocation: true
---

# Team review

Act as the Team Lead (`${CLAUDE_PLUGIN_ROOT}/agents/team-lead.md`) and apply the contract (`${CLAUDE_PLUGIN_ROOT}/reference/handoff-contract.md`).

Scope requested: $ARGUMENTS

1. **Resolve the scope.** Empty → uncommitted changes plus the current branch versus the main branch (`git diff main...HEAD` and `git status`). A task ID → its branch. A path → that module. `all` → the whole codebase.
2. **Check the baseline.** If `docs/architecture/repo-map.md` is missing for an existing codebase, the Architect runs Map mode first.
3. **Run in parallel**, each writing its report per the contract, with the model set per the Team Lead's model policy, and given the report paths and diff range by reference (never pasted):
   - `software-factory:software-architect` — Review mode (architecture conformance, clean code, OO design, DRY, patterns, scalability, standards).
   - `software-factory:security-engineer` — Review mode.
   - `software-factory:test-automation-engineer` — Verify mode for a task; for other scopes, run the suites and assess coverage and test quality.
   - `software-factory:finops-engineer` — Review mode, only if infrastructure, scaling, retention or paid third-party APIs changed.
4. **Consolidate** for the user: one overall verdict (the strictest of the reviewers), a single table of Blocker and Major findings across reviewers (deduplicated, each with its report link), counts of Minor/Nit, and the recommended next step (e.g. hand the findings to the Developer in Fix mode).
5. Do not fix anything in this command; ask the user whether to send the findings to the Developer.
