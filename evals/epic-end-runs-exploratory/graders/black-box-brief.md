---
# Judged on the trace, not the last message: a dispatched explorer may return early and turn the reply into a blocker.
type: llm
focus: trace
criteria: >
  The run dispatches an Exploratory QA Engineer for epic 2 (coupons); judge the prompt of that Agent call. The brief
  names the epic's stories and acceptance criteria (or the task Done-means claims) and the environment to use. It
  passes the explorer no diff, no branch comparison and no src/ path or source file to read, and it does not ask
  the explorer to review code. The dispatch is one explorer session for the whole epic, not one per task. Pass only
  if all of this holds.
---
