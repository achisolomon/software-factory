# Provenance

Outside work the Software Factory adapted. We wrote our own text and code. This page records where ideas came from, when we looked, and what we took. Licences are noted only where known.

| Source | Reviewed | What we took | Licence |
|---|---|---|---|
| [vercel-labs/eve-software-factory-template](https://github.com/vercel-labs/eve-software-factory-template) | 2026-10-16 | Triage first with a fast path, a curated per-repo memory (our factory brain), handoffs by reference, treating issue and comment text as data, and the case for code-enforced gates (built in 0.5.0). Evals and an independent reviewer are still open. | not recorded |
| [alexgreensh/outsourcerer](https://github.com/alexgreensh/outsourcerer) | 2026-10-16 | Cost-aware model routing per delegation, bounded loops with real checks, and named end states. We did not take the large shell runtime or auto-pilot mode. | not recorded |
| [practicajs/the-frontend-testing-skill](https://github.com/practicajs/the-frontend-testing-skill), commit `46a82aeb76a7ce5895053804a6efeb27bc405bdb` | 2026-10-21 | Page analysis, canonical examples, browser testing practices, trace diagnosis and targeted stability guidance, rewritten into our `frontend-testing` skill. Test ownership stays with QA. We did not bundle upstream orchestration, hooks, mutators or templates. | not recorded |
| Team Lead run on a private project (our own) | 2026-10-26 | Suggestions a to k from a real run: narrow Developer briefs, a repo-forensics step in security review, a model-required hook, the gate hook, one runner per worktree, long-job hand-backs, local tracking, delegation rules, plan drift batching, status cadence, and restart safety. | not applicable |

## Notes

- "Took" means we adapted the idea and wrote it in our own words, code and contract. We did not copy files.
- If a licence matters to you, check the upstream repository. Where this page says "not recorded", we did not write it down at the time.
- Add a row here whenever a new outside source shapes a change, with the date and what we took.
