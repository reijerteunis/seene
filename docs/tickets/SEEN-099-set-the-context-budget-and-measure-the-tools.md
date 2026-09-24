---
id: SEEN-099
title: "Set the context budget and measure what the tools changed"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-096, SEEN-098, SEEN-091]
status: doing
---
# SEEN-099: Set the context budget and measure what the tools changed

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Write the context budget into `harness/thresholds.toml` and name in `docs/harness/skill.md` which tool
answers at which stage: codegraph while writing code, repowise at clarify, solution and review,
graphify for the map across code and documents. The budget is three rules: one tool call per question,
`codegraph_explore` queries name a symbol rather than a directory, and no repository-wide read when a
graph can answer. They exist because three MCP servers put three sets of tool schemas into every
session before a ticket is read.

Then measure. After five delivered tickets with the tools, compare output tokens and tool calls per
point against `docs/harness/reports/context-tools-baseline.json`, captured before any of them existed:
27 points, 40,581 output tokens and 18.5 tool calls per point.

The decision rule is recorded before the measurement, because measuring without one is theatre. Below
the baseline, the tools paid for the context they occupy. Above it, one is removed, graphify first,
because the other two can partly answer its questions. A rise removes them immediately rather than
after five tickets. The figure and the call go in the sprint report, and the call is the founder's.

## Acceptance criteria

- [ ] harness/thresholds.toml carries the three context budget rules
- [ ] docs/harness/skill.md names which tool answers at which stage, and sync regenerates both copies
- [ ] The sprint report shows output tokens and tool calls per point against the baseline
- [ ] The report states the decision the rule points to, and the founder's call beside it
- [ ] A question with two right addressees is reported as one tool too many, which is the test of the design

## Depends on

- [SEEN-096](SEEN-096-add-codegraph-and-route-the-graph-command.md): Add codegraph and route the graph command to it
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate
- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- The baseline captured before any of these tools existed: `docs/harness/reports/context-tools-baseline.json`, ten delivered tickets, 27 points, 40,581 output tokens and 18.5 tool calls per point.
- Split out of SEEN-096 on 24 September 2026: one clarify record covering two tool installations, the routing, the budget rules and a five-ticket measurement scored 0.67, 0.68 and 0.62, while the same question asked about one tool scored 0.81.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
