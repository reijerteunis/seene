---
id: SEEN-107
title: "Let Jev settle what the review can settle before a model reads the diff"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-105, SEEN-098, SEEN-104]
status: doing
---
# SEEN-107: Let Jev settle what the review can settle before a model reads the diff

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

The review is the most expensive read in the procedure: a model reads the whole diff, the journal and the criteria, and Jev only scores the findings it wrote. Turn the review into three passes, cheapest first, so the model reads only what the cheaper passes could not settle. Pass one runs no model: the checks the harness already has (coverage, lint, gitleaks, the fingerprint, files inside the accepted slice) plus the ones the journal makes possible (a RED recorded as failing for the stated reason, tests added, an acceptance_evidence entry for every criterion, the pull request body's required parts). Pass two is one Jev request with the journal and the diff excerpts as state: criterion_evidenced per acceptance criterion (noul: does the cited check record, test name or hunk satisfy it), diff_matches_solution (noul: are the files and the mechanism the ones the solution record named), reviewer_must_read per file (noul, with the hunk size, the package, repowise's change-risk percentile, the coverage delta and whether the solution record named the file as state), and review_depth (choice: spot, full). Pass three is the reviewer subagent from SEEN-105 reading only the focus set at that depth, its findings scored by severity and must_fix as today. Three things stay rules, never Jev: a ticket that changes an agent action, touches billing or the policy gate, or carries a migration always gets full depth; a criterion Jev marks unevidenced returns the ticket to tdd with the criterion named before any model reads anything; and nothing here takes effect until SEEN-109's shadow window says it saves more than it misses. The decision that matters: Jev cannot execute a test or read the repository, so every answer it gives is only as good as the state the harness puts in front of it, which is why pass one exists and why the state is excerpts the journal already holds, not the tree.

## Acceptance criteria

- [ ] harness review triage <ticket> runs the deterministic pass and one Jev request and writes a triage record carrying the per-criterion answers, diff_matches_solution, reviewer_must_read per file, review_depth and the focus set, each with its probability
- [ ] A criterion answered unevidenced below the threshold returns the ticket to tdd naming the criterion, before the reviewer subagent is spawned, proven with a fixture
- [ ] A ticket that changes an agent action, touches billing or the policy gate, or carries a migration gets full depth by rule with Jev not asked, proven with a fixture
- [ ] The reviewer subagent's task carries only the focus set at the chosen depth, and the review gate refuses a review record whose recorded read list is smaller than the focus set
- [ ] In shadow mode the reviewer still reads everything and the triage record stores what would have been excluded; kpi.json carries the reviewer's output tokens and the excluded share of the diff

## Depends on

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate
- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack

## Blocks

- [SEEN-109](SEEN-109-calibrate-the-review-triage-and-the-routes-on.md): Calibrate the review triage and the routes on ten tickets before either saves a token

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

Delivered on 24 September 2026 in six attempts, three slices and five rework
slices, one session by the digest: `253bf8e84e82`. The return was the triage's
own doing: run on this branch at record 19 it flagged the four files `sync`
generates as changed but named by no slice, while the solution record named both
their sources. A generated copy has no review surface of its own, because
`doctor` refuses one that does not match what its source would generate, so
naming the source is naming the copy; left in place it would have forced full
depth on every harness ticket that runs `sync`, which is most of them, and left
SEEN-109 nothing to calibrate. `triage.generated_paths` is the fix. The nine
other paths the same check flagged were a true positive and stand: adding one
required field to the review template really did change six test fixtures the
solution record never named, so this ticket reviews at full depth on its own
evidence. The second return was the reviewer's, and it found three holes worth
code. A well-formed Jev reply that left one answer key out was treated as a
transport failure, so it destroyed the whole triage rather than recording that one
absence, and with no triage record the review gate then had no focus set and would
have accepted any read list at all. Nothing re-checked the diff between the triage
and the review advance, so a file added in between was read by nobody and refused
by nothing. And `kpi.json` could never have carried the reviewer's tokens that
criterion 5 names, because delivery is its only writer and called `kpi.measure`
without them.

The third return came from the review of those fixes, and three of its five
findings were the fixes themselves being half right. The F1 fix made an elided
answer key cheap instead of fatal, and then `focus_set` scored that absence zero
and dropped the file from a spot review, which is the exact inversion of the rule
the module states twice elsewhere: a judgement nobody made resolves towards
reading more. `review_window` opened at the first triage of the ticket rather than
the last, so on this ticket it spanned records 19 to 33, two returns and two whole
tdd attempts, and would have charged every scout and, from SEEN-108, every
implementer subagent to the reviewer. And the only guard on the F3 fix asserted
that two words appeared in the source of `delivery.verify`, while the comment
above the call carried both, so it passed with the behaviour removed. That one is
now a walk to delivered through a real triage, with a subagent entry inside the
review window and an implementer entry outside it, reading the figure out of the
delivered file.

The fourth return was the sharpest, and it was about what the triage claims rather
than what it computes. The task said to read the focus set "and no others", but
the journal can never be in a focus set, because the changed-file list drops
everything the fingerprint excludes, and the ticket file can be dropped from one at
spot depth like any other file. At spot depth the task would have told the reviewer
not to read the criteria or the evidence it reviews against. The task now names
those two separately, above the focus set, and "no others" is scoped to the diff.
Two checks were also claiming more than they prove and then being listed as
settled: `red_before_green` proves the cited check exited non-zero and never that
it failed for the reason the slice states, which is the failure this ticket had
already had once and resolved without code, and `acceptance_entries` counts two
lists against each other without either saying which entry answers which. Both are
handed to the reviewer now with the remainder named, in `PARTLY_SETTLED`, rather
than closed.

