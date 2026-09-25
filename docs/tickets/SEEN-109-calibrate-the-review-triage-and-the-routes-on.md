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

- [ ] harness/thresholds.toml carries a [calibration] section with the shadow window of ten tickets, the escape definition and the go-live rule for the triage and for the routes, committed before the first triage record it counts exists (as amended: SEEN-107 and SEEN-108 wrote triage and route records on their own branches while building the things under calibration, so the literal wording was impossible before this ticket began. The amendment is the exclusion rule in clarify record 4, decision 1: those two and this ticket are excluded by name, and counted_from is the commit that added the section)
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

Six deviations from the solution record. Four of them are files the plan did not name and
`slice_files` fails on, so a reader auditing that check finds every one here: `harness/doctor.py`,
`harness/kpi.py`, `harness/tests/test_context_budget.py` and `harness/tests/test_triage.py`. The
other two are about how the tests were run rather than which files changed. The two about running them: the tests were named in the plan as
`pytest` commands and this repository runs `unittest`, which is what every check records; and the
gate tests for the finding file went into `test_calibration.py` rather than `test_stage_gates.py`,
because that is the file slice 1 declared.

The four files, in the order the reviews forced them. `harness/tests/test_context_budget.py`: SEEN-108
left a guard there asserting `report --calibration` is not a command the parser accepts, with a note
saying the ticket that lands it may lose the tense. This is that ticket, so the sentence in
`render_cost` is in the present now and the guard holds the other direction. `harness/doctor.py`
came with attempt 3, for F3 of the second review: the go-live decision had to be checked somewhere,
and `doctor` is where it belongs, because CI runs it and a refusal in front of every triage would
make spot depth untestable. `harness/tests/test_triage.py` came with attempt 3 and attempt 4: its
two helpers that flip the go-live switch flip both lines now, and two fixtures that return a ticket
from review declare `--no-findings`. `harness/kpi.py` came with attempt 6, for F2 of the fifth
review: two committed reports must not state different findings for one ticket.

### What the review found

The `seen-reviewer` subagent returned the ticket on one high finding, recorded in full at note 17.
`path_of` stripped the characters `.` and `/` rather than the prefix `./`, so a finding in a dot
directory became a path nothing held: `.claude/agents/seen-reviewer.md` was compared as
`claude/agents/seen-reviewer.md`, matched no exclusion, and because the result was not empty no
unattributable row was written either. A high or blocking finding in any dot directory therefore
read as no escape at all, which is precisely the silent pass the recorded rule forbids, and this
ticket's own triage listed four such files among the thirteen it would have dropped. Both sides of
the comparison now come through one `normalise`, the prefix is removed as a prefix, and an absolute
path is placed nowhere rather than silently placed outside the exclusions.

Three more were taken in the same attempt. The weekly report's shadow line was tested only in the
branch that cannot see an escape, so deleting the escape branch left it green. `harness return
--unmet` had no test of its own, so removing the flag would have left the suite green while the
second escape kind became permanently undetectable. And a review return that named no criterion was
counted clean rather than unattributable, which left the rule depending on an operator remembering
a flag; it is now placed nowhere, and the triage's own return carries the numbers of the criteria
it could see no evidence for, so the one return that caught a criterion itself is not read as one
that forgot to say so.

The fifth finding is not implemented and is a question for the founder. Once spot depth is live a
reviewer no longer reads the files the narrowing drops, so a defect in one of them becomes a
finding only if the reviewer reads beyond its focus set; the safety net the ticket describes then
leans on that. An escaped defect is computed per ticket and shown in the report, but it is not an
escape by the ticket's own two-kind definition, and making it one would change the rule this ticket
exists to commit before the numbers. The limit is printed in the report and written into
`docs/harness/workflow.md` rather than left to be discovered.

### What the second review found

It returned the ticket again, and it was right to: the fix had stopped one line short. `_covers`
still stripped the characters `.` and `/` from a slice's planned files, one function below the
docstring written to explain why that is wrong, on the other side of the same comparison, where it
decides the route verdict rather than the triage one. A finding in a dot directory was charged to no
slice, so a downgraded slice that produced one read as having produced nothing, and findings are the
only per-slice measure the route rule has. Both sides now go through `normalise` and a test
exercises a slice whose files sit in a dot directory, which is what was missing the first time.

