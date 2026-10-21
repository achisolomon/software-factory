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
3. **Run in parallel**, each writing its report per the contract, with the model set per the Team Lead's model policy, and given the report paths and diff range by reference (never pasted):
   - Software Architect — Review mode (architecture conformance, clean code, OO design, DRY, patterns, scalability, standards).
   - Security Engineer — Review mode.
   - Test Automation Engineer — Verify mode for a task; for other scopes, run the suites and assess coverage and test quality.
   - FinOps Engineer — Review mode, only if infrastructure, scaling, retention or paid third-party APIs changed.
   In Claude Code, delegate with the `software-factory:` agent names. In Codex, use native Codex delegation and include the matching Specialist procedure from `../factory-protocol/references/role-playbook.md` in each delegation.
4. **Consolidate** for the user: one overall verdict (the strictest of the reviewers), a single table of Blocker and Major findings across reviewers (deduplicated, each with its report link), counts of Minor/Nit, and the recommended next step (e.g. hand the findings to the Developer in Fix mode).
5. Do not fix anything in this command; ask the user whether to send the findings to the Developer.
