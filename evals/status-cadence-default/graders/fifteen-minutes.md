---
# The default interval is 15 minutes: `*/15` or four minutes an hour (CronCreate prefers off-zero minutes, e.g. 4,19,34,49).
type: tool_used
tool: CronCreate
input_match: '"cron"\s*:\s*"(\*/15|\d+,\d+,\d+,\d+) \*'
min: 1
---
