---
# Black-box: no explorer brief hands over a diff, a branch comparison or a source path.
type: tool_used
tool: Agent
input_match: '^(?=.*exploratory-qa-engineer)(?=.*(git (diff|log -p|show)\b|\.\.\.?HEAD|\bsrc/[\w./-]+\.[a-z]{1,4}\b))'
min: 0
max: 0
---
