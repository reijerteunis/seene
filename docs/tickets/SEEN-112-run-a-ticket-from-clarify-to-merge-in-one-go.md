---
id: SEEN-112
title: "Run a ticket from clarify to merge in one go, asking only what it cannot decide"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-105, SEEN-107, SEEN-111]
status: review
---
# SEEN-112: Run a ticket from clarify to merge in one go, asking only what it cannot decide

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | review |

## Description

A ticket with nothing to ask should not need five sessions and four handoff packs. Today it does: the session cap says work one slice, write the pack and stop, and that cap exists because a session's own context is what runs out, not because the ticket needs a break. Once each slice is worked by `seen-implementer` and the review by `seen-reviewer`, the orchestrating session holds the pack, the ticket and the gate answers and nothing else, so its context no longer grows with the work and the reason to stop at a slice boundary goes with it. That is why this ticket waits on SEEN-111: the delegation has to be binding before it can be relied on to keep the orchestrator small.

What the run must get right is not the loop, which is thin. It is the stopping. A run that retries a refused gate, invents an answer to a question only a person can settle, or ticks a criterion its own evidence does not carry is worse than five sessions, because it produces a journal that reads as if the work were done. So every stop is named in advance: a gate that refuses, a Jev question that does not clear, a failed check, red CI, and a second return on the same slice, which is where a replan stops being a correction and starts being thrashing. Each stop reports the stage, the record number and the one command to resume from, and none of them is retried.

Questions are asked once. A ticket whose clarify record would carry an open question stops there, asks every question it has in one batch, records the answer as a note and carries on when `clarified` clears the threshold, which is the harness's existing definition of a sufficient answer and is better than a new one. A second stop for something the first batch could have carried is a defect of the run and is named as one in its summary, because the cost of a question is the person's attention and two halves of one question cost more than the whole. SEEN-100's distinction holds throughout: an unknowable is recorded as the decision to proceed with the observation that will settle it, and is never asked as though a person could answer it.

Two things this ticket has to settle rather than assume, and the second is not the implementer's to decide.

The merge is outward-facing and irreversible in the way nothing else in the procedure is. The default is that the run reaches a green `verify-merge` with the receipt in the pull request body and stops there, one command short, because that is the last point at which a person can still read what was built. Merging without being asked is the one thing an end-to-end run must not quietly acquire.

And `docs/harness/workflow.md` opens by saying the harness is a procedure and not an orchestrator: it runs inside the current assistant session and launches no other model. A command that spawned the implementer and the reviewer itself would contradict that line. The honest shapes are that the run is a skill the assistant follows while the harness says unambiguously what the next action and its exact arguments are, or that the principle is amended on purpose. The first keeps the harness a program anyone can read; the second is a founder decision and is recorded as one, with the line it changes quoted. Either way it is settled at the solution stage and written down before any code.

A human-executor ticket is refused at the start. SEEN-110 is the worked example: three of its five criteria wait on an observation in an interactive Codex session, and a run that started it would arrive at a verification whose only way forward is to invent the fact the criterion exists to establish.

## Acceptance criteria

- [ ] A code ticket with no open questions runs from clarify to a green `verify-delivery` without a stop, in one orchestrating session whose own spending stays inside one slice's budget, with every slice's RED and GREEN recorded by `seen-implementer` and the review by `seen-reviewer`, proven on a real ticket of at most 2 points and evidenced by its journal and its budget figures
- [x] A ticket with an unknown a person must settle stops once, asks every question it has in a single batch, records the answer as a note, and continues to the end when `clarified` clears; a second stop for a question the first batch could have carried is reported as a defect of the run and named in its summary
- [x] Every stop is one of the named ones and none is retried: a gate that refuses, a Jev question that does not clear, a failed check, red CI, and a second return on the same slice, each reporting the stage, the record number and the one command to resume from
- [x] The merge is never taken without authorisation: the run stops at a green `verify-merge` with the receipt in the pull request body, and merges only when that was authorised for this ticket and the authorisation is in the journal with who gave it and when
- [x] A ticket whose executor is `human` is refused at the start, naming the criteria only a person can settle, rather than run into a verification it would have to invent
- [x] Whether the harness may launch a model is settled at the solution stage and recorded either way, quoting the line of `docs/harness/workflow.md` it stands on, and the run's shape follows that decision rather than the other way round
- [x] The run widens nothing: no criterion is ticked that its own evidence does not carry, and the summary lists every criterion left unmet with what each is waiting on

## Amendment

**27 September 2026: two amendments were made to criterion 1 and both are withdrawn. It stands as
written.** Recorded here rather than erased, because a criterion that was edited twice and put back is
a thing a later reader should be able to see.

The first amendment moved the proof on a real ticket of at most 2 points to a follow-up ticket, because
no such ticket is available: SEEN-032 is the only 2-point ticket at `todo` and it waits on SEEN-008.
The second narrowed the criterion to the fixture walk and this journal's own delegation, because the
criterion named a green `verify-delivery` and a review by `seen-reviewer`, neither of which exists when
the review triage judges it.

The review triage refused criterion 1 all three times, at 0.96, 0.94 and 0.90, and it was right every
time. The reason is not the wording and it is not missing evidence. Criterion 1 asserts a run that goes
the whole way **without a stop**, and this ticket's own journal is the counterexample: three stops,
three returns and a session more than three times over the one-slice budget. No arrangement of words
makes a journal full of stops into evidence for a stopless run, which is exactly why the criterion said
the proof belongs on another ticket. The amendments were attempts to make a self-referential claim pass
on the one ticket that cannot carry it.

So the criterion is restored and its proof moves where it always belonged: Ruud decided on 27 September
2026 that the loop is proven end to end on SEEN-008, from a branch off this one, with the single
deviation recorded that SEEN-008 is 5 points and four slices rather than at most 2. SEEN-112 cites that
run's journal and budget figures as criterion 1's evidence.

