---
id: SEEN-120
title: "Affected-only checks and a local CI that finishes in minutes"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-097, SEEN-094]
status: todo
priority: P1
---
# SEEN-120: Affected-only checks and a local CI that finishes in minutes

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

verify-delivery waits for CI on the delivered commit, and CI runs everything on every push. Make the checks proportional to the change: turbo --filter=...[origin/main] for typecheck, lint and test on the packages a change touches, turbo remote cache on the GitHub Actions cache so unchanged packages cost nothing, the docker compose stack from SEEN-097 for the integration job so it runs the same locally, a pre-push hook that runs the affected set before the push, and path filters so a docs-only or harness-only change does not wait on the TypeScript jobs. The decision that matters: a session should never wait more than a few minutes to learn whether it is done, because waiting is where a session starts doing something else.

## Acceptance criteria

- [ ] CI runs typecheck, lint and test only on affected packages, with turbo remote cache hits shown in the job log
- [ ] The integration job runs on the SEEN-097 compose stack in CI and locally with the same command
- [ ] The pre-push hook runs the affected set and refuses a push that fails it
- [ ] A docs-only change runs only the docs and harness jobs, proven by a run log
- [ ] Median CI time on a one-package change is under five minutes, recorded in the sprint report

## Depends on

- [SEEN-097](SEEN-097-set-up-the-local-docker-development-environment.md): Set up the local Docker development environment
- [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md): Verify delivery against CI and verify the merge against the receipt

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
