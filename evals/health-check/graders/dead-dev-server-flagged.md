---
# The dev stack recorded in Background processes is not listening: flagged.
type: regex
flags: i
pattern: '(dev stack|3000|8080|bg7k2)[^\n]*\b(warn|fail)\b|\b(warn|fail)\b[^\n]*(dev stack|3000|8080|bg7k2)'
match: contains
---
