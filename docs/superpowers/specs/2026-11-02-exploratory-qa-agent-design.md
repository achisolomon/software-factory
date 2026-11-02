# Design: Exploratory QA Engineer agent

## Context
The factory tests white-box only. `test-automation-engineer` reads the diff, maps acceptance criteria to tests and runs them. Nobody plays the old-school QA role: use the running product as a user would, put the data into odd states and hunt for bugs nobody wrote a test for. This design adds a black-box exploratory tester that can change DB state in disposable environments.

Decisions from the user:
- Runs at **epic end** and **on request**. It is not a per-task reviewer and not part of Release readiness.
- DB writes go to **local/disposable environments only**. A shared environment needs the user's approval, quoted by the Team Lead. Production is never allowed.
- **Black-box first.** The agent reads source code only after it has reproduced a bug, to point to the likely cause.
- For each confirmed bug it **writes a failing regression test**, besides the report and the issue.
- **Reuse [tester-army/e2e](https://github.com/tester-army/e2e) (Apache-2.0)**: adapt its explore and bug-bash method in our own words. Use `npx e2e explore` as an optional UI driver only.

## What we take from tester-army/e2e
Sources: `skills/e2e/references/bug-bash.md`, `skills/e2e/references/explore.md` and `docs/explore.mdx`, reviewed 2026-11-02.
- **Charters:** one area, one posture, one sentence, naming the start route and the account. Five to ten per session. **Postures** are first-time user, numbers and copy (skeptic: cross-check every number), edge input (an exact input matrix: empty, 300 chars, unicode, leading spaces, special chars), state (create, rename, delete, then reload or go back) and error paths. We add a **data-state** posture: put the DB in a state, then walk the flow.
- **Finding shape:** title, issue or warning, severity 1 to 5, expected, actual, reproduction steps, path, evidence.
- **Triage buckets before any test:** explorer artifact, environment (missing key or service), design (code or tests say it is intended), fixture (seed data is unrealistic) and candidate. This is the point where reading code is allowed.
- **Verify rule:** a finding is a claim. It counts as confirmed only when a repro test fails on the assertion that encodes the bug. A locator error or a timeout means the test is wrong. A pass means the bug did not reproduce, so the finding is rejected.
- **Isolation:** one seeded account or workspace per charter, so explorers do not report each other's edits. Explore a production build, not a dev server.
- **Report order:** confirmed bugs (most severe first), then environment risks marked unverified, then rejected findings by reason, then warnings, then the charters run and the areas no charter reached.
- **Tagging:** repro tests are tagged `exploratory`. The gating run excludes them until the bug is fixed. Then the tag is removed and the test stays as a regression test.
- **Optional tool:** when the project already has `e2e.config.ts`, or the user approves adding it, the agent may run `npx e2e explore '<charter>' --output .e2e/explore/<slug>` for UI charters and read `report.json`, with `E2E_TELEMETRY_DISABLED=1` set. Otherwise it drives the UI with Playwright through `skills/frontend-testing`. DB state and API probing are always our own (e2e has neither).
- Not taken: the parallel `xargs` fan-out, the bug-bash config template and the MCP locator workflow. They are e2e-specific and can be added later if needed.
- Add a row to `docs/provenance.md` (licence Apache-2.0).

## Approach (recommended: standalone agent)
- **A. New agent `exploratory-qa-engineer` (chosen).** It has its own stance (curious user, no code), its own trigger and its own report. It stays independent of the Test Engineer's view of the code.
- B. An "Explore" mode on `test-automation-engineer`. Rejected: that agent has already read the diff, so it cannot be black-box, and its file is already 168 lines.
- C. A skill the Test Engineer loads. Rejected for the same independence reason.

## Agent definition: `agents/exploratory-qa-engineer.md`
Frontmatter: tools `Read, Grep, Glob, Write, Edit, Bash, WebSearch, WebFetch`, model `sonnet` (Team Lead may use `opus` for auth, payments or data deletion), color `orange`, memory `project`.

**Inputs it may read before it finds a bug:** the PRD, the stories and their acceptance criteria, `contracts/`, the DB schema and migrations (read only, to learn the states the data can be in), `project-facts.md`, the brain, and the running app (UI, API, CLI, logs, browser console). It never reads `src/`, the diffs or the unit tests during exploration.

**Code access after a reproduction:** once a bug has reproduced at least twice from clean state, it may Read/Grep the code to name a suspected `file:line`. It records in the report that it read code from that point on.

**Session flow (one session per run, 5 to 10 charters, run one after another):**
1. **Charters** (format and postures from the e2e section above). Write the mission, the scope (an epic's stories or the user's ask), a timebox counted in actions, and the risk heuristics it will use. Heuristics: CRUD on every entity, interrupts (back, refresh, double-submit, two tabs), boundaries, bad and hostile input, locale/time zone/clock, permissions and roles, state transitions (expired, cancelled, deleted parent, half-migrated), volume, and a dependency that is down or slow.
2. **Environment.** Start or reuse the local/disposable stack (the project's local CI script, docker compose or the emulators named in project facts). Take the machine-wide lock (`reference/local-ci-lock.sh`) when ports are fixed. Refuse to work against any environment not marked local or disposable unless the brief quotes the user's approval naming it.
3. **State setup.** Seed or change data directly in the DB (SQL or the DB's CLI) or through admin APIs, so the app sits in the states the charter targets. Record every setup step so a bug can be reproduced. Reset to clean state between probes that would contaminate each other.
4. **Explore.** Drive the product through the UI (the `frontend-testing` skill for browser work), the API (curl or HTTP clients) and the CLI. Keep a running session log: each action, what was expected and what was observed.
5. **Merge and triage.** Merge duplicates. Sort each finding into the e2e buckets, reading the code here to settle design and fixture questions. Only candidates go on.
6. **Verify by failing test.** For each candidate, write a repro test at the lowest level that proves it (API or integration test when the bug is in data or the API, E2E when it is in the UI), in `tests/exploratory/` tagged `exploratory`. Confirmed only when it fails on the bug's assertion from clean state. Otherwise fix the test or reject the finding. Record the suspected `file:line` cause. Rejected findings keep their reason.
7. **File** each Blocker and Major as a GitHub issue per contract section 5. The body has the steps to reproduce, the state setup, the evidence (screenshot, response, log line), the suspected cause and the test path.
8. **Report** at `docs/testing/exploratory/<date>-<scope>.md`, in the e2e report order, plus the environment and commit, the state setups used, the log error counts and the regression tests added.

**Hard rules (mirroring siblings):** never touch production. Never write to a DB that it did not start or that is not approved. Never change application code. Never weaken tests. Files are changed with Edit and Write only. It deletes only files it created. No real personal data. It never pushes or merges.

## Wiring changes
- `reference/handoff-contract.md`: a roster row (owns `docs/testing/exploratory/` and `tests/exploratory/`, runs at epic end and on request), the artifact map entry, an ownership row, and the findings-as-issues list.
- `agents/team-lead.md`: a team table row, a trigger paragraph like the Performance Engineer's, and Build loop step 11 (Retro at epic end) preceded by "run the Exploratory QA Engineer on the epic's stories". Its findings go through the normal fix loop and skeptic pass. The model table gets an `opus` exception.
- `agents/test-automation-engineer.md`: one line saying `tests/exploratory/` tests come from the explorer. The Test Engineer reviews them at the next Verify and keeps them in regression.
- `docs/provenance.md`: a row for tester-army/e2e.
- DevOps/Test: the gating run excludes the `exploratory` tag (a note in the agent and the Test Engineer, no CI change by default).
- `.claude-plugin/plugin.json` description and version bump (minor), `README.md` agent list, `CHANGELOG.md`.
- Evals (pattern: `evals/release-readiness-runs-performance/`): `epic-end-runs-exploratory` (Team Lead dispatches it at epic end) and `exploratory-not-per-task` (no dispatch on a single task).
- `tests/test_evals.py` / other tests: check whether they count the agent roster and update them if so.

## Implementation process
Work happens on branch `worktree-exploratory-qa-agent`. After this spec is reviewed, the writing-plans skill produces the implementation plan, and then the plan is implemented.

## Verification
- `python -m pytest tests/` passes, evals included.
- Run the two new evals with the repo's eval runner (see `evals/README.md`).
- Run a manual smoke test: load the plugin locally, ask the Team Lead "run exploratory QA on epic X" in a sample project, and confirm it dispatches `exploratory-qa-engineer` with a black-box brief.

Skipped: a dedicated DB-state helper script (the agent uses the project's own tools); Release-readiness placement (user chose epic end).
