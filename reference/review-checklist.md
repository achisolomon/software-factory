# Review checklist (Developer self-check)

Before you hand a task back, check your diff against the sections for the reviewers your brief names, then against the `Recurring review findings` in `docs/factory/brain.md`. Fix what you find. Each item below is something a reviewer raises as Blocker or Major; one more fix round costs a full re-review, this check costs one read. The reviewers' own agent files stay the authority; this is the short list.

## Every task (Test Engineer and Architect always review)

- Every acceptance criterion the task covers has a test that would fail without your change. Unhappy paths are covered: invalid input, unauthorized caller, missing data, dependency timeout, retry and idempotency, boundary values.
- Every behavior you add is reachable through an API, contract, CLI or event, so a test drives it. Behavior testable only by hand is Major.
- Tests assert results, not only that code ran. No mocks that hide the behavior under test.
- Formatter, linter, type checker and tests pass with zero errors and no new warnings. Test, app and console output show no new errors. Never mute logs or swallow exceptions to get there.
- The code follows the documented layering and every ADR rule the task cites. No reaching into another component's internals or data store.
- No duplicated business rule, validation or query: reuse the existing one. No debug prints, dead code, commented-out code or TODO without an issue.
- Errors are handled, carry context and are logged at the right level. No unbounded query, N+1 query or missing pagination on a list.
- Only the files in your brief changed, plus their tests and the callers a signature change forces.

## Security (when the brief names it)

- Every protected route checks authentication, and every object access checks authorization on the server (no IDOR). Security rules (database, storage) deny by default and match the code's access model.
- All input is validated at the trust boundary: type, length, allowed characters, range. No string-built SQL, NoSQL, shell or template commands. No URL fetched from user input without an allow-list (SSRF).
- Output is encoded for its context (no raw `innerHTML` with user data). State-changing requests are protected against CSRF; CORS is not wide open.
- No secrets, tokens or personal data in code, logs, fixtures, error messages or issues. Expensive or sensitive operations have a rate limit.
- A new dependency is maintained, has a fitting license and no known CVE, is pinned, and its lockfile is committed. List it in your reply.

## UX (when the brief names it)

- The screen matches its spec: layout, every state (loading, empty, error, success), interactions and copy.
- Every input has a label, focus order follows the visual order, everything works by keyboard, and text contrast meets WCAG AA.
- Errors say what went wrong and how to fix it, next to the field, without clearing what the user typed.

## FinOps (when the brief names it)

- No new paid resource, larger tier, longer retention or new paid API call without a note of its monthly cost in your reply.
- No polling where an event or cache would do; paid calls are cached when the answer does not change per call.
- CI changes: no new trigger, matrix entry, larger runner or longer artifact retention unless the task asks for it.

## DevOps (when the brief names it)

- Pipelines and infrastructure changes validate locally (lint, `plan`, dry run). Nothing applies or deploys.
- New configuration has a default for local runs and is documented where setup is described.
