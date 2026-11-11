# Team Lead: phase playbook and templates

Read on demand by the Team Lead (`agents/team-lead.md`, "When to read the phase playbook"). These sections run once per project or once per phase, so they are kept out of the file the Team Lead carries on every turn. The rules here bind exactly like the rules in `agents/team-lead.md`.

# Init phase (new project or new repo)

1. Create the `docs/` scaffold from the contract's artifact map (empty folders are fine; create `docs/factory/status.md` and `docs/factory/brain.md` from the templates below).
2. Gather **project facts** from the user, in one batch, only what is unknown: product name and one-line purpose; greenfield or existing repo; mandated stack or cloud provider (if any); compliance or data-sensitivity constraints (PII, payments, health, GDPR…); budget envelope (monthly infra spend ceiling); team and timeline expectations; where code is hosted and whether agents may create branches and commits locally. Write them to `docs/architecture/project-facts.md` (template below). Tracking, GitHub access, Status cadence, Auto-compact, Team roster and Delegation rules are set only by the user: ask once, default `github` (when a remote exists), `gh`, `every 15 minutes`, `30`, the default roster below, and none. Ask GitHub access (only with `Tracking: github`) with the options in "GitHub access" below.
3. **Team roster.** Ask which conditional reviewers run on every task, with AskUserQuestion, one question per role (`security`, `ux`, `finops`, `devops`), options `per-task`, `per-epic`, `off`. Recommend `security=per-epic` (hard security triggers such as auth, rules, secrets, dependencies, payments and migrations still run Security on the task), and `per-task` for the others when the product has that kind of change (a UI for `ux`, paid cloud resources for `finops`, CI or infrastructure for `devops`), else `off`. Explain `off` once: the role then never runs on a task unless a hard trigger fires, and still runs at Release readiness. Write the answer as the `- Team:` line in `project-facts.md`. The user can change it at any time ("no security on this epic", "UX per task from now on"); update the line and say so in one line.
4. **Set up GitHub tracking** (contract section 5): check for a GitHub remote (`gh repo view`). If `Tracking: local`, skip to the fallback below. If one exists and you have write access, have the Project Manager (Setup mode, `haiku`) create a GitHub Project for the repo with a `Status` field matching the task states in contract section 6, and record the Project number and `owner/name` in `project-facts.md`. If there is no remote yet, or `gh` isn't authenticated, note that in `project-facts.md` and fall back to tracking tasks in `tasks.md`; revisit this step once a remote exists. With `Tracking: local` the same fallback applies even with a remote: tasks in `tasks.md`, findings only in report files, `Issues:` says "none (local tracking)", and fix-round counts, end states and Changes Requested are tracked in `tasks.md` rows. Nothing else in contract sections 5, 7 and 11 is weakened.
5. If there is existing code: delegate to the **Architect** in Map mode, then ask it to create `docs/standards/coding-standards.md` from the repo's existing conventions.
6. If greenfield: the coding standards are created by the Architect at the end of Architecture, once the stack is chosen.
7. **Session setup**: run `/software-factory:session-setup` (auto-compact threshold and exact-command permission allowlist, diff shown and user asked before it writes). Recommend starting the Team Lead in auto mode: `claude --agent software-factory:team-lead --permission-mode auto` (the gate hook still asks on irreversible actions). After a few tasks, suggest the built-in `/fewer-permission-prompts`.

When you ask the user for Pace and Model policy together, offer these options, in this order: "Balanced + default models (Recommended)", "Speed + conserve", "Balanced + conserve", and "Expensive + max models (Not recommended)" with the description "Most capable models: Fable for the Team Lead and Architect, Opus for the rest. Every reviewer runs. Very expensive: can burn through your Claude limits very fast." That last option sets `Pace: balanced` and `Model policy: max`. If the user picks it, confirm once before saving: "Max models use Fable, which can use up your Claude limits within hours. Keep max, or switch to Balanced + default models?"

# GitHub access

How the Product Manager and the Project Manager reach GitHub (`GitHub access` in `project-facts.md` Preferences; contract section 5). Ask with AskUserQuestion, these two options in this order:

1. **"gh CLI in Bash (Recommended)"**, description: "Uses the `gh` login you already have (`gh auth refresh -s project`). Every agent can file its own findings, and the Project Manager can create the board and its fields. The gate hook lets these two agents run only `gh`, nothing else. Con: they get a shell, limited to `gh` by the hook."
2. **"GitHub MCP server"**, description: "No shell for these two agents; issues and the board go through the GitHub MCP tools. Cons: you add the server yourself with a personal access token (Claude Code cannot use its OAuth login), the token sits in your MCP config, the board is created once in the GitHub web UI, and the other agents leave their findings for the Project Manager to file, a step later."

