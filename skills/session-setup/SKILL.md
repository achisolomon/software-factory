---
name: session-setup
description: Configure the project's Claude Code settings for Software Factory runs. Sets the auto-compact threshold and an allowlist of exact read-only and stack commands, after showing the diff and asking. Claude Code only.
argument-hint: "[auto-compact percent]"
disable-model-invocation: true
---

# Session setup (Claude Code only)

Act as the Team Lead. In Codex this skill is not applicable: say so and stop.

Goal: fewer permission prompts and a safe auto-compact threshold, written to the PROJECT's `.claude/settings.json`. Merge into the existing file and keep every existing key. Show the diff and ask the user before writing. Never touch user-level settings.

1. **Auto-compact.** Set `env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` to the user's choice (the argument, or the `Auto-compact` preference in `docs/architecture/project-facts.md`), default `"30"`. It is a percent of the auto-compact window (range 1-100), it can only lower the threshold, it applies to the main session and subagents, and the session continues after compaction. Write it to the `.claude/settings.json` of the folder the user starts Claude Code from: when that is a parent of the project (a multi-repo workspace), the project's own settings file is not loaded. It takes effect in sessions started after the change.
2. **Exact-command allowlist** in `permissions.allow`, built from the stack's exact commands: test, lint, typecheck, build, format-check. Detect them from `package.json` scripts (use the runner the lockfile implies), `pyproject.toml`, `go.mod`, `Cargo.toml`, the Gradle wrapper and Makefile targets. Add:
   - read-only git: `git status`, `git diff:*`, `git log:*`, `git show:*`, `git worktree list`
   - read-only gh: `gh issue list:*`, `gh issue view:*`, `gh pr view:*`, `gh project item-list:*`
   - the contract section 5 issue writes, only when `Tracking: github`: `gh issue create:*`, `gh issue comment:*`, `gh issue edit:*`, `gh project item-add:*`, `gh project item-edit:*`
3. **Never allow** wildcards over script runners (`npm run:*`, `python:*`, `bash:*`) and never any command the gate hook asks on (push, deploy, apply, publish, recursive force delete, and so on).
4. Project `env` and `allow` take effect after the user trusts the folder.
5. **Tell the user:**
   - Start the Team Lead in auto mode: `claude --agent software-factory:team-lead --permission-mode auto`. (`defaultMode: auto` only works in user settings.) Auto mode drops broad allow rules, and the gate hook's ask still prompts.
   - After a few tasks, run the built-in `/fewer-permission-prompts` to harvest more exact read-only rules.
6. Record the chosen `Auto-compact` value in `project-facts.md` Preferences if it is not there.