Three more, taken in the same attempt. Findings were read only from the record that passes, so a
blocking finding that returned a ticket counted only if the next round repeated it, which nothing
requires and three tickets happened to do; a returning round now records what it found with
`harness return --findings`, `escapes` reads both, and a finding is the same finding when its id,
its claim and its file agree, keyed at the earliest round that carried it because that is the round
whose triage would or would not have dropped the file. Going live was one line anybody could
change with no record anywhere of the decision; it now takes two, `[review] triage_shadow` and
`[calibration] went_live` naming the ticket and the record number, and `doctor` refuses a switch
flipped with nothing named. The check is in `effective_shadow` and in `doctor`, which CI runs, so a
branch that flips the switch with nothing named cannot go green; the harness's own triage tests flip
both lines now, which is the change propagating rather than a workaround and is the second
disclosed deviation from the slice plan, after `test_context_budget.py`. And `counted_from` was eight minutes earlier than the commit that added
the section, which is eight minutes in which a ticket could have been counted against a rule that
did not exist; it is read from the commit now.

The fifth is an evidence gap and is disowned in note 28 rather than reconstructed. Slice 1 planned
two REDs and record 7 is the first: it fails with the ImportError every test in the new file
produces, so it proves the module was absent and not that the review gate was permissive. A RED
recorded now would have to be produced by removing the requirement and running against a tree nobody
worked in, which is a check written to pass a gate. The behaviour is covered and the diff proves the
change; the journal does not prove the order, and note 28 is where a reader finds that out.

### What the third review found

Two mediums and six lows, the mediums both about the gap between what the harness now demands and
what a person is told or required to do.

The first was the one that mattered. A returning round's findings reached the window only if the
session remembered `--findings`, and the omission wrote an unattributable row that the verdict
counted neither way, so the ticket still read clean. Counted neither way had to mean the verdict
waits: a window carrying anything nobody can place now states stay-shadow rather than go-live,
naming the tickets, which is the escape definition as it was written rather than a new rule. And a
return from review must now declare itself, with `--findings`, with `--unmet` or with
`--no-findings`; the harness refuses one that says nothing, because an absence nobody declared
cannot be told from a flag somebody forgot.

The second was that every printed go-live instruction still said one line while the implementation
demanded two, including the `triage_rule` the report prints verbatim. A founder following the report
would have set `triage_shadow` false, turned CI red on every branch and got nothing live. Four
places now say two lines and name what `doctor` checks.

The six lows, in the same attempt. A receipt voided by `harness reopen` counted as a delivery, so a
ticket being worked could join the window and a verdict be taken on a review round that had not
happened; `delivered_at` reads the reopen. `verdict_routes` reported every route-carrying ticket
while its rates came from the last ten, so an audit would have recomputed over the wrong list.
Nothing distinguished charging a repeated finding to the earliest round's triage from charging it
to the latest, and a test now plants different exclusions in the two triages so the behaviour
cannot be removed quietly. Reading every journal was unguarded from inside the triage, so a stray
file in one journal would have refused the review stage of every other ticket; a journal that
refuses to be read is now excluded and named, and `doctor` remains where a damaged journal is
reported. Criterion 1 is marked `(as amended)`, the way this repository marks a criterion a ticket
deliberately did not meet. And a sentence in the workflow paragraph starts with a capital.

### What the fourth review found

The same class of defect a third time, reached through the shape of a reference rather than through
`lstrip`. An unattributable row was written only when the reference could not be read at all, so a
finding at `harness/skipped.py:12-20`, which is what a reviewer writes for a hunk, or at
`harness/skipped.py:58:5`, or at a path the triage never saw, was counted clean. Two answers were
giving the same reply: not in the exclusions, and not a file the triage ever read. The triage record
carries `files` as well as `would_exclude`, so a reference in neither is now placed nowhere, and the
tail of a reference is stripped whether it is a line, a hunk or a line and a column.

The triage read the escapes while the report read the escapes and the unplaceable evidence, so the
calibration report could say stay-shadow about the same tree the weekly report said `In shadow: no`
about, with four documents claiming the triage reads the verdict. It reads both now, and the four
documents say exactly that: an escape or evidence nobody can place returns a live triage to shadow,
while a window that is simply not full is a reason to conclude nothing and never a reason to
override the switch.

