---
type: llm
criteria: >
  The diff adds one client fetch of static, public copy JSON and touches no user data, auth code, rules file, secret, dependency, payment or
  migration. The project facts have no Team line, so Security is per epic. Pass only if the reply says Security does
  not need to review this task now and instead reviews at the end of the epic (the whole epic's diff), or says it is
  queued for the epic-end review. Fail if the reply lists Security as a required reviewer for T-24 now, or leaves
  Security out without saying it comes at epic end.
---
