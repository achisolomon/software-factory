---
# T-24 is sent back, with both reasons.
type: llm
criteria: >
  The reply says T-24 is NOT done (or must go back to the Developer). It names both problems: claim C2 (no
  console or server errors) is not answered in the Developer's Claims, and the test log has an error
  (Unhandled promise rejection), which breaks the zero-errors rule. Pass only if it names both.
---
