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
status: todo
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
| Status | todo |

## Description

Write docs/harness/history/<ticket>/kpi.json at verify-delivery with cycle time total and per stage, first-pass CI result, RED-before-GREEN compliance, tests added, coverage delta, review findings by severity with fixed and waived counts, rework count, tokens and cost (from session logs where available, else from a --cost note), and escaped defects linked later by fix tickets. Add harness report --week and --sprint <n> that aggregate into docs/harness/reports/ as Markdown plus JSON, with the targets from docs/harness/workflow.md shown against actuals. The decision that matters: KPIs are derived from journal records that already exist, never typed in by hand, except cost where no log is available.

## Acceptance criteria

- [ ] verify-delivery writes kpi.json with every field listed in the description populated from the journal
- [ ] harness report --week writes docs/harness/reports/<year>-W<week>.md and .json covering every ticket delivered that week, with median cycle time, first-pass CI rate, rework per ticket, findings by severity and points delivered
- [ ] harness report --sprint 0 shows planned versus delivered build points and the eval pass rate for gate-action tickets
- [ ] A fix ticket that names an earlier ticket in its frontmatter increments escaped defects on that ticket in the next report
- [ ] The report contains no secret, token or environment value, checked by the same test as the journal

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
