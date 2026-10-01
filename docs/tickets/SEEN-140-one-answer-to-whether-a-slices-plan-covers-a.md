---
id: SEEN-140
title: "One answer to whether a slice's plan covers a path"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: []
fixes: SEEN-104
status: done
priority: P0
---
# SEEN-140: One answer to whether a slice's plan covers a path

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |
| Priority | P0 (it blocks SEEN-114 at the review stage) |

## Description

Three places in the harness ask whether a slice's plan covers a changed path, and they do not agree. `harness/calibration.py` `_covers` answers it for the route verdict and reads a directory entry: a slice naming `packages` covers `packages/core/db/tables.ts`. `harness/guard.py` answers it for the PreToolUse guard with `if relative not in entry['files']`, and the triage's `_slice_files_check` in `harness/triage.py` answers it with `path not in named`; both compare exactly, so the same slice naming `packages` covers nothing inside it. One question, three readers, two answers, and the looser one is the one a session meets first.

SEEN-114 is what that cost, three ways in one ticket. Its slices named `apps` and `packages` because adopting a formatter rewrites every source file it is pointed at, twenty-six of them, and that is the honest way to say so. One implementer was refused the right to write `rules/fixtures/<slug>/violation.ts` and `packages/core/db/tables.ts` although its plan named `rules/fixtures` and `packages`, and wrote both through a shell, which the PreToolUse guard does not intercept; another met the same refusal, stopped and reported, so the two agents behaved differently because the guard did, not because they did. Then the triage returned the ticket three times saying it could see no evidence for two criteria, with `slice_files` failing in each round and naming about forty files as belonging to no slice: the criteria whose evidence lives in exactly those files are the two Jev would not answer yes for, at 0.36, 0.37 and 0.39 against a threshold it never approached, while every check that proves them was recorded and moved it by hundredths.

The fix is one shared reader rather than three, and it is small. `_covers` is already the right answer and already tested, so it moves to where all three can call it, and `guard.py` and `triage.py` call it. What the ticket must not do is widen it: a slice naming `packages` covering `packages/core/db/tables.ts` is the behaviour `gates.py` has had since SEEN-104, decided there and not here, and the point is that the other two stop disagreeing with it. The guard's refusal message keeps naming the files the slice listed, because a path is what a session can go and look at.

One thing the ticket has to answer rather than assume: whether a slice that names a directory should be allowed at all, or whether the solution gate should refuse a plan whose slices overlap. SEEN-114 would have been a different ticket with narrower slices, and record 107 of its journal argues that `apps` and `packages` was the true description of a formatter adoption. That question is noted and not settled here; this ticket makes the three readers agree, which is the defect, and leaves the policy to the founder.

## Acceptance criteria

- [x] (as amended) One function answers whether a slice's plan covers a path, called by `harness/calibration.py`, `harness/guard.py` and `harness/triage.py`, with no second implementation of the comparison anywhere in `harness/`
- [x] `harness guard <path>` allows a write to a file inside a directory the accepted slice names, and still refuses one outside every entry, with the refusal naming the entries
- [x] The triage's `slice_files` check passes when every changed path is inside a directory the plan names, and still fails on a path no entry covers, with the failure naming it
- [x] A test fails before the change for each of the two readers: one proving `harness guard` refused a path inside a named directory, one proving `slice_files` reported such a path as belonging to no slice
- [x] (as amended) The whole harness suite is green

## Amendments

- **1 October 2026, Claude Code: criterion 1 is amended.** The third caller is
  `harness/calibration.py` and not `harness/gates.py`, which this ticket's own
  description got wrong when it was written. `gates.py` never asks the membership
  question: it collects a slice's files and hands them to git as a pathspec, so what
  it asks is "what changed under these paths", which git answers directory-aware by
  its own rules and which no Python predicate can be asked. The membership readers
  were three and are now one. `NoSecondReaderTest` holds that by grepping
  `harness/*.py` for a hand-written exact comparison against a plan's files, and it
  is the guard against a fourth.

- **1 October 2026, Claude Code: criterion 5 is amended.** Its second half asked
  that SEEN-114's `slice_files` check pass against its own journal and diff. That
  measurement happens on another branch, after this one merges and that one rebases,
  so it can never be evidenced in this journal, and a criterion that cannot be
  evidenced where it is written holds a ticket at the gate for ever. The review
  triage answered it unevidenced at 0.10 before any model read anything, twice, which
  is the triage doing its job. It is removed from the criterion and recorded as the
  follow-up it is: the first thing SEEN-114's next session does, in that ticket's
  journal. What is left is this branch's own suite, green at 1,449 tests in record 24.

