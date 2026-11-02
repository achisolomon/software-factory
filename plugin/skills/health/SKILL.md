---
name: health
description: Read-only health check of a Software Factory project. Flags stale in-flight dispatches, dead background processes, worktrees with uncommitted or unpushed work, board drift and errors in logs. Use when the user asks for a factory health check, or before a long run or a cleanup.
---

# Factory health check

Read-only: never commit, stash, push, remove a worktree, kill a process or edit `status.md` here. Report, then let the Team Lead or the user act.

Read `docs/factory/status.md` and `docs/architecture/project-facts.md`. If `status.md` is missing, the project is not initialized: say so and stop.

Check, and give each a status `ok`, `warn` or `fail`:

1. **In flight.** Every `## In flight` row whose `Expect back` time has passed with no report on disk is `warn` (`fail` if over twice the expected time). A row with Agent ID `pending` after its dispatch returned is `warn`.
2. **Background processes.** For each `## Background processes` row, check its ports with `nc -z` on 127.0.0.1 and ::1 or its shell id with the task output tool (`ps` is blocked in the Claude Code sandbox). A row whose process is gone is `warn`.
3. **Worktrees.** `git worktree list`, then for each worktree `git -C <path> status --porcelain` and `git -C <path> log --oneline @{upstream}..` (or against the base branch when there is no upstream). Uncommitted or unpushed work is `warn`; a worktree whose folder is missing (`prunable`) is `fail`, because its uncommitted work is lost. Name the branch and the count of files or commits.
4. **Board.** With `Tracking: github`, `gh project item-list` and `gh issue list`: a task `In Progress` on the board with no `## In flight` row, or a row with no matching board item, is `warn`. Items in `Blocked` with no open question in `status.md` are `warn`.
5. **Logs.** Scan the logs the project names in `project-facts.md` (local CI, dev server, emulators) from this session for `error`, `exception`, `fail` and stack traces (contract rule 9.13). Each distinct error is `warn` until it has an issue or a fix.
6. **Version.** Name the running Software Factory version and say if a newer one is installed (the session-start message has it).

Reply with one table, worst first, every item a link where one exists (contract rule 9.14):

| Check | Status | Finding | Suggested action |
|---|---|---|---|

End with one line: `Health: ok` when every row is `ok`, else the count of `fail` and `warn` rows. Suggested actions that change anything (remove a worktree, stop a process, close an issue) wait for the user.
