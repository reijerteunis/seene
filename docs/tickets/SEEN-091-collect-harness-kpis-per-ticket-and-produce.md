---
id: SEEN-091
title: "Collect harness KPIs per ticket and produce weekly and sprint reports"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086, SEEN-089]
status: doing
---
# SEEN-091: Collect harness KPIs per ticket and produce weekly and sprint reports

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

Derive a KPI record from each ticket's journal at delivery, and aggregate those records into weekly
and sprint reports. Every number comes from records that already exist: cycle time from the start
record to the receipt and per stage from the records that enter and leave it, first-pass CI from the
checks on the first commit pushed, RED-before-GREEN from the cited slices, findings by severity from
the review record, rework from the return and reopen records, and coverage from the measurement the
tdd gate already requires.

The decision that matters: nothing is typed in by hand. Cost is the one exception, because no session
log is available to read; where none exists the KPI records it as `null` rather than zero, since zero
is a claim and null is the truth.

`harness report --week` writes `docs/harness/reports/<year>-W<week>.md` and its JSON beside it,
covering every ticket delivered in that ISO week by the receipt's timestamp in UTC, with median cycle
time, first-pass CI rate, rework per ticket, findings by severity and points delivered.
`harness report --sprint <n>` compares planned points, from the estimates in the frontmatter of every
ticket carrying that sprint, against delivered points from the receipts.

The eval pass rate for policy-gate action tickets is reported as not yet measurable rather than as
zero: the eval set belongs to SEEN-036 and no policy-gate action ticket has been worked, so a figure
here would be invented.

## Acceptance criteria

- [ ] verify-delivery writes kpi.json carrying cycle time total and per stage, first-pass CI, RED-before-GREEN compliance, tests added, coverage delta, findings by severity with fixed and waived counts, rework, cost and escaped defects
- [ ] harness report --week writes the Markdown and the JSON for every ticket delivered that week, with median cycle time, first-pass CI rate, rework per ticket, findings by severity and points delivered
- [ ] harness report --sprint 0 shows planned against delivered build points, and reports the eval pass rate as not yet measurable
- [ ] A fix ticket naming an earlier ticket in its frontmatter increments escaped defects on that ticket in the next report
- [ ] No report can contain a secret, token or environment value, by the same rule as the journal

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness

## Blocks

- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
