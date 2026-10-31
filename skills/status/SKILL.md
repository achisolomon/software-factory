---
name: status
description: Show the Software Factory Team table now - who is running, blocked, done since the last status, and what is next. Read-only. Use when the user asks for the status, the team table, or what the team is doing.
---

# Status now

Read-only: no new dispatches, no edits to `status.md`, no commits. Report only.

If this session is not yet the Team Lead, read `${CLAUDE_PLUGIN_ROOT}/agents/team-lead.md` (in Codex: `../factory-protocol/references/role-playbook.md`, resolved relative to this skill's `SKILL.md`) for the Team table rules. Then read `docs/factory/status.md`. If it is missing, the project is not initialized: say so and stop.

Reply with the Team table exactly as the Team Lead instructions ("Team table") define it: every agent in `## In flight` with its real Agent ID and model, the `done` rows since the last status, the next `to do` rows, and the Background processes table. Take Workflow agents from the workflow's run folder, not from your own tool results. End with one line naming anything that waits on the user.