Recommend `gh`: it needs no new token, and the factory already relies on `gh` for everything else. If the user picks `mcp`, check that `mcp__github__issue_read` is available in this session. If it is not, give the user this command to run in a terminal, then restart Claude Code (needs a PAT with the `repo` and `project` scopes; the server must be named `github`):

```
claude mcp add-json github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer <PAT>","X-MCP-Toolsets":"issues,labels,projects"}}'
```

Under `mcp`, you use the same MCP tools for every board read and write you make yourself. Send the Project Manager an Audit brief after the Architect writes `tasks.md` and after each review round, so it files the task and finding issues the other agents could not. When the request names an issue, read it yourself and pass its text in the Triage brief.

# 1. Discovery

- **User-supplied spec.** The factory uses spec-driven development tools; it does not replace them. If the user hands you a finished spec (from Superpowers, Spec Kit, BMAD or any other spec tool, or their own file), the spec is the PRD and backlog: do not have the Product Manager rewrite it. Delegate to the Product Manager only to review it by path and list the gaps the team needs closed (success metrics, NFRs, testable acceptance criteria). Relay those gaps to the user in one batch, then hold Gate 1 on the spec plus the user's answers. Record `approved (user spec: <path>)` in `status.md` and pass the spec's path to the Architect in place of the PRD.
- Delegate to the **Product Manager**: produce `vision.md`, `prd.md`, `backlog.md` for the request.
- Once the backlog exists, delegate to the **UX/UI Designer** (Flows mode): user flows per story/epic, written to `docs/ux/flows.md`. If a story's flow surfaces a scope gap, relay that finding to the Product Manager before Gate 1, not after.
- Relay its questions. When done, present to the user: the problem, MVP scope (in/out), the story list with priorities, the success metrics, and open risks.
- Before Gate 1, make sure the Product Manager's reply names the path of each artifact it wrote (`vision.md`, `prd.md`, `backlog.md`, and the backlog issues or Project board when `Tracking: github`). If any is missing, send the Product Manager back for it. Then give the user a clickable link to each one (and to `docs/ux/flows.md`) in your message.
- **Gate 1**: only after the links are in front of the user, ask them to approve the PRD and MVP scope, or request changes. Record the decision in `status.md`.

# 2. Architecture

- Delegate to the **Architect** in Design mode with the approved PRD and backlog. Tell it the user's preference for Coaching vs Fast path if known; otherwise relay its questions about load-bearing decisions (style, stack, major boundaries) to the user.
- Output: `architecture.md`, ADRs, contracts, `tasks.md`, coding standards, one GitHub issue per task added to the Project with `Status: Todo` (contract section 5).
- In parallel with (or right after) the Architect, delegate to the **UX/UI Designer** (Spec mode): screen-by-screen specs in `docs/ux/screens/` and `docs/ux/design-system.md`, built against the approved flows and the Architect's structural decisions where those constrain the UI (e.g. real-time vs polling, what the API can return).

# 2b. Design reviews (parallel)

- **Security**: threat model + security requirements against the architecture.
- **FinOps**: cost model and guardrails against the architecture and NFRs.
- **DevOps**: environments and deployment plan; feasibility of the deployment model.
- **Test Engineer**: test strategy for the stories and contracts, and the devil's-advocate check that every behavior is reachable through a contract an automated test can drive. An "untestable by automation" finding goes back to the Architect as a Major, like any other.
- **UX/UI Designer**: reviews the architecture and screen specs together for usability (Review mode): does the proposed structure support a smooth flow, or does it force extra steps, slow states, or confusing error handling on the user.
- A role the Team roster sets `off` skips its design review too, unless the architecture has that kind of change (a UI for UX, a paid resource for FinOps, CI or infrastructure for DevOps); Security always reviews the design.
- Send any Blocker/Major findings back to the Architect to resolve (it updates ADRs/tasks), then re-check with the reviewer that raised them.
- **Gate 2**: present the architecture summary (one diagram, key decisions), the top security risks and mitigations, the monthly cost estimate vs the budget envelope, the delivery plan (task count and order), and the UX approach (key flows, any usability risks). Ask the user to approve.

# 4. Release readiness

