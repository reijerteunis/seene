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
status: review
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
| Status | review |

## Description

`gates.cited_check` refuses a check from another attempt, and the reason it gives is right: evidence from before a return cannot be quietly reused after one. What nobody had met until a ticket was returned five times is the other half of that rule. A return resets which checks a tdd record may cite, so a ticket returned more than once cannot accumulate its evidence: the slices proven in the first attempts are still green, their tests are still in the branch and the full suite still passes, but the tdd record of the final attempt can only cite the last slice, and the criteria the earlier slices answer lose their cited support.

SEEN-112 is the case that found it. Its criteria 3 and 4 were answered evidenced at 0.66 and 0.74 while their checks were citable, and at 0.59 and 0.58 once they were not, against a `criterion_evidenced` bar of 0.6 that `harness/thresholds.toml` itself calls a starting value nobody has evidence for yet. Nothing about the code changed between those readings. There is no honest way out from inside such a ticket, because re-proving a slice in a later attempt needs a RED for code that is already green, and a RED that cannot fail is the one thing the harness refuses outright.

The distinction the rule is missing is not the attempt. It is whether the tree moved. A check already records the fingerprint of the tree it ran against, before and after, so the question "is this evidence still about this code" is one the journal can already answer without trusting anybody's account of it. A check from an earlier attempt whose recorded fingerprint still matches the tree the citing record is written against is evidence about exactly this code; one whose fingerprint has moved is not, and stays refused. That keeps the original protection whole: what it was defending against was reusing evidence for code that changed, and the fingerprint is what says whether it did.

The same attempt boundary discards work in a second place. `handoff.plan_accepted_at` moves when a return re-accepts a plan, and `accepted_greens` counts only the greens recorded after it, so a replan makes the handoff pack and the guard read "slice 1 of 3, 0 of 3 done" while slices 1 and 2 are green and committed. On SEEN-112 that handed a session slice 1's file list for work that belonged to slice 3, and the session that walked into it could only proceed by writing through a shell the PreToolUse hook does not match. Both halves are the same mistake, so they are fixed together or the ticket has only half a point.

What this ticket must not do is weaken the rule it is loosening. A refusal has two reasons now rather than one, and it has to say which: the tree moved under this check, or there is no such check at all. A gate that answers "another attempt" where it means "different code" is the reason this took five returns to find.

## Acceptance criteria

- [x] A tdd record may cite a red or green recorded in an earlier attempt when that check's recorded tree fingerprint matches the tree the citing record is written against, and the gate accepts it without the cited work being re-proven
- [x] A check is refused across attempts whenever the code it covers has changed, and the refusal names which of four reasons applied: there is no such check; the check recorded no tree at all; the code this check covers has changed, naming what the round moved and what its slice names; or the tree moved and the comparison fell back to the whole tree, naming which of nine reasons it fell back for (amended, see `## Amendment`)
- [x] The ordering rule survives the change: each red still precedes its green, slices still do not overlap, and the regression is still the last check, whichever attempts the cited checks come from
- [x] A replan carries forward the greens of slices whose work is still in the branch, so the handoff pack and `harness guard` read a returned ticket as the slices it has actually finished rather than as none of them
- [x] Proven on a journal shaped like SEEN-112's, five attempts with slices proven in the first two and a tdd record in the fifth citing them, which the gate accepts, and on the mirror case where one cited check's tree has moved, which it refuses by name
- [x] No evidence is revived for code that changed: a test shows a check from an earlier attempt refused after its files are edited, with the fingerprint difference as the stated reason

## Amendment

**27 September 2026, recorded at journal record 20's review, and written by the orchestrating session
because it is bookkeeping the review was right to call out.**

Criterion 2 was written as:

> A check whose recorded fingerprint has moved since it ran is still refused across attempts, and the
> refusal names which of the two reasons applied: the tree moved under this check, or there is no such check

That wording describes the whole-tree rule the first plan specified, and record 9 amended that plan: the
comparison is scoped to the files the cited check's slice names, so a check whose recorded fingerprint has
moved is now accepted when its own slice's files have not, which is the entire point of the scoping. There
are three refusal reasons rather than two. The criterion is restated to describe the behaviour the amended
plan asks for, and the original is quoted above so the change is legible rather than silent.

