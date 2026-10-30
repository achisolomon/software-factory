---
# Running sessions keep the old version: the reply says to reload (or restart) and start a new chat.
type: regex
flags: i
pattern: '(reload window|restart claude code)[\s\S]*new (chat|session)|new (chat|session)[\s\S]*(reload window|restart claude code)'
match: contains
---
