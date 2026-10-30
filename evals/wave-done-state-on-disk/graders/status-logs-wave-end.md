---
# status.md records that wave 3 finished, so a compaction right now loses nothing.
type: regex
flags: i
pattern: 'wave[ -]?3[^\n]*(finished|done|complete)'
match: contains
target: {source: file, path: docs/factory/status.md}
---
