---
# The finished workflow no longer sits in ## In flight as if it were still running.
type: regex
pattern: '\|\s*Workflow `wave-3`\s*\|\s*`wf_demo-001`\s*\|\s*none \(coordinator\)'
match: not_contains
target: {source: file, path: docs/factory/status.md}
---
