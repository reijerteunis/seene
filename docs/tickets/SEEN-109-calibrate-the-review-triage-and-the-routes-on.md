---
id: SEEN-109
title: "Calibrate the review triage and the routes on ten tickets before either saves a token"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-107, SEEN-108]
status: todo
---
# SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Both decisions can cost more than they save: a spot review that misses a blocking finding, a slice routed to a small model that returns from review twice. So neither takes effect on a guess. For ten tickets both run in shadow: the triage is computed and the reviewer still reads everything; the route is computed and every slice still runs on the current model. Then a rule written now, before the first measurement, decides. An escape is a finding at high or blocking severity in a file the triage would have excluded, or a criterion the triage answered evidenced that the reviewer found unmet; with no escape in ten tickets, spot depth goes live and stays until the first escape, which returns it to shadow for another ten. For the routes, the slices Jev would have sent to a smaller model are compared with the rest on returns, findings and escaped defects; the route goes live when their rework rate is at or below the strongest model's over the window. harness report --calibration shows the evidence per ticket and states go-live or stay-shadow for the triage and the routes separately, and the switch is a founder decision recorded in the journal of the ticket that flips it. The decision that matters: the rule for reading the numbers is on the record before the numbers exist, as it was for the context tools in SEEN-099.

## Acceptance criteria

- [ ] harness/thresholds.toml carries a [calibration] section with the shadow window of ten tickets, the escape definition and the go-live rule for the triage and for the routes, committed before the first triage record exists
- [ ] harness report --calibration shows per ticket the reviewer's findings by severity, the files the triage would have excluded, the escapes, and per slice the recorded route against the returns and findings that followed
- [ ] After ten tickets the report states go-live or stay-shadow for the triage and for the routes separately, by the rule, and the founder's decision is recorded in the journal of the ticket that flips the switch
- [ ] An escape after go-live returns the triage to shadow automatically and the weekly report says so

## Depends on

- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff
- [SEEN-108](SEEN-108-route-each-slice-to-a-model-and-an-effort-at.md): Route each slice to a model and an effort at solution, by rule first and by Jev second

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