`--no-findings` was the third finding, and the reviewer made its case out of this ticket's own
journal: records 18, 26 and 37 carry no findings while notes 17, 25 and 36 record one high and three
mediums, one high and four, and two mediums and six lows. The harness cannot know what a reviewer
found, so it cannot refuse a wrong declaration; what it can do is name every round that made one,
which the report now does with the record, the actor and the reason. Record 47, the return that
carries this review, records its findings rather than declaring nothing, which is what the earlier
three should have done.

The fourth is a test: the printed go-live instruction is now pinned to naming both lines, in the
verdict's reason and in the rule the report prints verbatim, so the one-line instruction the third
review returned the ticket on cannot come back green.

### What the fifth review found

It was asked to settle whether the path-comparison defect three reviews had found three ways was
closed as a class, and it answered by running the module against planted records and against the
real journals of SEEN-105, SEEN-107, SEEN-108 and SEEN-109 rather than by reading it. Closed on the
triage side. Open on the route side, which is the fourth time the same shape appeared: `slice_rows`
charged a finding only to a slice whose planned files contained it, so a finding in a changed file
no slice named was charged to nobody, and `verdict_routes` had nowhere to put what it could not
charge. Ten counted tickets each carrying a blocking finding in an unnamed file produced a
downgraded rate of zero against a strongest rate of zero and a printed go-live.

Such a finding is now charged to every slice of the ticket, which is what `route_rule` already says
of a return and of an escaped defect and for the same reason: nothing says which slice caused it.
And the route verdict stays shadow while any finding in the window could not be charged, which is
what the triage verdict already does with evidence nobody can place. That is an amendment to
`route_rule`, taken while the window still counts nothing, so it is still a rule written before the
first number rather than after it. It is one line to reverse if the founder disagrees.

Three more with it. `kpi.findings` still read findings only from the review advance, so the weekly
report and the calibration report would have stated different findings for the same ticket in the
same commit; both read them the same way now, through the one function that knows a returning round
records its own. The `seen_by_triage` guard restored the merge the fourth review removed whenever a
triage record carried no files, and every `EscapeTest` fixture ran through that fallback rather than
through the real record shape; the guard is gone and the fixtures carry the shape. And the Outcome
now names all four files no slice planned, `harness/kpi.py` included, rather than three with one
described only in substance.

### What the sixth review found

It settled both questions it was asked. The path-comparison class is closed on both sides, checked by
running fourteen path shapes through both comparisons rather than by reading them: a plain path, a
hunk, a line and column, a dot directory, a leading `./` on either side, backslashes, surrounding
whitespace, an absolute path, an unreadable tail, a drive letter, a bare directory, a double slash, a
`./` segment mid-path and a case difference. On the triage side every one is either an escape or
placed nowhere; on the route side every one is either charged to a slice or held as uncharged. The
partition is exhaustive by construction rather than by patching, because `unchargeable` is the
complement of the union of every slice's planned files. And the amendment to `route_rule` is sound
and said the same way in the code, the rule, the workflow and the committed report, verified against
a window that still counts nothing.

It returned the ticket on a regression attempt 6 had introduced itself. Reading `kpi.findings`
through the calibration made every finding a returning round recorded count as waived, because a
return carries `status: open` and only a passing advance carries `resolved`; on this ticket's own
journal that was fixed 0 and waived 8 where all eight were fixed, and before the change `waived` was
structurally unreachable, so a dead figure had become a systematically wrong one. The answer is the
review gate's own rule: it refuses an advance carrying an unresolved finding, so a finding a later
advance followed was dealt with whoever wrote it down, and one on a return that nothing has advanced
past is still open and says so.

Three lows with it. `verdict_routes` tested a group by its rate rather than by its membership, so it
printed that no slice was routed below the strongest tier when the group held slices carrying no
points; it is the one merged comparison in the change that landed on the safe side, and it is two
answers now. `went_live_problem` swallowed a damaged journal into an empty record list, so a broken
chain and a record nobody wrote gave the same message and sent a reader to fix the wrong thing. And
the counts written around the four files were stale, which is what this section's own earlier
paragraph now states correctly.