- **1 October 2026, Claude Code: a note on where an amendment goes.** The first
  attempt at both of the above wrote the reasoning inline in the criterion. The
  triage reads a criterion as the text of that line, so the explanation became part
  of what Jev was asked to find evidence for, including the sentence saying the
  triage had been right to refuse it, and the answer fell to 0.10. SEEN-105's
  convention is the one that works and is now followed here: `(as amended)` in the
  criterion, the reasoning in this section.

## Depends on

Nothing. The three readers all exist on `main`.

## Blocks

- SEEN-114: Turn every recurring finding into a rule the pre-commit hook runs in seconds. It is parked at the review stage with four slices proved and the triage returning it on this defect.

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The evidence: SEEN-114's journal records 36 (the guard refusing a directory's contents), 52 and 103 (what it cost the tdd record), and 107 (the three triage rounds and the one cause under them)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

Delivered on 1 October 2026 in one slice. `normalise` and a public `covers(path, files)` live in
`harness/paths.py`, the leaf module that imports only `pathlib` and `re`; `calibration.py` imports
them back so its seven call sites keep the names they use; `guard.py` rule 4 asks
`covers(relative, entry['files'])` and `triage.py`'s `_slice_files_check` asks `covers(path, named)`.
One question, one reader. 1,449 harness tests pass, coverage on `packages/core` is 100.0 at a delta
of 0.0, `doctor` is clean.

The body of `_covers` moved unchanged, which was the one thing that could have gone wrong invisibly:
every caller was inside `calibration`, so its own tests would have passed against a subtly different
function. `OneReaderOfTheQuestionTest` pins the moved answers on nine cases, dot directories among
them, which is F1 of SEEN-109's second review and the thing a careless move would have dropped, and
it asserts `calibration.covers is paths.covers` so the import cannot quietly become a second copy.
`NoSecondReaderTest` greps `harness/*.py` for a hand-written exact comparison against a plan's files
and found the two this ticket removed.

Nothing was widened but those two comparisons. The `exempt` set in `_slice_files_check` stays exact,
because a generated path and the ticket file are named exactly and are not directories. The guard's
refusal still names the plan's own entries rather than a normalised form of them, so a session that
reads them can go and look at them in the solution record.

### Three REDs, one per reader

Records 6, 7 and 8. The guard refused `packages/core/db/tables.ts` against a slice naming `packages`,
with the entries in the message. The triage reported `harness/rules/fixture.py` as
"named by no slice and no changes entry" against a plan naming `harness/rules`. And `paths.covers` did
not exist, so the test pinning the moved function failed on the import while `NoSecondReaderTest`
listed both offenders by file and line. Greens at 9, 10 and 11.

### The deadlock this ticket had to break, and how

Its first regression, record 12, was red on one test:
`test_triage.PartlySettledIsDocumentedTest.test_the_workflow_names_every_partly_settled_check`, which
fails on `main` and has since `4b2ecc1`. SEEN-139's docs regeneration deleted the paragraph of
`docs/harness/workflow.md` naming the three partly-settled checks while `triage.PARTLY_SETTLED` still
lists them. The implementer verified it by stashing its whole change and left it alone, correctly: it
is not this ticket's defect.

But a cited regression must have exited zero, at `harness/gates.py:1001`, so this ticket could not
advance out of tdd while it failed, and the repair lived on `claude/SEEN-114-rules-from-findings`,
which is parked waiting for this ticket to pass its triage. A circular wait. Broken by cherry-picking
SEEN-114's own commit onto this branch with `git cherry-pick -x`, so the restore reaches `main` with a
one-point ticket instead of a parked one, and SEEN-114 keeps the commit it was asked to carry: git
drops the duplicate when that branch rebases. Record 14 is the regression at 1,449 tests green.

#### F1, and what it says about the test that missed it

The first review returned this ticket on a fourth reader nobody had counted:
`harness/triage.py:517` computed `named_in_solution=path in named`, an exact
comparison against the plan's own file list, and `file_subject` writes that straight
into the state Jev reads as "Named by the solution record" when it decides what the
reviewer must read. So the one answer this ticket set out to give had a fourth
dissenter, in the place where the wrong answer does the most harm, and it is
plausibly part of why SEEN-114's criteria 2 and 5 scored 0.36 and 0.41: every file
under `apps` and `packages` was shown to Jev as named by no slice.

