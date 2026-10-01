---
id: SEEN-119
title: "Independent slices run in parallel worktrees"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-111, SEEN-112]
status: todo
priority: P1
---
# SEEN-119: Independent slices run in parallel worktrees

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

A five-point ticket is three or four slices worked one after another, and the sessions wait for each other for no reason when the slices touch different files. harness route marks the slices whose file sets are disjoint as parallel; the orchestrating session spawns their implementer subagents at once, each in its own git worktree (Claude Code's isolation: worktree; separate threads in Codex), each with its own handoff pack; the harness merges the worktrees in plan order with the sync commit rule and refuses a merge that touches a file another slice claimed. Slices that share a file stay sequential. Wall-clock per ticket joins the KPI record beside cycle time. The decision that matters: parallel is a property of the slice plan, decided at solution where the files are known, never improvised in the session.

## Acceptance criteria

- [ ] harness route marks slices with disjoint files as parallel and refuses to mark two slices that share a file
- [ ] Parallel slices run as concurrent implementer subagents in separate worktrees in Claude Code, and the harness merges them in plan order with the sync commit rule
- [ ] A merge touching a file another slice claimed is refused with both slice names
- [ ] kpi.json carries wall-clock per ticket beside cycle time, and the sprint report shows the saving on parallel tickets
- [ ] The Codex copy of the skill says how the same plan runs as separate threads

## Depends on

- [SEEN-111](SEEN-111-hold-a-slice-to-the-context-it-was-routed-to.md): Hold a slice to the context it was routed to, and price it before it is worked
- [SEEN-112](SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md): Run a ticket from clarify to merge in one go, asking only what it cannot decide

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
