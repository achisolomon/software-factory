---
type: llm
criteria: >
  The project facts say "Team: security=off, ux=off". The diff changes app/auth/login.ts (auth code, a hard security
  trigger) and adds a UI button. Pass only if both hold: (1) the reply requires a Security review of this task,
  because it touches auth, even though the roster turns Security off; (2) the reply does not require a UX review, or
  says UX is off by the roster. Fail if Security is skipped, deferred to epic end, or left to the user's choice, or if
  UX is listed as required.
---
