---
id: SEEN-089
title: "Enforce TDD and CI quality gates in the harness"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-006, SEEN-086]
status: todo
---
# SEEN-089: Enforce TDD and CI quality gates in the harness

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Make harness check record command, exit code, duration and output hash per phase (red, green, regression, qa), accept a RED only when the named test fails, and refuse advance from tdd without at least one RED and one GREEN per slice, a non-negative coverage delta on packages/core, and green typecheck, lint and build. Extend ci.yml with coverage reporting, gitleaks, pnpm audit --audit-level high, graphify extract and the harness tests, and add the pull request template that carries acceptance criteria, RED and GREEN evidence, review findings and the receipt hash. Add harness return so review findings route the ticket back to tdd or solution and count as rework. The decision that matters: CI green on the delivered SHA is the only definition of done; the harness verifies it, never asserts it.

## Acceptance criteria

- [ ] harness check --phase red on a passing test is rejected with a message that the RED did not fail
- [ ] advance from tdd is refused without a RED and a GREEN per slice and with a negative coverage delta on packages/core, and the refusal names the missing evidence
- [ ] ci.yml runs typecheck, migrations twice, tests with coverage, build, gitleaks, pnpm audit at high, graphify extract and the harness tests, and a seeded secret in a test branch fails the pipeline
- [ ] The PR template is applied automatically and verify-delivery refuses a PR body without the receipt hash
- [ ] harness return SEEN-089 --to tdd appends a rework record and status shows the ticket back in tdd

## Carried in from SEEN-087

SEEN-087 wrote its delivery receipt while a CI job was red, because SEEN-086's verify-delivery is
offline by design. Add both halves here: verify-delivery refuses while any check on the delivered
SHA is not green, and the merge check compares the receipt's commit to the branch tip, so a fix
pushed after a receipt cannot be merged under a receipt that attests the commit before it.

## Depends on

- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages
- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
