---
name: frontend-testing
description: Plan, write, debug, and verify browser tests for web UI changes using the existing Test Automation Engineer. Use for page or component behavior, responsive layouts, keyboard accessibility, and browser failures; skip for backend-only work and ordinary unit tests.
---

# Frontend testing

Use the project's existing framework and the factory's ownership, approval and reporting rules. The Test Automation Engineer owns browser test code and evidence; the Developer owns application fixes; UX owns experience requirements. This skill adds no agent, global hook, MCP installation or additional user approval gate.

## Scope and plan

Read the task's acceptance criteria, relevant UX specs, changed UI code, runner configuration and one canonical working browser test. Reuse the app's existing fixtures, authentication and network interception patterns. If no canonical test exists, establish one representative test rather than introducing another framework by default.

Identify the task's base commit and include committed and uncommitted changes in the review scope. Discover tests using the configured runner, including its `.spec.*`, `.test.*` and project-specific patterns; do not infer scope from the last N commits. Map criterion IDs to actual test names and files. Record a short plan in `docs/testing/reports/T-NNN.md`; use the contract's dated report convention for work without a task ID. No fixed cap on scenarios: cover the requirements and prioritize risk.

## Inspect before writing

For changed pages, inspect interactive elements, accessible names, network boundaries and loading/empty/error/success states. Use a live local or staging browser when available; label source-only analysis explicitly. Never claim browser behavior was verified from reading source. Record unavailable runtime checks as a gap and withhold approval when a required criterion remains unproven.

For browser interaction, use the browser tool available in the runtime or the project's test runner. The QA role must be granted that tool before delegation if needed; a skill cannot grant tool access. Do not install a new MCP server automatically.

## Write useful tests

- Assert visible user outcomes tied to arranged data, including invalid input and API failures where relevant. Prefer roles, labels and accessible names; use stable test IDs when semantics cannot uniquely identify a target. Missing semantics are a Developer/UX finding, not permission for QA to edit application code.
- Use auto-waiting actions and retrying assertions. No sleeps, shared mutable state or test-order dependence. Build isolated data and register network routes before navigation.
- Mock at the network boundary for page/component tests; keep internal application behavior real. Maintain selected critical journeys through the real non-production backend. Label mocked page coverage separately from full-stack E2E evidence.
- Exercise required breakpoints, keyboard navigation, focus transitions and relevant accessibility checks. Automated accessibility checks alone do not establish WCAG conformance. Use existing visual baselines only where meaningful; inspect differences before accepting a new baseline.
- Keep tests readable with one behavior and clear arrange/act/assert phases. Do not enforce arbitrary statement or assertion counts at the expense of proving a requirement.

## Verify and debug

Run targeted tests first and the required task suites afterward. Repeat new or changed browser tests three times with retries disabled, recording each result. Repeat broader suites only for changed code, failure, release requirements or unresolved risk. Three successful runs are a stability sample, not proof that a test cannot be flaky.

For failures, capture traces and inspect the failing action, DOM state, network response and console evidence. Classify the cause as application defect, test defect or environment issue. Fix only demonstrated test defects; never weaken assertions, skip tests or accept new screenshots to hide an application regression. Hand application defects to the Developer with a reproduction.

Use the existing coverage tool if available. Compare unique covered/total lines on the same file scope and denominator; do not sum per-test coverage percentages. Mark unavailable coverage as unknown. Mutation testing is optional for selected critical logic and runs only in a disposable isolated checkout, with checks that source is restored; never mutate the shared working directory.

## Report

Extend the existing task report with criterion-to-test mapping, commit and dirty-worktree scope, model, commands, per-run pass/fail/skipped counts, runtime/browser/viewport, mocked versus real-backend scope, findings, evidence paths and untested requirements. Save large traces/logs as artifacts; return only relevant excerpts and paths. Record usage only when the runtime supplies it. Missing evidence never becomes a passing result.

The workflow was informed by [Practica's frontend testing skill](https://github.com/practicajs/the-frontend-testing-skill), reviewed at commit `46a82aeb76a7ce5895053804a6efeb27bc405bdb`. These are factory-specific instructions; no upstream scripts, agents or report templates are bundled.
