---
id: SEEN-113
title: "Let a tdd record cite the evidence a return did not invalidate"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-112]
status: doing
---
# SEEN-113: Let a tdd record cite the evidence a return did not invalidate

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

`gates.cited_check` refuses a check from another attempt, and the reason it gives is right: evidence from before a return cannot be quietly reused after one. What nobody had met until a ticket was returned five times is the other half of that rule. A return resets which checks a tdd record may cite, so a ticket returned more than once cannot accumulate its evidence: the slices proven in the first attempts are still green, their tests are still in the branch and the full suite still passes, but the tdd record of the final attempt can only cite the last slice, and the criteria the earlier slices answer lose their cited support.

SEEN-112 is the case that found it. Its criteria 3 and 4 were answered evidenced at 0.66 and 0.74 while their checks were citable, and at 0.59 and 0.58 once they were not, against a `criterion_evidenced` bar of 0.6 that `harness/thresholds.toml` itself calls a starting value nobody has evidence for yet. Nothing about the code changed between those readings. There is no honest way out from inside such a ticket, because re-proving a slice in a later attempt needs a RED for code that is already green, and a RED that cannot fail is the one thing the harness refuses outright.

The distinction the rule is missing is not the attempt. It is whether the tree moved. A check already records the fingerprint of the tree it ran against, before and after, so the question "is this evidence still about this code" is one the journal can already answer without trusting anybody's account of it. A check from an earlier attempt whose recorded fingerprint still matches the tree the citing record is written against is evidence about exactly this code; one whose fingerprint has moved is not, and stays refused. That keeps the original protection whole: what it was defending against was reusing evidence for code that changed, and the fingerprint is what says whether it did.

The same attempt boundary discards work in a second place. `handoff.plan_accepted_at` moves when a return re-accepts a plan, and `accepted_greens` counts only the greens recorded after it, so a replan makes the handoff pack and the guard read "slice 1 of 3, 0 of 3 done" while slices 1 and 2 are green and committed. On SEEN-112 that handed a session slice 1's file list for work that belonged to slice 3, and the session that walked into it could only proceed by writing through a shell the PreToolUse hook does not match. Both halves are the same mistake, so they are fixed together or the ticket has only half a point.

What this ticket must not do is weaken the rule it is loosening. A refusal has two reasons now rather than one, and it has to say which: the tree moved under this check, or there is no such check at all. A gate that answers "another attempt" where it means "different code" is the reason this took five returns to find.

## Acceptance criteria

- [ ] A tdd record may cite a red or green recorded in an earlier attempt when that check's recorded tree fingerprint matches the tree the citing record is written against, and the gate accepts it without the cited work being re-proven
- [ ] A check whose recorded fingerprint has moved since it ran is still refused across attempts, and the refusal names which of the two reasons applied: the tree moved under this check, or there is no such check
- [ ] The ordering rule survives the change: each red still precedes its green, slices still do not overlap, and the regression is still the last check, whichever attempts the cited checks come from
- [ ] A replan carries forward the greens of slices whose work is still in the branch, so the handoff pack and `harness guard` read a returned ticket as the slices it has actually finished rather than as none of them
- [ ] Proven on a journal shaped like SEEN-112's, five attempts with slices proven in the first two and a tdd record in the fifth citing them, which the gate accepts, and on the mirror case where one cited check's tree has moved, which it refuses by name
- [ ] No evidence is revived for code that changed: a test shows a check from an earlier attempt refused after its files are edited, with the fingerprint difference as the stated reason

## Slices

1. The fingerprint rule in `gates.cited_check` and its two refusal reasons, with the ordering rule held across attempts (2 pt). RED: a tdd record citing a green from an earlier attempt is refused although the tree has not moved, and the refusal says only "another stage or attempt"

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-112](SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md): Run a ticket from clarify to merge in one go, asking only what it cannot decide

## Blocks

- [SEEN-112](SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md): its delivery waits on this, because its own criteria 3 and 4 lost their cited support to the attempt boundary

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- The harness as built: [docs/harness/workflow.md](../harness/workflow.md)
- `harness/gates.py`, `cited_check` and the ordering line beneath it: the rule being loosened and the one that must survive
- `harness/handoff.py`, `plan_accepted_at` and `accepted_greens`: the second place the attempt boundary discards work still in the branch
- SEEN-112's journal, records 50 and 54: the case that found both, with the three triage readings that show the drift
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