The ticket's own pre-work said there were exactly three readers. It was wrong, and
the reason is the instrument: the grep that found them looked for `not in`, and this
one is positive. `NoSecondReaderTest` had the same blind spot, so the test that was
criterion 1's evidence could not see the case criterion 1 is about.

Widening the regex to both directions then matched three lines that are not
comparisons at all, `for position in named` among them, because a regex cannot tell
a membership test from a loop. So the instrument is now the syntax tree: an
`ast.Compare` with `In` or `NotIn` whose comparator is a plan's file list, over the
four modules that read a plan. A `for` clause is a `comprehension.iter` and never a
Compare, so the loops drop out by construction rather than by exception. Two tests
hold the instrument itself: one proving it sees a positive comparison, which is the
blind spot F1 came through, and one proving a loop over the plan is not one.

### The second review, and why the instrument needed fixing twice

Two findings, both about the instrument and neither about the fix, which the round
confirmed correct. The module allowlist was the first: four names, so a fifth reader
born in any other module would have passed silently. The second was the comparator,
matched against its unparsed text, so `entry.get('files') or []` is the same question
asked with a default and was not recognised.

Both are fixed at the root rather than patched. The allowlist existed only because
`named` meant a plan's files in four modules and a set of agent names in `kpi.py`,
and one name for two things is what made a list of modules look necessary; that
variable is now `agent_names`, which is what it holds, and the scope is every module
of the package, the only scope that cannot go out of date. The comparator is matched
as a subtree of the Compare node, so a wrapped expression is seen.

Four tests now hold the instrument itself, one per blind spot a review had to find:
it sees a positive comparison, it does not see a loop, it scans every module, and it
sees a wrapped comparator. That is the shape of this whole ticket repeated at one
remove: a question with one answer, and an instrument that can actually tell whether
there is one.

### Three rounds, and the instrument settled on the third

Round three, which Ruud called and which SEEN-118 reserves to the founder, attested
all three earlier findings resolved and raised one more, F4, against the fix it had
just confirmed: walking every node of a comparator traded a false negative for a
false positive, because `named` and `planned` are reused across this package for the
unmet criteria of a return and the points a sprint planned, so a membership test
against either would have been reported as a second reader.

The round's own suggestion was to rename the colliding identifiers, which is the
pattern this ticket used twice already and is right in principle; it is also a rename
across half a dozen modules and wider than this ticket owns. The narrower repair is to
ask what the comparator **is** rather than what it contains: the plan's file list, or
an `or` whose alternatives include it, which is the only wrapping that leaves it still
being the list. A tuple of two unrelated things is not.

So the instrument took three passes and each was a review's: an exact match that
missed a wrapped comparator, a walk that caught it and flagged unrelated words, and a
structural test that does neither. Six tests hold it now, one per property a round had
to find: it sees a positive comparison, it does not see a loop, it scans every module,
it sees a wrapped comparator, it does not see a word a plan shares with something
else, and it finds nothing in the tree as it stands.

Worth recording plainly: the F4 fix is the one change in this ticket no independent
context has read. It is ten lines in a test's helper, rated low by the round that
raised it, in the safe direction of error, not triggered anywhere in the tree, and
pinned by a test that fails without it. A fourth round for that would cost more than
it could find, and SEEN-118's rule is that the third round is where the list goes to
the founder.

## Carried forward

The policy question is open and is the founder's: whether the solution gate should refuse a plan whose
slices name overlapping directories. This ticket made the readers agree, which was the defect. Whether
a plan should be allowed to name `packages` at all is a different change, to a different gate, and
SEEN-114's record 107 argues both sides of it.

What this ticket is finally judged by is not in its own journal and cannot be: SEEN-114's
`slice_files` check passing against its own diff once this merges and that branch rebases. It was
written into criterion 5 and is amended out of it above, because a criterion that can only be
evidenced on another branch holds a ticket at the gate for ever; the triage answered it unevidenced at
0.10 before any model read anything, which is the triage doing its job. The measurement is the first
thing SEEN-114's next session does, and it belongs in that ticket's journal.

The triage also named two files changed by no slice and no changes entry, `CLAUDE.md` and
`docs/tickets/README.md`, which are where a new ticket is registered and which the plan did not think
to name. The plan is amended rather than the check argued with. Worth saying what that signal is: on
SEEN-114 the same check named about forty files and was wrong every time, because it compared paths
exactly against a plan naming directories. Here it named two and was right about both. That is this
ticket's fix working, measured on the ticket that made it.
