---
id: SEEN-123
title: "Cap harness work at ten percent of a sprint and make every harness ticket state its payback"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-091]
status: todo
priority: P2
---
# SEEN-123: Cap harness work at ten percent of a sprint and make every harness ticket state its payback

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P2 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Twenty-eight harness tickets delivered before the second product ticket opened. The harness is good and it is also the easiest thing in this repository to keep improving, because every session that works on it is working on its own tools. Put a rule where a mood was: harness tickets (epic E10) may take at most ten percent of a sprint's build points once Sprint 0 closes; a harness ticket's clarify record must state its payback (which KPI moves, by how much, measured how) and the weekly report checks the claim against the measurement two sprints later; doctor warns when the share is exceeded. The decision that matters: the harness exists to ship Seen, and the POC gate is 30 November.

## Acceptance criteria

- [ ] thresholds.toml carries the harness share cap and the clarify template a payback field required for E10 tickets
- [ ] The weekly report shows the E10 share of delivered points and the payback claims against their later measurement
- [ ] doctor warns when the E10 share of an open sprint exceeds the cap
- [ ] The rule is written in docs/harness/workflow.md and CLAUDE.md

## Depends on

- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
