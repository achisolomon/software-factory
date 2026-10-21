# Codex Model Routing

This repository supports two runtimes. The `model:` value in an agent's frontmatter is a Claude Code setting and must remain a Claude model name. Codex model selection is performed by `scripts/run-codex-agent`, which passes an explicit model to the Codex CLI.

## Current cost-effective policy

The runner was verified against the local Codex model catalog on 2026-10-21. The account has `gpt-6-luna` and `gpt-5.6-terra` available; it does not currently expose Sol or Astra. Terra is the balanced model for complex work and Luna is the low-cost model for focused, repeatable work.

| Role | Default model | Use Terra instead when |
|---|---|---|
| Team Lead | `gpt-5.6-terra` | — |
| Triage Classifier | `gpt-6-luna` | Inspecting unfamiliar repository context |
| Product Manager | `gpt-5.6-terra` | — |
| Software Architect | `gpt-5.6-terra` | — |
| Software Developer | `gpt-5.6-terra` | — |
| Test Automation Engineer | `gpt-6-luna` | Writing a strategy, diagnosing a non-obvious failure, or designing a test framework |
| DevOps Engineer | `gpt-5.6-terra` | — |
| FinOps Engineer | `gpt-5.6-terra` | — |
| Security Engineer | `gpt-5.6-terra` | — |
| UX/UI Designer | `gpt-6-luna` | Designing a substantial new flow or resolving an accessibility issue |

`--mode routine` uses Luna for a focused, repeatable Triage, Test Automation, or UX/UI task only. `--mode quality` uses Terra. A lower-cost model for another role requires an explicit `--model` choice. Do not change a lifecycle path, required review, or approval gate to save model usage.

## Running the factory

Run the script from the target project's root; it uses the current directory as the target workspace. Use `--project-dir <path>` when launching it elsewhere. `scripts/run-codex-agent team-lead -- <task>` starts an interactive Codex session, so the Team Lead can ask questions and stop at approval gates. Its target must already be a Git repository (`git init` is sufficient for a new project), because the interactive Codex CLI does not offer a no-Git override. The Team Lead launches a specialist with the factory-runner path supplied in its delegation and passes it a complete delegation; it reads the specialist's response and verifies its required artifacts before continuing. All other roles run through non-interactive `codex exec` and support non-Git targets.

## Escalation

Pass `--model <model-id>` only after a lower-cost pass has produced concrete evidence that it is insufficient: unresolved competing designs, an unrepeatable failure, missing evidence for a security finding, or a high-risk architecture decision. If the account later exposes `gpt-6.1-sol` or `gpt-6-astra`, use Sol before Astra; reserve Astra for new-system architecture and high-risk security or production-infrastructure decisions.

Before changing this policy, run representative tasks with both choices and compare task success, token usage, latency, and cost per successful task. Check the account's current choices with `codex debug models` rather than assuming a model is available.
