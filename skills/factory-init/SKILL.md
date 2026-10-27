---
name: factory-init
description: Set up the current repository for the Software Factory agent team — create the docs/ scaffold, capture project facts, and (for existing code) map the repo and derive coding standards. Run once per project.
argument-hint: "[one-line product description]"
disable-model-invocation: true
---

# Initialize this project for the Software Factory

Act as the Team Lead. Read and follow the Team Lead agent (especially "Init phase", the status board template and the project facts template) and the handoff contract (the artifact map): in Claude Code these are `${CLAUDE_PLUGIN_ROOT}/agents/team-lead.md` and `${CLAUDE_PLUGIN_ROOT}/reference/handoff-contract.md`; in Codex, read `../factory-protocol/references/role-playbook.md`, resolved relative to this skill's `SKILL.md`.

Use the product description in the user's request that invoked this skill; it may be empty.

Steps:

1. If `docs/factory/status.md` already exists, the project is initialized: summarize its state and stop, unless the user asks to re-initialize.
2. Detect whether this is an existing codebase (source files, manifests, git history) or greenfield.
3. Create the folders of the contract's artifact map under `docs/`, `docs/factory/status.md` from the template (Phase: Init), and `docs/factory/brain.md` from the factory brain template (empty sections).
4. Ask the user — in one batch, with AskUserQuestion where options fit, and only for what you cannot detect — for the project facts. Write `docs/architecture/project-facts.md`.
5. Existing codebase: delegate to the Software Architect in Map mode, then ask it to create `docs/standards/coding-standards.md` from the repo's existing conventions. In Claude Code use `software-factory:software-architect`; in Codex use native delegation with the Software Architect procedure in `../factory-protocol/references/role-playbook.md`. Greenfield: note in `status.md` that standards come after the architecture.
6. Claude Code only (Codex: not applicable): run the `session-setup` skill (`/software-factory:session-setup`) to set the auto-compact threshold and an exact-command permission allowlist. It shows the diff and asks before writing.
7. If the repo is a git repository, suggest (do not run) adding the factory folders to version control.
8. Finish with: what was created, the project facts captured, and the next step: invoke the `build` skill with what to build (in Claude Code, `/software-factory:build <what to build>`).
