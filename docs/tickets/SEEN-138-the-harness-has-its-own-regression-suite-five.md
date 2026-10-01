---
id: SEEN-138
title: "The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-091, SEEN-104, SEEN-105]
status: todo
priority: P2
---
# SEEN-138: The harness has its own regression suite: five finished tickets replayed when its rules, hooks or prompts change

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P2 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

Every change to the harness so far was judged by feel: a new rule, a new sentence in the reviewer's task, a threshold moved, and the next ticket felt better or worse. Nothing replays the same work twice, so nobody knows whether a change to the tools that make the code made the code better. Keep five finished tickets as a benchmark, chosen for spread (a connector, a detector, a migration, a web change, a harness change), with their ticket text, handoff packs, RED tests and recorded findings. When a change touches harness/, .claude/, .codex/, the rules or the skill, harness benchmark replays the five in shadow from clarify to review on a throwaway branch with the model and effort pinned, and writes a report against the recorded run: findings by severity, returns, tokens and tool calls per point, tests green, mutation score, and whether the recorded findings were found again. The run is evidence, not a gate on its own: a harness ticket's Outcome must cite the benchmark report before verify-merge accepts it, and a regression above the threshold in thresholds.toml returns the ticket to solution. The cost is real, roughly a day of tokens for five tickets, so the benchmark runs on harness changes only, at most once per harness ticket, its cost counts against the SEEN-123 cap, and a ticket in the suite is replaced when it stops being representative. The decision that matters: the harness is code, and code that changes without a test is the thing this whole epic exists to stop.

## Acceptance criteria

- [ ] docs/harness/benchmark/ carries five finished tickets with their text, handoff packs, RED tests and recorded findings, chosen for spread, each with the reason it was chosen
- [ ] harness benchmark replays the five in shadow on a throwaway branch with model and effort pinned and writes a report comparing findings by severity, returns, tokens and tool calls per point, tests, mutation score and recovered findings against the recorded run
- [ ] A harness ticket (epic E10) does not pass verify-merge without a benchmark report cited in its Outcome, and a regression above the threshold in thresholds.toml returns it to solution, proven with a fixture
- [ ] The benchmark's tokens are recorded in kpi.json under the harness ticket that triggered it and count against the SEEN-123 cap

## Depends on

- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports
- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
