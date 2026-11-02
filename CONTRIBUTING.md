# Contributing to Software Factory

Thanks for helping build the best software factory together. Every lesson from your own projects can make the factory better for everyone.

## Ways to help

- **Use it and report what happened.** A review the agents missed, a gate that was too loose or too strict, a step that wasted time or tokens: [open an issue](https://github.com/achisolomon/software-factory/issues/new/choose) with the bug form. It asks for four things: what you asked, what the team did, what you expected, and your plugin version.
- **Report a vulnerability privately.** Do not use a public issue. Follow [SECURITY.md](SECURITY.md).
- **Pick a starter issue.** Issues labelled [`good first issue`](https://github.com/achisolomon/software-factory/labels/good%20first%20issue) are small and well scoped.
- **Propose an idea.** Check [docs/improvement-backlog.md](docs/improvement-backlog.md) first (it lists what is done, planned and declined), then start a [discussion](https://github.com/achisolomon/software-factory/discussions).

## Where things live

| Path | What it is |
|---|---|
| `agents/` | One prompt file per agent role |
| `reference/handoff-contract.md` | The shared rules every agent reads first: paths, IDs, severities, Definition of Done |
| `hooks/` | Code-enforced gates (push, merge, deploy, reply checks) |
| `skills/` | Slash commands and the "team lead" trigger |
| `evals/` | Behavior evals for the agents themselves |
| `tests/` | Offline tests for hooks and scripts |
| `.github/` | Repo automation: `CODEOWNERS`, the pull request template, `ISSUE_TEMPLATE/` forms, and `workflows/` (CI) |

See [docs/TRUST.md](docs/TRUST.md) for what the plugin's hooks do and do not do.

```text
software-factory/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── agents/          11 agent definitions
├── hooks/           gate, reply check, model check, after-compact, team-lead trigger
├── assets/          README and link-preview images
├── scripts/
│   └── review-route
├── skills/          factory-init, build, team-lead, review, resume, status, health, session-setup, frontend-testing
├── reference/
│   └── handoff-contract.md
├── docs/
│   ├── TRUST.md                 what code enforces and what relies on prompts
│   ├── provenance.md            outside sources we adapted
│   └── improvement-backlog.md   ideas from similar projects: done, planned, declined
├── CHANGELOG.md     release notes
├── CONTRIBUTING.md  how to contribute
├── LICENSE          AGPL-3.0
└── README.md
```

## Making a change

Python 3.9 or newer is supported. CI runs the step 3 command on Python 3.9 and 3.13.

1. Fork the repo and create a branch.
2. Make one focused change.
3. Run the tests: `python3 -m unittest discover -s tests`.
4. Try it on a real project: `claude --plugin-dir /path/to/your/fork`. Editing a checkout does not update an installed plugin; `--plugin-dir` loads your checkout directly.
5. Open a pull request that says what problem you saw, what you changed, and how you checked it. The [pull request template](.github/pull_request_template.md) has a section for each.

Small, evidence-backed changes are merged fastest. By contributing you agree your work is released under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0-only).

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Maintainer notes

Plugin files run on users' machines, so treat every pull request as untrusted code.

- Run `gh pr diff <n>` and read it before anything else.
- Never run `claude --plugin-dir` on a fork until you have read its hooks and prompts. Hooks run code on your machine.
- Do runtime tests in a throwaway VM or container that holds no credentials: no mounted home directory, no `gh` or `git` auth, no API keys or tokens.
- Read the full diff, line by line, for any change under `hooks/`, `agents/`, `skills/`, `reference/`, `scripts/`, `.claude-plugin/`, `.claude/`, or `.github/`. These ship to every user on merge.
- Review Dependabot pull requests as code, not as routine bumps.

## Releasing

Installed copies only pick up a change after the version is bumped and pushed to `main`.

1. Bump `version` in `.claude-plugin/plugin.json`.
2. Add a matching section at the top of `CHANGELOG.md`. `tests/test_release_consistency.py` fails if the two differ.
3. Merge through a pull request once CI is green.
4. Create an annotated tag on the merge commit: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
5. Publish the release: `gh release create vX.Y.Z --notes-file <file with the CHANGELOG section>`.

Pushing a tag needs the owner's explicit approval.
