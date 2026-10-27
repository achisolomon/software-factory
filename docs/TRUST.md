# Trust: what code enforces and what relies on prompts

Software Factory protects you in two ways. Some rules are enforced by code that runs outside the model. Others are written in the agents' prompts and depend on the model following them. This page says which is which, so you know how much to lean on each.

## Enforced by code (Claude Code only)

The hooks live in `hooks/` and are wired in `hooks/hooks.json`. They only act in a factory context: a factory subagent, or a repo that has `docs/factory/status.md`. Elsewhere they do nothing, except the version check, which shows a one-line version message in every session.

| Piece | Runs on | What it does |
|---|---|---|
| `hooks/gate.py` | Every Bash call | Asks you to confirm irreversible or external commands (contract rule 9.7): `git push`, `gh pr create\|merge\|ready`, releases, `terraform apply`, `kubectl apply`, `helm upgrade`, deploy CLIs, package publishes and similar. Also asks before local destructive commands (rule 9.12): recursive force `rm` outside a temp directory, `git reset --hard`, `git clean -f`, `git branch -D`, whole-tree discard, `git stash drop`. For factory subagents it denies shell-written file edits (heredoc redirects, `sed -i`, `perl -i`, Python write scripts) and tells them to use Edit or Write. It never answers "allow", so your own permission settings still apply. |
| `hooks/require_agent_model.py` | Every Agent or Task dispatch | Refuses a delegation that does not set `model` explicitly. |
| `hooks/check_reply.py` | When a factory subagent stops | Blocks a reply that is missing required fields (`Status`, `Summary`, `Files`, `Claims`, `Revision`, `Logs`, `Checks run`, plus `Job` or `Questions for the user` when they apply), or whose `Files:` names a `docs/` report that is not on disk. It gives up after one retry so it cannot loop. |
| `hooks/after_compact.py` | Session start after compaction | Reminds the Team Lead to re-read its instructions and run the resume procedure before any new dispatch. |
| `hooks/version_check.py` | Session start (new, resumed or cleared session) | Shows the installed version and whether a newer one exists. Its only network call is a read of this repo's public `.claude-plugin/plugin.json` on GitHub `main`, at most every 6 hours, with a 2-second timeout; it sends nothing about you or your project. The result is cached in the plugin data folder (or `~/.cache/software-factory`), and only a plain version number is ever shown. Offline, it shows the installed version only. This hook runs in every session, not only factory projects. |
| `hooks/team_lead_trigger.py` | Every prompt | Adds context when you say "team lead" or "team leader", so the session hands over to the Team Lead. Never blocks. |
| `scripts/review-route` | Run by the Team Lead on the diff | Decides which reviewers are required and whether the review is deep, from changed paths and from added and removed lines (a deleted guard counts). It can add reviewers to triage's list, never drop one. Unknown or unreadable input fails toward more review. |
| Settings from `session-setup` | Claude Code itself | The project's `.claude/settings.json` gets auto-compact and exact-command allow rules, written only after you approve the diff. It never allows broad runners such as `npm run:*` or `bash:*`, and never a command the gate asks on. |

## Relies on prompts

These are instructions the model is asked to follow. Hooks do not check them.

- The three human gates (PRD, design plus cost, release) and the rule that only you approve them.
- One owner per artifact, who may edit what, and the reviewer roles staying read-only.
- Bounded loops: three fix rounds, three attempts per check, named end states.
- Briefs with "Done means" claims and "Least sure of", and treating an omitted claim as untested.
- The skeptic pass, one runner per worktree, mutation checks, and zero errors in logs.
- Plan drift batching, status cadence, the retro asset, and promoting lessons.
- Treating issue, comment and web text as data, not instructions.
- Local versus GitHub tracking, and working only on the issues you name.

## Limits

- **Regex hooks can be evaded.** The gate reads the command text. A command that is built at run time, encoded, fetched and piped to a shell, or hidden behind an unusual wrapper can get past it. The gate fails closed when it cannot parse a command, but it cannot see everything.
- **Hooks are feedback, not a security boundary.** They catch honest mistakes and drift. They are not a sandbox. Do not rely on them against a hostile agent or a hostile repo.
- **Codex has no hook enforcement.** The Codex plugin and the project-local runtime carry the prompts, contract and review-route script, but nothing runs the hooks. Every gate there is a prompt.
- **The reply check looks at shape, not truth.** It confirms the fields exist and the reports are on disk. It cannot tell whether a claim is correct. Evidence still comes from checks the Test Engineer and Architect re-run.
- **Coverage is Bash and subagents.** File edits through the Edit and Write tools, and actions in other tools or MCP servers, are not gated by `gate.py`.

If a gate matters to you, also turn on your own permission settings and branch protection. Use hooks as the second line, not the first.
