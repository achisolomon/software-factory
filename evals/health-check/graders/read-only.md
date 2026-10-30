---
# The health check is read-only: it never prunes, removes, commits, resets or kills anything.
type: tool_used
tool: Bash
input_match: 'git\s+(push|commit|reset|clean|stash|checkout|switch|merge|rebase|worktree\s+(remove|prune|add))|\brm\s|\bkill\b'
min: 0
max: 0
---
