---
id: SEEN-108
title: "Route each slice to a model and an effort at solution, by rule first and by Jev second"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-105, SEEN-098]
status: doing
---
# SEEN-108: Route each slice to a model and an effort at solution, by rule first and by Jev second

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Every slice runs on the session's model at the session's effort today, whatever the slice is. After the solution record is accepted, harness route <ticket> decides per slice which model and which effort implement it. Rules first, in a [routing] section of harness/thresholds.toml: a slice that changes an agent action, touches billing or the policy gate, money arithmetic in packages/core (detectors, matching, fee expectations), a migration or an RLS policy, or credentials goes to the strongest model at high effort, and Jev is not asked. Every other slice is a Jev choice: implementation_model over haiku, sonnet and opus and implementation_effort over low, medium and high, with the slice (points, files, the RED), the approach, the risk score from clarify, repowise's change-risk percentile, whether the pattern already exists in the repository (the codegraph and repowise answers on record), new dependencies, the marketplaces touched and the ticket's returns so far as state, and the criteria per option written into the question. The route lands in the solution record as execution (slice, model, effort, source rule or jev, probability) and in the handoff pack; the implementer subagent is spawned with it (Claude Code: the per-invocation model and the agent's effort; Codex: model and model_reasoning_effort in the agent TOML harness sync writes for that slice), and the tdd gate refuses a check recorded under a model other than the route's, reading the model from the session log the cost KPI already reads. The reviewer's model is a rule too: the strongest model at full depth, one tier down at spot depth. The decision that matters: the route is chosen where the information is, at solution with the slice plan and the risk answers on record, and never inside the session that would benefit from a stronger model.

## Acceptance criteria

- [ ] harness route <ticket> writes an execution entry per slice with model, effort, source and probability into the solution record, and the handoff pack carries it
- [ ] A slice matching a routing rule (agent action, billing or policy gate, money arithmetic in packages/core, migration or RLS, credentials) is routed to the strongest model at high effort without a Jev call, proven with a fixture
- [ ] The implementer subagent is spawned with the routed model and effort in Claude Code and in Codex, and a check recorded under a different model is refused by the tdd gate naming both models
- [ ] kpi.json carries model, effort, output tokens and cost per slice, and harness report --sprint shows cost per point by model beside the tokens per point it already shows
- [ ] docs/harness/skill.md says the route is read from the handoff pack and never chosen inside the session, and sync regenerates both copies

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate

## Blocks

- [SEEN-109](SEEN-109-calibrate-the-review-triage-and-the-routes-on.md): Calibrate the review triage and the routes on ten tickets before either saves a token

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
