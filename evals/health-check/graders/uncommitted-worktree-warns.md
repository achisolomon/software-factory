---
# The worktree with uncommitted work is flagged.
type: regex
flags: i
pattern: '(lane-copy[^\n]*\b(warn|fail)\b|\b(warn|fail)\b[^\n]*lane-copy)'
match: contains
---
