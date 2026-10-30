---
# The two corrections are batched.
type: llm
criteria: >
  The reply accepts the review (it passed) and collects the two plan-text corrections (T-30 wording and the
  stale ADR name) for one Architect maintenance pass at epic end or before the dependent task, instead of
  sending them now. Pass only if it batches them.
---
