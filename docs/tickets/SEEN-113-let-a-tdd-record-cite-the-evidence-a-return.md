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
- [x] A check is refused across attempts whenever the code it covers has changed, and the refusal says which situation it is refusing rather than giving one sentence for every situation (amended twice, see `## Amendment`)
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

**Second amendment to criterion 2, 27 September 2026, recorded at journal record 44.** Its wording has now
changed twice and a reader should be able to see all three versions. As written:

> A check whose recorded fingerprint has moved since it ran is still refused across attempts, and the refusal
> names which of the two reasons applied: the tree moved under this check, or there is no such check

As first restated, after the second review found that wording described the whole-tree rule record 9 had already
amended away:

> A check is refused across attempts whenever the code it covers has changed, and the refusal names which of
> four reasons applied: there is no such check; the check recorded no tree at all; the code this check covers
> has changed, naming what the round moved and what its slice names; or the tree moved and the comparison fell
> back to the whole tree, naming which of nine reasons it fell back for

The first restatement was accurate and written at the wrong altitude. A criterion states what must be true; an
enumeration of the implementation's branches is documentation, it is already in the Outcome in full, and putting
it here turned one claim into thirteen. So the criterion now states the claim and the Outcome keeps the list.

**Nothing is claimed less than the code does**, which is the test that separates a correction from a tuning:
all four refusal sentences and all nine fallback reasons remain asserted by tests and described in the Outcome.
What moved is where the list is written down. The reviewer should be suspicious of a criterion reworded three
times and is asked to judge exactly that: whether the restatement gives up any assurance the previous one made.

The reading it was refused on, and why the threshold was not touched instead: 0.52 against a bar of 0.6 that
`harness/thresholds.toml` calls a starting value nobody has evidence for yet. `harness report --calibration`
reports two counted tickets against a window of ten, and the window's own rule says an unfull window is a reason
to conclude nothing rather than to override a switch. Two of the three readings that have crossed this bar are
this session's own blocked tickets, which is the worst position from which to lower it.

## Outcome

`gates.cited_check` keeps its phase and stage requirements and replaces the attempt requirement with a content
test: a check counts when it was recorded in this attempt, or when the code it covers has not changed since it
ran. Five rounds and three reviews shaped what that sentence means, and every clause of it exists because using
the rule found something reading it had not.

**The scope is the code the check covered, not the tree.** Every green records a distinct tree (SEEN-107 thirteen
of thirteen, SEEN-109 thirteen of thirteen), so a whole-tree comparison can never accept an earlier slice's green
on a ticket whose later slices added code. The scope is therefore the files the cited check's slice names, widened
by what the round's own commit moved so a declaration can only add files and never remove one. **A citation cannot
vouch for its own scope**: the position it claims must be corroborated by the positions other accepted tdd records
declared for that check, and a disagreement, a null, or nothing at all falls closed to the whole tree. Every entry
in a granted scope must resolve in the commit compared against, so a typo or a gitignored path discards the scope
rather than comparing nothing.

**A round that belongs to no single slice is scoped by the plan.** Null is what the template asks a rework round
to declare, so treating it as unknowable refused exactly the rounds a return produces. Several slices and
unknowable are different things, in the same way that no plan accepted and every slice done were different in the
defect that started this ticket.

**The commit search tolerates the one path the procedure forces.** The workflow requires the `## Outcome`, the
frontmatter `status` and the ticks before review is left, so the ticket file always moves between a check and the
commit carrying its work, and no commit carries the recorded tree. The fingerprint and `FINGERPRINT_EXCLUDED` are
untouched, because covering the whole ticket file is what gives the receipt its meaning and SEEN-109 withdrew an
attempt to weaken it. Only the search became tolerant, of that one path, and a candidate differing in it and
anything else is refused by name. The copies `sync` generates are deliberately not tolerated.

**A slice's pair is judged by its green**, which is Ruud's decision at record 57. A red runs on a tree holding the
test without the code that answers it, so no commit ever carries a red's tree: measured, none of SEEN-112's five
reds is any commit's content modulo any single path. The green's comparison is made first and passed into the
red's citation, a pair whose green is refused fails as a pair, and both halves must come from the same attempt,
which all 100 slice entries in every journal already satisfy. What a red keeps is everything it ever really had:
a non-zero exit, a failure for the reason its slice states, its place in the ordering, and its route.

**What the rule refuses, and this is the part worth trusting.** It refuses this ticket's own citation. Records 34
and 35 are not citable, the failing half is the green, and the reason is that attempt 5 rewrote the two files it
covers. The ticket advanced by the ordinary path instead, citing the attempt-5 pair its last round produced. And
across every delivered journal, 274 citations evaluated twice with the tolerance on and forced off: no verdict
moved, none of the 274 is cross-attempt, and none of the 100 pairs is split across attempts.

**What it now carries that nothing did before**: on SEEN-112's branch, slice 3's pair is citable whole, the first
cross-attempt pair in any journal that is, while slices 1 and 2 stay refused by name on the files attempts 3 and 4
reworked. That is the shape the ticket was written for, and the shape next to it that must still refuse.

Three reviews, six high findings, all closed: a citation compared against another slice's files and accepted; a
file entry matching no path making the comparison vacuous; a carry-forward counting greens rather than slices,
which read worse than the code it replaced; a corroboration only one round deep, so one mis-declaration
self-corroborated for the rest of a ticket; and a shorter plan's greens surviving into a plan that grew. None was
visible from the diff without constructing the input.

What is left, named rather than owned. Inside one attempt the pairing of a red to a green is the record's word:
the ordering makes entries disjoint and the attempt ties the halves, but nothing distinguishes one slice's red
from another's, and a nearest-red rule was measured wrong rather than argued away, because SEEN-098's green 8
belongs to red 6 with another red at 7. `content_fingerprint` reads the fingerprint definition a second time
because `harness/repository.py` was outside the plan, pinned by a test that now compares on a dirty tree as well
as a clean one. `_require_the_routed_model` still returns immediately while `[routing] shadow` is true, so nothing
in the route comparison would catch a mis-declared position. And `criterion_evidenced` remains an uncalibrated 0.6
with two counted tickets against a window of ten, which record 44 records rather than moves.

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
