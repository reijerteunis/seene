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
status: review
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
| Status | review |
| Priority | P0 (it blocks SEEN-114 at the review stage) |

## Description

Three places in the harness ask whether a slice's plan covers a changed path, and they do not agree. `harness/calibration.py` `_covers` answers it for the route verdict and reads a directory entry: a slice naming `packages` covers `packages/core/db/tables.ts`. `harness/guard.py` answers it for the PreToolUse guard with `if relative not in entry['files']`, and the triage's `_slice_files_check` in `harness/triage.py` answers it with `path not in named`; both compare exactly, so the same slice naming `packages` covers nothing inside it. One question, three readers, two answers, and the looser one is the one a session meets first.

SEEN-114 is what that cost, three ways in one ticket. Its slices named `apps` and `packages` because adopting a formatter rewrites every source file it is pointed at, twenty-six of them, and that is the honest way to say so. One implementer was refused the right to write `rules/fixtures/<slug>/violation.ts` and `packages/core/db/tables.ts` although its plan named `rules/fixtures` and `packages`, and wrote both through a shell, which the PreToolUse guard does not intercept; another met the same refusal, stopped and reported, so the two agents behaved differently because the guard did, not because they did. Then the triage returned the ticket three times saying it could see no evidence for two criteria, with `slice_files` failing in each round and naming about forty files as belonging to no slice: the criteria whose evidence lives in exactly those files are the two Jev would not answer yes for, at 0.36, 0.37 and 0.39 against a threshold it never approached, while every check that proves them was recorded and moved it by hundredths.

The fix is one shared reader rather than three, and it is small. `_covers` is already the right answer and already tested, so it moves to where all three can call it, and `guard.py` and `triage.py` call it. What the ticket must not do is widen it: a slice naming `packages` covering `packages/core/db/tables.ts` is the behaviour `gates.py` has had since SEEN-104, decided there and not here, and the point is that the other two stop disagreeing with it. The guard's refusal message keeps naming the files the slice listed, because a path is what a session can go and look at.

One thing the ticket has to answer rather than assume: whether a slice that names a directory should be allowed at all, or whether the solution gate should refuse a plan whose slices overlap. SEEN-114 would have been a different ticket with narrower slices, and record 107 of its journal argues that `apps` and `packages` was the true description of a formatter adoption. That question is noted and not settled here; this ticket makes the three readers agree, which is the defect, and leaves the policy to the founder.

## Acceptance criteria

- [x] One function answers whether a slice's plan covers a path, called by `harness/calibration.py`, `harness/guard.py` and `harness/triage.py`, with no second implementation of the comparison anywhere in `harness/`. **Amended on 1 October 2026:** the third caller is `calibration.py` and not `gates.py`, which this ticket's own description got wrong. `gates.py` never asks the membership question: it collects a slice's files and hands them to git as a pathspec, and git answers "what changed under these paths", which is a different question answered directory-aware by git's own rules and cannot be asked of a Python predicate. The membership readers were three and are now one, which `NoSecondReaderTest` holds by grepping `harness/*.py` for a hand-written exact comparison against a plan's files.
- [x] `harness guard <path>` allows a write to a file inside a directory the accepted slice names, and still refuses one outside every entry, with the refusal naming the entries
- [x] The triage's `slice_files` check passes when every changed path is inside a directory the plan names, and still fails on a path no entry covers, with the failure naming it
- [x] A test fails before the change for each of the two readers: one proving `harness guard` refused a path inside a named directory, one proving `slice_files` reported such a path as belonging to no slice
- [x] The whole harness suite is green, and SEEN-114's `slice_files` check passes against its own journal and diff, which is the measurement this ticket is judged by

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

### Carried forward

The policy question is open and is the founder's: whether the solution gate should refuse a plan whose
slices name overlapping directories. This ticket made the readers agree, which was the defect. Whether
a plan should be allowed to name `packages` at all is a different change, to a different gate, and
SEEN-114's record 107 argues both sides of it.

What this ticket is finally judged by is not in its own journal: SEEN-114's `slice_files` check passing
against its own diff once this merges and that branch rebases. Until that is measured, criterion 5
rests on this branch's own suite.
