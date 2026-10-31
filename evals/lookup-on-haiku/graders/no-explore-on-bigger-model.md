---
# No Explore search is even attempted on sonnet or opus (the model hook would block it; this checks the rule itself).
type: tool_used
tool: Agent
input_match: '"Explore".*"model"\s*:\s*"(sonnet|opus)"|"model"\s*:\s*"(sonnet|opus)".*"Explore"'
min: 0
max: 0
---
