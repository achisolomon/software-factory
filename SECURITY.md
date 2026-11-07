# Security policy

## Supported versions

Only the latest release (and the current `main`) is supported. Update to the latest version before reporting.

## Reporting a vulnerability

Report privately through a GitHub security advisory: https://github.com/achisolomon/software-factory/security/advisories/new

Do not open a public issue or pull request for a vulnerability.

I will reply within 7 days. That is a first reply, not a promise of a fix or a timeline. If the report is valid, the fix is prepared in a private advisory and published through GitHub security advisories, which can also issue a CVE.

## In scope

- A bypass of the hooks in `hooks/` or evasion of the gate (`hooks/gate.py`) that is not already described as a limit in `docs/TRUST.md`.
- Prompt or agent text that makes an agent leak data or run commands you did not approve.
- Anything that lets a pull request or a release change what ships to users without being noticed.

## Out of scope

- Limits already documented in [docs/TRUST.md](docs/TRUST.md), such as "hooks are feedback, not a security boundary", unless you found a new way to evade them.
- Model mistakes that rely only on prompts, which `docs/TRUST.md` lists as not enforced by code.
- Vulnerabilities in Claude Code, GitHub or other third-party tools. Report those to their owners.
