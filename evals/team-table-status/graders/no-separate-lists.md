---
# No separate "Finished" or "Next" lists: done and to do are rows of the one table (0.5.4).
type: regex
pattern: '^\W*(Finished|Next( steps)?)\W*$'
flags: m
match: not_contains
---
