# Contributing to Software Factory

Thanks for helping build the best software factory together. Every lesson from your own projects can make the factory better for everyone.

## Ways to help

- **Use it and report what happened.** A review the agents missed, a gate that was too loose or too strict, a step that wasted time or tokens: [open an issue](https://github.com/achisolomon/software-factory/issues/new) with what you asked, what the team did, and what you expected.
- **Pick a starter issue.** Issues labelled [`good first issue`](https://github.com/achisolomon/software-factory/labels/good%20first%20issue) are small and well scoped.
- **Propose an idea.** Check [docs/improvement-backlog.md](docs/improvement-backlog.md) first (it lists what is done, planned and declined), then start a [discussion](https://github.com/achisolomon/software-factory/discussions).

## Where things live

The plugin that users install is the `plugin/` folder. Everything else (docs, evals, tests, images) is for developing it and is not shipped.

| Path | What it is |
|---|---|
| `plugin/agents/` | One prompt file per agent role |
| `plugin/reference/handoff-contract.md` | The shared rules every agent reads first: paths, IDs, severities, Definition of Done |
| `plugin/hooks/` | Code-enforced gates (push, merge, deploy, reply checks) |
| `plugin/skills/` | Slash commands and the "team lead" trigger |
| `evals/` | Behavior evals for the agents themselves (`scripts/behavior-check`) |
| `tests/` | Offline tests for hooks and scripts |

```text
software-factory/
├── .claude-plugin/
│   ├── marketplace.json   points at ./plugin
│   └── plugin.json        version pointer for installs older than 0.8.0
├── plugin/                the installed plugin
│   ├── .claude-plugin/
│   │   ├── plugin.json
│   │   └── icon.png
│   ├── agents/            11 agent definitions
│   ├── hooks/             gate, reply check, model check, after-compact, team-lead trigger
│   ├── reference/
│   │   └── handoff-contract.md
│   ├── scripts/
│   │   └── review-route
│   └── skills/            factory-init, build, team-lead, review, resume, status, health, session-setup, frontend-testing
├── assets/          README and link-preview images
├── evals/           behavior evals
├── scripts/
│   └── behavior-check   runs the evals
├── tests/           offline tests
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

1. Fork the repo and create a branch.
2. Make one focused change.
3. Run the tests: `python3 -m unittest discover -s tests`.
4. Try it on a real project: `claude --plugin-dir /path/to/your/fork/plugin`. Editing a checkout does not update an installed plugin; `--plugin-dir` loads your checkout directly.
5. Open a pull request that says what problem you saw, what you changed, and how you checked it.

**Releasing (maintainers):** bump `version` in `plugin/.claude-plugin/plugin.json` and in the root `.claude-plugin/plugin.json` pointer (a test checks they match), and add a `CHANGELOG.md` entry. Installed copies only pick up a change after the version is bumped and pushed to `main`.

Small, evidence-backed changes are merged fastest. By contributing you agree your work is released under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0-only).
