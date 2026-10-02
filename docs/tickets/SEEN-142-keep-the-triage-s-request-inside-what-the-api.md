---
id: SEEN-142
title: "Keep the triage's request inside what the API accepts, and say so when it cannot"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-107, SEEN-109]
status: todo
priority: P1
---
# SEEN-142: Keep the triage's request inside what the API accepts, and say so when it cannot

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (the narrowing stops working on exactly the tickets it would save the most on) |

## Description

The review triage's request to Jev grows with the journal it is about, and past a point the API refuses it with `HTTP Error 400: Bad Request`. SEEN-114 crossed that point mid-ticket and the last six of its fourteen triages got no typed answers at all.

Measured on that journal, by rebuilding each triage's own request from the record it wrote:

| triage | request, bytes | journal excerpt, bytes | slices cited | Jev |
|---|---|---|---|---|
| 64 | 139,895 | 17,548 | 4 | answered |
| 171 | 166,501 | 47,865 | 26 | answered |
| 229 | 189,359 | 67,007 | 38 | answered |
| 251 | 198,765 | 76,413 | 44 | 400 |
| 366 | 280,324 | 157,374 | 81 | 400 |

Bytes of the UTF-8 encoding of the request body, which is what a size limit counts, and not a
figure scaled from a rounded one: the first draft of this table carried three numbers derived
from kilobytes and two of them were wrong, which is the defect SEEN-141 is about, met while
writing the ticket that measures something.

Every request up to 189,359 bytes was answered and every one from 198,765 bytes was refused, so the limit is between them, and 192 KiB is 196,608 bytes. The ticket should establish the real number rather than assume that one, but the shape is not in doubt: it is a size, it is a hard edge, and nothing in the harness knows about it.

What grows is one field. `journal_excerpts` carries every accepted tdd record's slices, not the latest record's, and deliberately so: a returned ticket proves slices in each attempt and each still evidences the criterion it was written for, which is the defect SEEN-107 fixed at its own record 75. The caps that exist bound how much each entry carries, `MAX_SLICE_OUTPUTS` at 8 and `EXCERPT_CHARACTERS` at 800, and nothing bounds how many entries there are. SEEN-114 ended with 81, which is 157,374 bytes of a 280,324 byte request. Everything else is flat: the file facts for a 103-file diff are about 19 KB at every triage, and the questions are 110 at every triage after the diff settled.

What the harness does with the refusal is right and is not the defect. `ask_batch` catches the transport failure, `must_answer` is false at the triage, so the answers come back as absences, the record says `HTTPError: HTTP Error 400: Bad Request` in `fallback_reason`, the depth falls closed to full and the reviewer is routed to the strongest model. A judgement nobody made neither sends a ticket back nor narrows what a reviewer reads. The defect is that the request cannot be sent at all, so on a long ticket the triage is a deterministic pass and a fallback, and the narrowing SEEN-107 built never runs.

The consequence is worth stating plainly, because it is not a lost nicety. SEEN-109 calibrates the narrowing over a window of ten delivered tickets and will not turn it on until the figure says it saves more than it misses. A ticket with enough attempts can contribute nothing to that window, and those are the tickets whose reviews are most expensive: SEEN-114 cost six full-depth reviews at 103 files each. So the mechanism meant to make long reviews cheaper is switched off by length.

Four directions for the solution stage, which owns the choice. Cap the entries the way the outputs are capped, keeping the most recent and saying in the state how many were dropped and why, so Jev is told it is reading a window rather than everything. Summarise the older entries to their behaviour and their verdict and keep the full excerpt for the recent ones. Split the request, which is a change to how `ask_batch` reports one answer per key and the thing most likely to grow new failure modes. Or ask the vendor what the limit is and whether it moves, which is not in this repository's hands and is the only option that leaves the growth law alone. Whichever is chosen, two things belong in the ticket regardless: the harness should measure its own request before sending and refuse with a sentence that names the size and the limit rather than discovering it as a `400`, and the limit belongs in `thresholds.toml` where a person can read it.

One small thing to correct while in that module. `jev.post` is documented as "The live call. Unverified: no valid credential has yet reached this API", and that has not been true since the first triage that got an answer: fourteen triage records on SEEN-114 alone carry `source: jev` and `model: jev-1.13.0`, which can only come through that function. A comment that says a path is unexercised, in the module whose failure mode this ticket is about, is the kind of stale note that makes the next reader measure the wrong thing.

## Acceptance criteria

- [ ] The real limit is established by measurement rather than assumed, recorded with how it was found, and written into `harness/thresholds.toml` where a person can read and change it
- [ ] A request larger than that limit is refused before it is sent, with a message naming the size, the limit and the field that grew, and the refusal is recorded as what it is rather than reaching the journal as an `HTTPError`
- [ ] The triage's request stays inside the limit for a journal of at least SEEN-114's size, 81 cited slices and 368 records, with the state saying how much of the journal it carries and how much it left out
- [ ] A triage on a long journal gets typed answers again, proven by rebuilding SEEN-114's own triage request and sending it, or by a fixture journal of that size if the credential is absent
- [ ] `jev.post`'s docstring says what is true of it
- [ ] A RED per criterion, the whole harness suite green, and SEEN-114's fourteen triage records still readable by `calibration.evidence` and by `harness report --calibration`

## Depends on

- SEEN-107: Let Jev settle what the review can settle before a model reads the diff. It built the triage, the state and the fallback, and its record 75 is why the excerpt carries every attempt's slices rather than the latest record's.
- SEEN-109: Calibrate the review triage and the routes on ten tickets before either saves a token. It is the thing this defect quietly starves, because a ticket that cannot be triaged cannot be in the window.

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The measurement: SEEN-114's fourteen triage records, 64 to 366. Each stores the `files`, `criteria` and `deterministic` halves of its own state, so the request it sent can be rebuilt from the journal and weighed, which is how the table above was produced.
- The growth: `journal_excerpts` in `harness/triage.py`, with `MAX_SLICE_OUTPUTS` and `EXCERPT_CHARACTERS` beside it, and `jev.ask_batch` and `jev.post` in `harness/jev.py`.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Carried forward

Whether the route's own requests hit the same edge is not measured here. SEEN-108 asks two questions per unruled slice at the solution stage with a much smaller state, so it is unlikely, and unlikely is not measured. A session working this ticket is in the right place to weigh one route request and say.