Nothing is loosened by the restatement: the property that matters, that no evidence is accepted for code
that changed, is criterion 6 and it is unchanged. The review returned this ticket with criterion 6 unmet on
two reproduced paths, which is the right verdict, and the restated criterion 2 would not have hidden either
of them.

What went wrong is worth naming rather than only fixing: the box was ticked while the delivered rule
contradicted the criterion's first clause, in a ticket whose sibling SEEN-112 carries a criterion about
never ticking what the evidence does not support. The review caught it; the Outcome had not.

## Outcome

`gates.cited_check` keeps its phase and stage requirements and replaces the attempt requirement with a content
test: a check counts when it was recorded in this attempt, or when the code it covers has not changed since it
ran. Three review rounds shaped what "the code it covers" means, and the answer no longer rests on any
record's claim about itself.

`_the_files_the_round_moved` takes the commit whose content is the tree the check ran against, diffs it
against its first parent, and filters to the paths the fingerprint counts. It walks back over commits that
moved nothing counted, because the newest commit matching a tree is usually a journal-only one whose own change
the fingerprint excludes: on SEEN-112, check 11's tree is carried by a note-and-handoff commit, so without the
walk-back the scoped comparison this ticket exists for was unreachable in practice. The comparison is the
**union** of what the round moved and what the declared slice names, so a declaration can only add files and
never remove one, and the position a citing record claims must still be corroborated by the positions other
accepted tdd records declared for that check. Every entry in a granted scope must resolve in the commit
compared against, so a typo, a gitignored path, a file created later or a pathspec git will not take discards
the whole scope and falls back. Four refusal sentences say which situation applies, and nine reasons say why a
comparison fell back to the whole tree, one of which is always the regression, because it covers the suite and
not a slice.

`handoff` counts slices proved rather than greens recorded, each run capped by the plan it actually ran
against, so a shorter plan's correction greens cannot survive into a plan that grew; and a green that two
records disagree about does not advance the count at all, which is the gate's fail-closed reading rather than a
vote for the larger number.

**What the reviews cost and bought.** Three rounds, five high findings, every one reproduced end to end rather
than argued from the diff. Round one: a citation declared under another slice's position was compared against
that slice's files and accepted; a file entry matching no path made the comparison vacuous; and the
carry-forward counted greens rather than slices, which read worse than the code it replaced. Round two: the
corroboration was only one round deep, because a same-attempt citation skips the content test and the route
comparison returns immediately in shadow, so one mis-declaration self-corroborated for the rest of a ticket;
and a shorter plan's greens survived a plan that grew, with this ticket's own journal one green short of the
harm. None of the five was visible from the diff without constructing the input, and two of round one's three
were confirmed closed across fifteen constructed inputs before round two moved on.

**What this does not do, measured three times.** It does not unblock SEEN-112, the ticket that found the
defect. All fourteen of its citations are refused before and after the change, four slice pairs and four
regressions across four tdd records: attempts 3 and 4 reworked exactly the files slices 1 and 2 named, so that
evidence really is about code the ticket changed since, and the corroboration was satisfied rather than
missing. Two refusal sentences changed and both are still refusals. Its handoff count is unchanged at three of
three, and `slices_proved` now returns three rather than four, so the clamp is no longer hiding an over-count.
The rule was not bent toward the ticket that motivated it, and the reviewer verified that independently in
every round.

**The named next step, which is not this ticket.** A cross-attempt RED can never pass a content test by
construction: a red runs against the pre-fix tree, and the files its slice names must change before its green.
Since a tdd record needs a red and a green per slice, it can never accept a real cross-attempt slice pair.
Judging a slice's pair by its green, whose standing the ordering rule and the red's own recorded failure
already carry, is the next step. Reaching for it here would have been the motivated reasoning this ticket was
warned about in all three rounds.

Three narrowings and one duplication to own. The corroboration is a necessary condition, so a slice proved in
an attempt that never advanced out of tdd can never be cited later: fail-closed, and a real limit on what a
heavily reworked ticket can accumulate. `_require_the_routed_model` still returns immediately while `[routing]
shadow` is true, so nothing in the route comparison would have caught a mis-declared position. Five README rows
still disagree with their own frontmatter, inherited from main and not touched here beyond this ticket's own
row and the two counts. And `content_fingerprint` reads the fingerprint definition a second time because
`harness/repository.py` was outside the slice's files; the pinning test now catches a drift in the
pending-and-untracked half as well, and its honest home is still `Repository`.

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
