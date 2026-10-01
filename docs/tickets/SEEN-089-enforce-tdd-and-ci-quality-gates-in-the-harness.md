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
status: done
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
| Status | done |

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

- [x] harness check --phase red on a command that exits 0 appends the record and then refuses, naming that the RED did not fail
- [x] A red that timed out or could not start is refused as RED evidence for the same reason
- [x] advance from tdd is refused when a slice cites a red that passed, naming the slice
- [x] advance from tdd is refused without a coverage measurement for the attempt, and when the delta on packages/core is negative; a first measurement with no baseline records a null delta and passes
- [x] A blocking decision that did not clear its threshold is refused with a message that says it did not clear
- [x] harness return appends a rework record and status shows the ticket back at the target stage

## Outcome

Delivered on 23 September 2026. Three slices, each with a red that failed for the reason the solution
record predicted.

**A RED that did not fail is refused**, and the run is still recorded: the fact happened, the claim is
what gets rejected. Exit zero contradicts it; a timeout or a command that could not start cannot
support it. The tdd gate holds cited reds to the same rule, so evidence recorded before this commit
cannot be laundered through it.

**Coverage on `packages/core` is measured by one fixed command** and compared with the last delivered
figure, which only a delivery moves. A first measurement has no baseline and is not a regression.
The real measurement on this tree is 100% of lines, recorded at record 17.

**A refusal now says what happened.** A blocking decision that failed to clear its threshold read as
one that cleared, because the message printed the rule's own word.

**The regression check caught a defect I had just written.** Writing the coverage baseline at delivery
changed the tree the receipt had attested a moment earlier, so the receipt could not survive the
delivery that produced it, which is the circularity ADR 0002 exists to resolve. The baseline is
bookkeeping, and now sits outside the fingerprint beside the journal, the drafts and the graph. The
tdd gate refused the advance until it was fixed.

**This ticket was split and its gate recalibrated, both on evidence.** The original scope covered
seven enforcements and its solution record scored 0.50, 0.51 and 0.49 on `solution_complete`; closing
four genuine gaps moved it by 0.01, while the same question asked about one enforcement scored 0.67.
Delivery and merge verification moved to [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md),
and the threshold moved from 0.8 to 0.6 with the five measurements recorded beside the value. The
final record reached 0.59 and the founder overrode it at 0.85, on the record, at record 9.

## Moved to SEEN-094

The carried-in work from SEEN-087 and SEEN-088, the CI additions and the pull request template all
moved to [SEEN-094](SEEN-094-verify-delivery-against-ci-and-the-merge.md).

## Depends on

- [SEEN-006](SEEN-006-scaffold-the-pnpm-turborepo-monorepo-with-all.md): Scaffold the pnpm turborepo monorepo with all six packages
- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers
- [SEEN-116](SEEN-116-property-based-and-mutation-tests-on-the-money.md): Property-based and mutation tests on the money core, as a gate
- [SEEN-136](SEEN-136-no-test-touches-the-clock-the-network-or.md): No test touches the clock, the network or randomness unfaked, and a flaky test is a defect

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