The fifth return was the one that mattered most, and the reviewer found it by
reading this ticket's own journal rather than its code. A failed deterministic
check was appended to the same list as the three depth rules, and the whole Jev
request was skipped whenever that list was not empty. So `criterion_evidenced`,
the one answer that can send a ticket back, was never asked on exactly the tickets
pass one had already found something wrong with, which is the opposite of what the
solution record said was being built. The evidence was in the journal all along:
all five triages on this branch carried `jev.asked: false` and
`criteria_answers: []` because `slice_files` fails on this ticket, so pass two had
never run once while the ticket that builds it was being worked. Only the three
rules silence the request now. The same finding exposed a second: every one of
those triages recorded `excluded_share: 0.0`, which in `kpi.json` cannot be told
apart from a narrowing that would have saved nothing, and that is the figure
SEEN-109 divides on. The record now carries two depths, what the rules enforced
and what the model would have chosen, and measures the narrowing against the
second, so a narrowing that never ran still has a number. The solution gate refused twice at 0.58 against 0.6 and
cleared at 0.65 once the record named the interfaces the clarify decisions had
settled, which is the gap the question was right about: Jev is shown the solution
record and not the clarify one, so a mechanism decided at clarify and never
restated is a mechanism an implementer would have had to stop and ask for.

**What was built.** `harness review triage <ticket>` runs at the review stage and
appends a `triage` record, its own journal kind for the reason `handoff` is one.
Pass one is nine named checks answering pass, fail or unavailable with a line of
detail each: coverage, lint, gitleaks, the reviewed-tree fingerprint, every changed
file being one the slice plan named, a RED that failed, a test in the change, an
entry in the clarify record for every criterion in the ticket, and a pull request
whose body names the ticket. A failure forces full depth and is carried in the
record rather than refusing, because most of these can be unavailable for a reason
about the machine rather than about the work.

Pass two is one Jev request. `jev.ask_batch` keys the payload rather than naming
it, so one request carries `criterion_evidenced` once per criterion,
`diff_matches_solution`, `reviewer_must_read` once per changed file and
`review_depth`, each with the subject that tells it from its siblings in its own
instructions; `ask_many` is now a wrapper over it and every earlier call site is
unchanged. All four questions carry no stage, so the review advance still asks only
`severity` and `must_fix`. `must_answer=False` is what separates the triage from a
stage gate: a stage needs a judgement and refuses without one, and the triage
records the absence, because a judgement nobody made must neither send a ticket
back nor narrow a review.

Pass three stays a model the harness does not run. The record carries the task
text naming the focus set and nothing else, and the review gate refuses a review
record whose `read` list does not cover that focus set, so what the reviewer was
given and what the gate checks are one list read from one record. `[review]
triage_shadow` is true, so the focus set is still the whole diff and
`would_exclude` and `excluded_share` record what the narrowing would have dropped;
that is the figure SEEN-109 decides on, measured before anything is decided by it.
`kpi.measure` carries `review_triage`, null on a journal without one, and the
reviewer's own output tokens come from the session log's sidechain entries over
`kpi.review_window` rather than being typed by the session they measure.

**What the work settled that the ticket did not.** Three rules stay rules, and two
of them are `gates.full_depth_rules`, the one predicate `needs_two_reviewers` also
reads, so the copy that H3 of SEEN-105 warned about was never made. Every doubt
resolves towards reading more: a tie on `review_depth`, an unavailable answer and
any failed check are all full depth, and a spot focus set is never empty. The
ticket file is excluded from the slice-plan check, because the procedure writes it
and no solution record plans it, so the check would otherwise have failed on every
ticket including this one, and generated copies are excluded for the same reason
one layer out; `triage.procedure_paths` is the one set, and the review gate's
`code_fingerprint` comparison leaves out the same paths, because the procedure
writes them between the triage and the advance every time. Neither is excluded
from the diff, only from those two comparisons: they changed, and a reviewer can
still be sent to them. The `## Outcome` section is written before the regression
rather than after it, because the triage's own fingerprint check compares against
the tree the tests last ran on, and that one has no exemption to give.

**What is unsettled.** No subagent has ever been logged on this repository: every
`isSidechain` field in the session logs reads false, so the reviewer's token figure
is null until the first ticket runs the reviewer as a subagent, and the null is
what says so. The four thresholds in `[jev.thresholds]` and `[review]
focus_probability` are starting values with no evidence behind them yet; SEEN-109
calibrates them on ten tickets, and nothing narrows a review until it does. Two
review findings were resolved without code and their reasons are in the review
record: the accepted tdd evidence for slice 3 states a failure reason that check
12 does not show, because the fixture was corrected between that RED and its
GREEN, and the triage's own fingerprint check fires on the ticket file whenever a
triage is re-run after the procedure has written it, which is bounded to forcing
full depth and is SEEN-109's to carry. Three findings across the three reviews
were about a check that fires on the harness's own writing, and the answer each
time was to name what the procedure writes rather than to weaken the check:
`triage.procedure_paths` is that list, and it is left out of the slice check and
of the fingerprint the review gate compares, and of nothing else. The reviewer's
token figure counts every subagent entry in the review round, because the session
log cannot tell one subagent from another: a scout spawned to answer a question a
finding raised lands in it too. The window is right and the name claims more than
the log supports, which is recorded here rather than renamed, because criterion 5
names the figure and SEEN-109 is the ticket that divides on it. Three checks pass
on less than their name suggests and are handed to the reviewer with the remainder
named rather than listed as settled: `red_before_green`, `acceptance_entries` and
`tests_added`. A ticket renamed after it started is followed by `cli.ticket_file`,
the one resolver `_ticket_text` already used, rather than by a second reading of
record 1.
