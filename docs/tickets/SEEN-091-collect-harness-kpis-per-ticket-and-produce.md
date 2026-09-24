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
status: done
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
| Status | done |

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

- [x] verify-delivery writes kpi.json carrying cycle time total and per stage, first-pass CI, RED-before-GREEN compliance, tests added, coverage delta, findings by severity with fixed and waived counts, rework, cost and escaped defects
- [x] harness report --week writes the Markdown and the JSON for every ticket delivered that week, with median cycle time, first-pass CI rate, rework per ticket, findings by severity and points delivered
- [x] harness report --sprint 0 shows planned against delivered build points, and reports the eval pass rate as not yet measurable
- [x] A fix ticket naming an earlier ticket in its frontmatter increments escaped defects on that ticket in the next report
- [x] No report can contain a secret, token or environment value, by the same rule as the journal

## Outcome

Delivered on 24 September 2026. Two slices, each with a red that failed for the reason the solution
record predicted.

**The first report covers what already happened.** Eight tickets had delivered before this one
existed, none with a `kpi.json`, and SEEN-086 has no journal at all. A report reading only `kpi.json`
files would have produced an empty first output while eight delivered tickets sat in the tree. So the
journal is the source and `kpi.json` is a cache: a ticket delivered before this ticket is covered
identically to one delivered after it, and SEEN-086 is listed with its points and a note rather than
dropped. That gap is what the clarify gate refused three times until it was found.

**Running it found two defects in itself.** SEEN-090 reported thirty findings, because four review
records each listed the same nine; a finding is now counted once, by id, most recent record winning.
And rework read `1.1428571428571428`, which is now two decimals.

**Cost is real.** Claude Code keeps one JSONL per session carrying token counts and timestamps, so a
ticket's tokens are the entries inside its window. Only those four numbers are read: a session log
holds prompts and file contents, none of which belongs in a journal. Euros are not computed, because
a price per token is stale the day it is written.

**First-pass CI needed something the journal lacked**, so `verify-delivery` now records the checks it
already fetches. It reads null for everything delivered before this ticket, and the report's last
section names that alongside the eval pass rate and euros, because a report that omits what it cannot
measure reads as though everything were measured.

**Reports and `kpi.json` sit outside the reviewed-tree fingerprint**, beside the journal, the drafts,
the graph and the coverage baseline. Counting them would let a report refuse a delivery: the same
circularity ADR 0002 resolves, which the coverage baseline reintroduced once already.

**And the merge check refused this ticket's own merge**, for regenerating the report so the week
included the ticket that had just delivered. Reports now sit beside the journal, the coverage baseline
and the graph as things delivery writes; anything else after a receipt is still refused. The receipt
was voided and written again rather than the check overridden.

**And the append-only proof could not tell a record from a cache.** `kpi.json` is rewritten whenever a
ticket delivers again, which is what a reopen leads to, so `doctor` reported a rewritten record and CI
refused this delivery. Any reopened ticket could never have delivered, which would have made SEEN-093's
reopen unusable. The proof now covers the numbered records; the cache and the attachments beside them
are not records.

### What the first report says

27 points delivered across eight tickets, median cycle time 18 minutes, rework 1.14 per ticket
against a target of 0.5, and 45 review findings by severity: 5 blocking, 18 high, 23 medium, 17 low,
all fixed, none waived. Sprint 0 stands at 27 of 77 planned points.

The rework figure is the honest headline: three tickets took four attempts each, and every return was
the harness refusing something it should have refused.

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts
- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness

## Blocks

- [SEEN-099](SEEN-099-set-the-context-budget-and-measure-the-tools.md): Set the context budget and measure what the tools changed
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers
- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