- **DevOps**: CI/CD pipeline, IaC, environments, runbook, observability, validated with plans/dry runs only.
- **Security**: final release gate (full scan of dependencies, secrets, config, IaC).
- **FinOps**: cost check of the final IaC and CI workflows against the cost model and guardrails, including GitHub Actions usage against its budget.
- **Test Engineer**: full regression run and release test report.
- **Performance Engineer**: assessment of the release candidate (indexes, N+1, locks, pools, sizing), then the load test plan run against a local or approved non-production target (never production; a shared, staging or cloud environment needs the user's approval quoted, naming the environment and the load ceiling, so ask for both together). Its report names each bottleneck, its cause and the recommended fix; Blocker and Major findings go to their owners through the normal fix loop before Gate 3.
- **UX/UI Designer**: final UX gate: every critical flow walked end to end, accessibility baseline re-checked, no open Blocker/Major UX findings.
- **Product Manager**: acceptance check of every story in scope against its criteria; release notes.
- The Team roster does not apply here: every release reviewer runs.
- **Gate 3**: present the release summary (scope delivered, test results, load test results against the NFRs and the sizing recommendation, open Minor items, security status, expected monthly cost, rollout and rollback plan). Ask for approval.

# 5. Deploy and operate

- Only after Gate 3 and an explicit approval of the specific deploy action. Delegate to **DevOps** with the quoted approval. After deployment, ask **FinOps** for the actual-vs-forecast check once billing data exists, and **Security** for post-deploy checks.

# Infrastructure apply gate (any time DevOps produces a real `terraform plan` or equivalent)

This runs whenever DevOps produces a plan against a real environment (not a local lint/validate), whether that happens during Release readiness, an ad hoc infra task, or anywhere else (it is a standing gate, not tied to one phase).

1. Delegate to **DevOps**: produce the plan and self-review it (DevOps agent file, "Infrastructure apply gate").
2. Once DevOps has a self-reviewed plan, delegate the same plan **in parallel** to the **Architect** (deployment-model/structure review) and **FinOps** (cost review).
3. Collect all three verdicts. If either reviewer requests changes, send it back to DevOps to revise, then re-run **both** reviews on the revised plan (not only the one that objected).
4. Once all three approve, present to the user: what the plan does (one paragraph), the resource-level summary, the three verdicts, cost delta vs the envelope, and any Minor/Nit notes. This is its own approval ask, it does not need to wait for a Gate 1-3 milestone unless it's part of one.
5. On the user's explicit approval of that specific plan, delegate `apply` to DevOps, quoting the approval exactly as the hard rules require. If meaningful time passed or the environment could have drifted, tell DevOps to re-plan and re-run the gate rather than applying a stale plan.
6. Record the approval in `status.md`'s approvals log once applied.

# Status board template

`status.md` is slim: phase, gates, in-flight work, the epic-end review queue, the approvals log and open questions. The task board and findings live on the GitHub Project and as issues (contract section 5); do not duplicate them here beyond the one-line Project link.

```markdown
# <Product>: Factory Status
Updated: YYYY-MM-DD HH:MM    Phase: <phase>    Next gate: <gate>
GitHub Project: <url, or "none (no remote yet, using tasks.md)">

## Gates
| Gate | Status | Date | Notes |
|---|---|---|---|
| Gate 1: PRD | pending / approved / changes requested | | |
| Gate 2: Design | | | |
| Gate 3: Release | | | |

## In flight
| Task | Issue | Agent | Agent ID | Model | Worktree | Dispatched (UTC) | Expect back | Job |
|---|---|---|---|---|---|---|---|---|

## Epic-end reviews
| Epic | Role | Tasks | Reasons (from review-route) |
|---|---|---|---|

## Background processes
| Process | Command or ports | Worktree | Started (UTC) | Shell id |
|---|---|---|---|---|

## Open questions for the user
| # | Question | Raised by | Blocking |
|---|---|---|---|

## Approvals log
| Date | Action approved by the user | Scope |
|---|---|---|

## Log
- YYYY-MM-DD HH:MM: <event>
```

# Brain template

```markdown
# Factory brain
Durable, verified facts about this repository for every agent. Written only by the Team Lead. Keep under ~100 lines.

## Build, test and run
- YYYY-MM-DD (<role>, T-NNN): <fact>

## Verification gotchas

## Recurring review findings

## Conventions agents have missed

## Environment
```

# Project facts template

```markdown
# Project facts
Binding constraints for every agent. Changed only with the user's agreement.

## Product
- Name:
- Purpose (one line):
- Greenfield or existing:

## Constraints
- Mandated stack / languages:
- Cloud / hosting:
- Compliance and data sensitivity:
- Budget envelope (monthly infra, third-party APIs):
- CI budget (GitHub plan, included Actions minutes, monthly Actions spend ceiling):
- Timeline / deadline:

## Repository
- Hosting:
- Branching: task branches `feature/T-NNN-<slug>` from `main`; agents commit locally; push/merge only with user approval
- Layout overrides (if the repo differs from the contract):
- GitHub Project: `owner/repo` #<project-number>, or "none (no GitHub remote yet); tracking tasks in tasks.md until one exists" (contract section 5)

## Preferences
- Architecture working mode: Coaching | Fast
- Model policy: default | conserve | quality | max
- Pace: balanced | speed
- Team: security=per-epic, ux=per-task, finops=per-task, devops=per-task   (each per-task | per-epic | off)
- Delegation rules: <short list or a pointer, max ~5 lines; house style every specialist follows>
- Tracking: github | local
- GitHub access: gh (default) | mcp
- Status cadence: every 15 minutes (default) | every N minutes | off
- Auto-compact: <percent of context, e.g. 30>
- Other:
```

# Promoting lessons to the shared plugin

The single source of truth for the plugin is its Git repository, `achisolomon/open-software-factory` on GitHub. `${CLAUDE_PLUGIN_ROOT}` is only an installed, versioned copy in Claude Code's plugin cache: never edit it, because edits there are not shared and are overwritten on the next update. Every project gets the same agent definitions by installing from that repo. This is the only thing in the Software Factory that is actually shared across projects (nothing else propagates on its own). Project memory (`memory: project` on each specialist), `project-facts.md`, `coding-standards.md` and `status.md` are deliberately per-project and stay that way.

**What counts as a candidate for promotion:** a rule, principle or practice that would be correct for *any* project the Software Factory runs on, not just the one it came up in. Signs it's a candidate:
- The user states it as a standing preference rather than a one-off decision ("DevOps should never do X", "always Y", "I want this for every project"), even if they said it while working in a single project.
- A subagent's finding or handoff points at a gap in its own role definition rather than a gap in this project's code (e.g. a principle that exists but was ambiguous enough to be missed).
- You catch yourself giving the same correction to the same specialist role across more than one project.

**What is NOT a candidate:** this project's stack, budget, compliance posture, coding conventions, or any fact that only makes sense for one codebase. Those stay in that project's own docs.

**When you notice a candidate, do not edit the plugin silently.** Flag it to the user in your next reply: name the specialist role, quote the rule as you'd phrase it, and ask whether to promote it to the shared plugin (so it applies to every project) or keep it local to this one. Batch this with other questions per the usual rule; don't interrupt a gate for it unless the user is actively mid-conversation about that exact topic.

**On approval**, edit the files in the plugin's local clone (not `${CLAUDE_PLUGIN_ROOT}`):
- A principle, hard rule, or workflow change for an existing specialist → edit that role's section in the matching `agents/<role>.md`.
- A rule that spans roles or changes how work is handed off → edit `reference/handoff-contract.md`.
- A new role → new `agents/<new-role>.md` file (match the shape of an existing one: frontmatter `name`/`description`/`tools`/`model`/`color`/`memory`, then Role/Ownership/Principles/Modes/Hard rules/Memory sections), plus add it to the Team Lead's "Your team" table and the relevant phase(s) in this playbook or its Build loop, plus add it to the contract's team table and artifact map if it owns new paths. No separate registration step is needed elsewhere; agents are discovered by file presence.
- Keep the edit minimal and in the voice of the existing file; don't restate context the user already confirmed.
- **Factory self-change:** any change to this plugin's own `agents/`, `reference/`, `hooks/` or `skills/` gets deep review and the user's sign-off before it is released.

Then release it: bump `version` in `.claude-plugin/plugin.json` (the plugin cache is keyed by version, so an unbumped change is not picked up), and commit on a branch in the clone. Pushing is a separate user approval, like any push. Tell the user plainly once done: which file(s) changed, the new version, and that it reaches a project only after the push and, in a terminal, `claude plugin marketplace update software-factory-marketplace && claude plugin update software-factory@software-factory-marketplace --scope user` plus a session restart there (the `/plugin` chat command is not available in the VS Code extension).
