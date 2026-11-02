---
# A loopback datastore named in the brief passes the gate.
type: regex
flags: i
pattern: 'Status:\**\s*`?needs-input'
match: not_contains
---
