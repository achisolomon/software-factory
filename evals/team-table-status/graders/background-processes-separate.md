---
# The dev server is reported in a separate Background processes table, after the agents.
type: regex
pattern: 'Background processes[\s\S]*npm run dev'
match: contains
---
