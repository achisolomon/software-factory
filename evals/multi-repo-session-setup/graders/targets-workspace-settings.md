---
# The proposed file is the workspace's .claude/settings.json.
type: llm
criteria: >
  The reply proposes to write env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE to the
  .claude/settings.json of the folder the session started in (the workspace root),
  not to Projects/shop project/.claude/settings.json, and explains that this covers
  every repo below it. It asks before writing. Pass only if all of this holds.
---