## Outcome

`harness run <ticket>` answers one question from the journal, the ticket file and the thresholds: what is
the next action, exactly. It returns the stage, the kind (`command`, `spawn`, `ask`, `stop` or `merge`),
runnable argv beginning `python3 harness/run.py`, the agent to spawn and that agent's task text where there
is one, why this action, and the named stops. It launches nothing, which is Ruud's decision at record 4
holding in the code: the implementer's task text is the one `routing.for_slice` already stored and the
reviewer's is the one the triage record already carries, so the loop composes what exists. The opening of
the Principles section of `docs/harness/workflow.md` is quoted and unchanged.

Six named stops live in `[run] stops`, where a person reviews an addition as a diff: `gate_refused`,
`question_open`, `check_failed`, `ci_red`, `second_return` and `awaiting_authorisation`. Each reports the
stage, the record number it points at and one resume argv, and `halt()` writes at most one stop record per
reason and record, which is what "none is retried" means in a journal. Two of the five conditions the
criterion names were found to be undetected once someone looked: `question_open` was reading the clarify
draft's list rather than a recorded decision below its threshold, and nothing read CI at all. Both are read
from the journal and from GitHub's own completed check runs now, and `DETECTED` and `DECLARED` say in the
module which conditions the loop finds and which a session must declare.

`harness authorise <ticket> --merge --by <who>` writes the `authorisation` record the `merge` action sits
behind. The run offers `verify-merge` until it is green, then stops at `awaiting_authorisation`, then offers
the merge only once that record exists, and it never invokes a merge itself.

**Criterion 1 is not met, and the summary says what each part of it waits on**, which is criterion 7 applied
to this ticket rather than to some other. It was amended twice on 27 September and both amendments were
withdrawn; the `## Amendment` section keeps that history. The review triage refused it three times, at 0.96,
0.94 and 0.90, and was right every time. What the proof run on SEEN-008 established and what it did not:

- **Met**: every slice's RED and GREEN was recorded by `seen-implementer`, declaring `--model` and
  `--agent` on each check, and the review was `seen-reviewer` in a context that had written nothing. The
  run reached review from clarify **with no stop**, driven by the loop naming each action and its arguments.
- **Not met, waiting on a ticket whose review passes first time**: "to a green `verify-delivery` without a
  stop". SEEN-008's review returned it on three high findings, each reproduced by execution, so it has not
  reached delivery. A returned ticket is the harness working, not the loop failing, but it is not the run
  the criterion describes.
- **Not met, waiting on a fresh session working one ticket**: "one orchestrating session whose own spending
  stays inside one slice's budget". This session spent 474,936 output tokens against a budget of 60,000,
  with 535,622 more across twelve subagents. It hand-orchestrated two tickets, five returns and four
  question batches. The loop is what removes the reason to stop at a slice boundary; it cannot retrofit a
  budget onto the session that built it.
- **Not met, waiting on a ticket of at most 2 points**: SEEN-008 is 5 points and four slices. No ticket of
  at most 2 points was available: SEEN-032 is the only one at `todo` and it waits on SEEN-008 itself.

So criterion 1 needs one thing this ticket could not provide: a small ticket, worked by the loop in a fresh
session, whose review passes first time. The loop exists and is proven as far as review; the run the
criterion describes has not yet happened end to end.

What the proof run bought that reading the code had not. Four defects in the harness, three fixed here and
one recorded: the guard allowed every path once a ticket's last slice was done, which is exactly the rework
phase after a return; the guard's exact path match refused a new file inside a directory a slice names, so
all three of SEEN-008's slices wrote their migration through a shell the hook does not see; and the coverage
gate's own command never enabled coverage, so it had been comparing a summary file dated 23 September
against the baseline and the control it advertises had not held. Record 48 carries `summary_written` for the
first time. The fourth, recorded and not fixed, is that `handoff.plan_accepted_at` moves on a replan so the
pack and the guard read "0 of 3 done" for slices that are green and committed.

Five returns, and the record should be read with that in front of it. Three were criterion 1 refusing to be
evidenced, one was the review of SEEN-008, and one was this deliberate amendment; none was a defect in
delivered code. The ticket is 5 points against a 3-point estimate. Two question batches to Ruud were
necessary and two more were defects of my own analysis, named at records 22, 31 and 41: the question to ask
at record 4 was not what proves criterion 1, but what happens to it given that the gate refuses an
unevidenced criterion, and that was answerable then.

## Slices

1. The loop over the five stages with every stop named and none retried, and the refusal of a human-executor ticket (2 points)
2. The single question batch, the resume once `clarified` clears, and the merge authorisation recorded in the journal (1 point)

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff
- [SEEN-111](SEEN-111-hold-a-slice-to-the-context-it-was-routed-to.md): Hold a slice to the context it was routed to, and price it before it is worked

## Blocks

- [SEEN-113](SEEN-113-let-a-tdd-record-cite-the-evidence-a-return.md): Let a tdd record cite the evidence a return did not invalidate
- [SEEN-119](SEEN-119-independent-slices-run-in-parallel-worktrees.md): Independent slices run in parallel worktrees

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The harness as built: [docs/harness/workflow.md](../harness/workflow.md), whose opening paragraph is the line criterion six is about, and whose session section is what this ticket changes the reason for
- SEEN-100, for the difference between a question that is open and one nobody can answer, which is what decides whether the run asks or records
- SEEN-110, the worked example of a ticket a run must refuse: three of its five criteria wait on an interactive Codex session
- `harness/cli.py`, `NEXT_COMMAND` and `status --brief`: what the harness already says about the next action, and the starting point for saying it unambiguously
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
