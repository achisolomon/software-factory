---
name: factory-init
description: Set up the current repository for the Software Factory agent team — create the docs/ scaffold, capture project facts, and (for existing code) map the repo and derive coding standards. Run once per project.
argument-hint: "[one-line product description]"
disable-model-invocation: true
---

# Initialize this project for the Software Factory

Act as the Team Lead. Read and follow the Team Lead agent, its phase playbook (especially "Init phase", "GitHub access", the status board template and the project facts template) and the handoff contract (the artifact map): `${CLAUDE_PLUGIN_ROOT}/agents/team-lead.md`, `${CLAUDE_PLUGIN_ROOT}/reference/team-lead-phases.md` and `${CLAUDE_PLUGIN_ROOT}/reference/handoff-contract.md`.

Use the product description in the user's request that invoked this skill; it may be empty.

Steps:

1. If `docs/factory/status.md` already exists, the project is initialized: summarize its state and stop, unless the user asks to re-initialize.
2. Detect whether this is an existing codebase (source files, manifests, git history) or greenfield.
3. Create the folders of the contract's artifact map under `docs/`, `docs/factory/status.md` from the template (Phase: Init), and `docs/factory/brain.md` from the factory brain template (empty sections).
4. Ask the user (in one batch, with AskUserQuestion where options fit, and only for what you cannot detect) for the project facts, including the Team roster (who reviews each task: Security, UX, FinOps, DevOps, each per task, per epic or off). Write `docs/architecture/project-facts.md`.
5. Existing codebase: delegate to the Software Architect in Map mode, then ask it to create `docs/standards/coding-standards.md` from the repo's existing conventions. Use `software-factory:software-architect`. Greenfield: note in `status.md` that standards come after the architecture.
6. Run the `session-setup` skill (`/software-factory:session-setup`) to set the auto-compact threshold and an exact-command permission allowlist. It shows the diff and asks before writing.
7. If the repo is a git repository, suggest (do not run) adding the factory folders to version control.
8. Finish with: what was created, the project facts captured, and the next step: invoke the `build` skill with what to build (in Claude Code, `/software-factory:build <what to build>`).
