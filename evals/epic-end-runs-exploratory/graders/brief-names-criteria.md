---
# The explorer's brief sends it to the stories and acceptance criteria. Judged on the Agent call input, not the reply:
# the dispatched explorer can return early and turn the last message into a blocker, and an llm judge on the whole
# trace misses a brief early in a long trace. The input is serialized JSON, so `.` spans the whole prompt.
type: tool_used
tool: Agent
input_match: '^(?=.*exploratory-qa-engineer)(?=.*([Aa]cceptance criteria|Done means))'
min: 1
---
