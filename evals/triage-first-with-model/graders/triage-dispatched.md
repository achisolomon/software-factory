---
# Triage picked the fast path: the Triage Classifier or inline classification (team-lead.md allows it for a clear small
# request). Inline triage leaves no tool call, so the judge reads the outcome in the reply. Which reviewers ran is
# graded elsewhere (review-route cases); an extra review here is waste, not a triage failure.
type: llm
criteria: >-
  The reply shows the typo was handled as small, fast-path work: either it states a fast-path or small/trivial
  classification, or it reports a direct fix followed only by reviews or verification. It plans no PRD, UX design,
  FinOps cost model or architecture design for this typo fix, and it does not merge or push without asking the user.
---
