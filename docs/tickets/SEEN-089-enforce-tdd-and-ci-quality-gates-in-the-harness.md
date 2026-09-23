---
id: SEEN-089
title: "Enforce the TDD gates in the harness"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-006, SEEN-086]
status: doing
---
# SEEN-089: Enforce the TDD gates in the harness

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Make the harness enforce what it currently only records. `harness check --phase red` accepts a RED
only when the command actually failed as a test: an exit code of zero is not evidence, and neither is
a timeout nor a command that could not start, because neither says anything about the behaviour under
test. The record is appended either way, because the run happened; the claim is what gets refused.
`advance` from tdd then requires every cited red to demonstrate a failure, and requires a coverage
measurement for the attempt whose delta on `packages/core` is not negative. A blocking decision that
did not clear its threshold says so, rather than printing the rule's own word and claiming the
opposite.

Delivery and merge verification were split out into SEEN-094 on 23 September 2026: one solution
record covering seven enforcements could not be judged complete, and the same question scored 0.49 on
all seven and 0.67 on one.

## Acceptance criteria

- [ ] harness check --phase red on a command that exits 0 appends the record and then refuses, naming that the RED did not fail
- [ ] A red that timed out or could not start is refused as RED evidence for the same reason
- [ ] advance from tdd is refused when a slice cites a red that passed, naming the slice
- [ ] advance from tdd is refused without a coverage measurement for the attempt, and when the delta on packages/core is negative; a first measurement with no baseline records a null delta and passes
- [ ] A blocking decision that did not clear its threshold is refused with a message that says it did not clear
- [ ] harness return appends a rework record and status shows the ticket back at the target stage

## Moved to SEEN-094

The carried-in work from SEEN-087 and SEEN-088, the CI additions and the pull request template all
moved to [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md).

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
