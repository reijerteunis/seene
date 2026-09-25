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
status: doing
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
| Status | doing |

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

## Outcome

The rule is on the record before the numbers exist. `[calibration]` in `harness/thresholds.toml`
carries the window of ten, `counted_from`, the three excluded tickets and why, the escape
definition and both go-live rules, and the loader treats a missing key as fatal like every other
rule in that file. `harness/calibration.py` derives the evidence from records that already exist:
the triage's `would_exclude` and `criteria_answers`, the review's findings, the route's `execution`
and the returns. `harness report --calibration` writes `docs/harness/reports/calibration.{md,json}`
with the evidence per ticket and per slice and states go-live or stay-shadow for each, by the rule;
a weekly report carries one line saying which shadow the triage is in and what put it there. On the
day it landed the report counts nothing: every ticket delivered so far started before the rule
existed, and the report says so ticket by ticket rather than showing an empty table.

Four judgement calls, all in the clarify record:

The criterion asks for the section to be committed before the first triage record exists, which was
already impossible: SEEN-107 and SEEN-108 wrote triage and route records on their own branches while
building the things under calibration. The rule SEEN-098 wrote for itself applies, so those two and
this ticket are excluded by name and `counted_from` is the moment the section was committed.

The window is the most recent ten counted tickets rather than a counter somebody keeps. That is
what makes the fourth criterion fall out of the rule instead of needing state: an escape holds the
verdict at stay-shadow until ten further tickets have pushed it out, which is the ticket's another
ten.

The return to shadow is computed and never written. Nothing rewrites `thresholds.toml`: going live
stays one line a person changes, and the triage asks `effective_shadow` rather than reading the
threshold alone. It returns to shadow on an escape and on nothing else. The first version returned
on any stay-shadow verdict, including a window that was not full yet, which overrode the founder's
own line and would have made going live impossible rather than early; twenty-four triage tests said
so.

Two record shapes had to change first, because without them the evidence is silently favourable to
the thing being measured. A finding at high or blocking severity must name the file it is in, which
`seen-reviewer` already emitted and the gate now requires; low and medium are left alone, because
neither can ever be an escape. And `harness return --unmet <n>` names the criteria a review found
unmet, which is the only thing that tells the second kind of escape from an ordinary return. A
finding or a criterion nothing can place is reported as unattributable and counted neither way.

What the route rule cannot do is name a cause. A return sends the whole ticket back and no record
says which slice caused it, so every slice of the plan carries it and an escaped defect is charged
the same way; findings are the one per-slice measure. That is written into `route_rule` so nobody
reads a per-slice rate as a per-slice cause.

Three deviations from the solution record. The tests were named there as `pytest` commands and this
repository runs `unittest`, which is what the checks record. The gate tests for the finding file
went into `test_calibration.py` rather than `test_stage_gates.py`, because that is the file slice 1
declared. And `harness/tests/test_context_budget.py` changed although no slice named it: SEEN-108
left a guard there asserting `report --calibration` is not a command the parser accepts, with a note
saying the ticket that lands it may lose the tense. This is that ticket, so the sentence in
`render_cost` is in the present now and the guard holds the other direction.
