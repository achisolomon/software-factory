# Contributing to Software Factory

Thanks for helping build the best software factory together. Every lesson from your own projects can make the factory better for everyone.

## Ways to help

- **Use it and report what happened.** A review the agents missed, a gate that was too loose or too strict, a step that wasted time or tokens: [open an issue](https://github.com/achisolomon/software-factory/issues/new) with what you asked, what the team did, and what you expected.
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

## Making a change

1. Fork the repo and create a branch.
2. Make one focused change.
3. Run the tests: `python3 -m unittest discover -s tests`.
4. Try it on a real project: `claude --plugin-dir /path/to/your/fork`.
5. Open a pull request that says what problem you saw, what you changed, and how you checked it.

Small, evidence-backed changes are merged fastest. By contributing you agree your work is released under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0-only).
