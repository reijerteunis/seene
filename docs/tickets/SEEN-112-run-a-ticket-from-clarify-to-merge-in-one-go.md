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
status: doing
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
| Status | doing |

## Description

A ticket with nothing to ask should not need five sessions and four handoff packs. Today it does: the session cap says work one slice, write the pack and stop, and that cap exists because a session's own context is what runs out, not because the ticket needs a break. Once each slice is worked by `seen-implementer` and the review by `seen-reviewer`, the orchestrating session holds the pack, the ticket and the gate answers and nothing else, so its context no longer grows with the work and the reason to stop at a slice boundary goes with it. That is why this ticket waits on SEEN-111: the delegation has to be binding before it can be relied on to keep the orchestrator small.

What the run must get right is not the loop, which is thin. It is the stopping. A run that retries a refused gate, invents an answer to a question only a person can settle, or ticks a criterion its own evidence does not carry is worse than five sessions, because it produces a journal that reads as if the work were done. So every stop is named in advance: a gate that refuses, a Jev question that does not clear, a failed check, red CI, and a second return on the same slice, which is where a replan stops being a correction and starts being thrashing. Each stop reports the stage, the record number and the one command to resume from, and none of them is retried.

Questions are asked once. A ticket whose clarify record would carry an open question stops there, asks every question it has in one batch, records the answer as a note and carries on when `clarified` clears the threshold, which is the harness's existing definition of a sufficient answer and is better than a new one. A second stop for something the first batch could have carried is a defect of the run and is named as one in its summary, because the cost of a question is the person's attention and two halves of one question cost more than the whole. SEEN-100's distinction holds throughout: an unknowable is recorded as the decision to proceed with the observation that will settle it, and is never asked as though a person could answer it.

Two things this ticket has to settle rather than assume, and the second is not the implementer's to decide.

The merge is outward-facing and irreversible in the way nothing else in the procedure is. The default is that the run reaches a green `verify-merge` with the receipt in the pull request body and stops there, one command short, because that is the last point at which a person can still read what was built. Merging without being asked is the one thing an end-to-end run must not quietly acquire.

And `docs/harness/workflow.md` opens by saying the harness is a procedure and not an orchestrator: it runs inside the current assistant session and launches no other model. A command that spawned the implementer and the reviewer itself would contradict that line. The honest shapes are that the run is a skill the assistant follows while the harness says unambiguously what the next action and its exact arguments are, or that the principle is amended on purpose. The first keeps the harness a program anyone can read; the second is a founder decision and is recorded as one, with the line it changes quoted. Either way it is settled at the solution stage and written down before any code.

A human-executor ticket is refused at the start. SEEN-110 is the worked example: three of its five criteria wait on an observation in an interactive Codex session, and a run that started it would arrive at a verification whose only way forward is to invent the fact the criterion exists to establish.

## Acceptance criteria

- [ ] A code ticket with no open questions runs from clarify to a green `verify-delivery` without a stop, with every slice's RED and GREEN recorded by `seen-implementer` and the review by `seen-reviewer`, proven over a fixture journal driven from clarify to the receipt and evidenced by this ticket's own journal and budget figures (amended 27 September 2026, see `## Amendment`)
- [ ] A ticket with an unknown a person must settle stops once, asks every question it has in a single batch, records the answer as a note, and continues to the end when `clarified` clears; a second stop for a question the first batch could have carried is reported as a defect of the run and named in its summary
- [ ] Every stop is one of the named ones and none is retried: a gate that refuses, a Jev question that does not clear, a failed check, red CI, and a second return on the same slice, each reporting the stage, the record number and the one command to resume from
- [ ] The merge is never taken without authorisation: the run stops at a green `verify-merge` with the receipt in the pull request body, and merges only when that was authorised for this ticket and the authorisation is in the journal with who gave it and when
- [ ] A ticket whose executor is `human` is refused at the start, naming the criteria only a person can settle, rather than run into a verification it would have to invent
- [ ] Whether the harness may launch a model is settled at the solution stage and recorded either way, quoting the line of `docs/harness/workflow.md` it stands on, and the run's shape follows that decision rather than the other way round
- [ ] The run widens nothing: no criterion is ticked that its own evidence does not carry, and the summary lists every criterion left unmet with what each is waiting on

## Amendment

**27 September 2026, on Ruud's authority, recorded at journal record 22.**

Criterion 1 was written as:

> A code ticket with no open questions runs from clarify to a green `verify-delivery` without a stop,
> in one orchestrating session whose own spending stays inside one slice's budget, with every slice's
> RED and GREEN recorded by `seen-implementer` and the review by `seen-reviewer`, proven on a real
> ticket of at most 2 points and evidenced by its journal and its budget figures

It is narrowed to the proof this ticket can carry: the loop driven from clarify to the receipt over a
fixture journal, with both slices worked by `seen-implementer` and this ticket's own budget figures on
record. Two things move out of it, and neither is dropped:

1. **The proof on a real code ticket of at most 2 points** moves to a follow-up ticket, because no
   such ticket is available. SEEN-032 is the only 2-point ticket still at `todo` and it waits on
   SEEN-008, which is 5 points and not started. Proving the run on a 5-point ticket instead would
   evidence a criterion nobody wrote.
2. **The orchestrating session staying inside one slice's budget** moves with it, because it can only
   be measured on that run. This session's own figures are recorded and they are over: hand
   orchestration is what the loop exists to remove, and measuring it on a session that predates the
   loop would measure the wrong thing.

Why it was amended rather than left unmet: the ticket's own review triage refused an unevidenced
criterion at record 20 and returned the ticket to tdd, as it is built to. Delivering with criterion 1
unticked was the intention at record 4 and the harness does not allow it, so the choice was between
amending the criterion, parking the branch for weeks, or proving the run on the wrong ticket. The
first is the only one that leaves the record true. Nothing else in the criteria changes.

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
