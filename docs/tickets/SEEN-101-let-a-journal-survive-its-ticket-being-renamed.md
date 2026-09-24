---
id: SEEN-101
title: "Let a journal survive its ticket being renamed"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-088]
status: review
---
# SEEN-101: Let a journal survive its ticket being renamed

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | review |

## Description

`cli.state_for` reads the ticket from the path recorded in record 1 and falls back to record 1's
snapshot when that path is gone, silently. A ticket filename carries its title, so renaming a ticket
is ordinary: SEEN-096 was split three ways on 24 September and its file went from
`SEEN-096-add-codegraph-and-repowise-and-assign-each.md` to
`SEEN-096-add-codegraph-and-route-the-graph-command.md`.

Every gate decision on SEEN-096 since that split was made against the pre-split ticket, which asked
for codegraph, repowise and a stage assignment for each context tool, while the record being judged
described codegraph alone. The model reported a record two thirds short of its ticket, which is what
it was looking at. SEEN-096 has now parked twice: once for SEEN-100, once for this.

The ticket id is stable and the filename is not, so resolve the ticket by id, and never pretend to have
read a file that is not there. Which source was used belongs in the state, so a reader of a journal can
tell a judgement made against the live ticket from one made against a snapshot.

This does not overturn SEEN-100's measurement, which sent the same payload under both sets of criteria.
It does mean SEEN-096's absolute scores were never about SEEN-096 as it now stands.

## Acceptance criteria

- [x] state_for reads the ticket at the recorded path when it exists, and records which source it used
- [x] When the recorded path is gone, state_for finds the ticket by id at docs/tickets/<ID>-*.md and records that it did
- [x] The snapshot in record 1 is used only when no ticket file matches, and the state says so rather than passing it off as the ticket
- [x] More than one file matching the id is a refusal naming the candidates, not a choice between them
- [x] SEEN-096's clarify record, unchanged, is re-asked against the ticket that now exists and the score is recorded in this journal
- [x] docs/harness/skill.md's fourth rule tells a session to name an unknowable in decisions, because the code layer requires open_questions to be empty and SEEN-100 shipped advice the gate refuses

The last criterion is a correction to SEEN-100, delivered this morning. Its fourth rule tells a session
to write a named unknown into `open_questions` with a resolution. The code layer of the clarify gate
requires `open_questions` to be empty, so a session following that advice is refused. Found while
writing this ticket's own clarify record, which is the shortest possible feedback loop and the reason
the rule is being fixed here rather than in a ticket of its own.

## Depends on

- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates

## Blocks

- [SEEN-096](SEEN-096-add-codegraph-and-route-the-graph-command.md): Add codegraph and route the graph command to it

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Opened on 24 September 2026 from SEEN-096's solution stage, recorded in that ticket's journal at records 10 and 11.
- The reason state_for reads the live ticket at all is SEEN-088: a ticket is amended during clarify on purpose, and judging a record against the document it was written before is how a resolved question keeps reading as an open one. This ticket finishes that thought for the case where the amendment was a rename.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

`cli.state_for` now resolves a ticket by its id. It reads the recorded path when it is there, finds
`docs/tickets/<ID>-*.md` when it is not, and uses record 1's snapshot only when nothing matches, saying
which of the three it used in a new `ticket_source` field that travels with the payload. Two files
sharing an id is a refusal naming both, but only when the id is what is being resolved by: a recorded
path that still exists is unambiguous whatever else shares its id.

All thirteen journals were checked. One was stale, SEEN-096, whose own three-way split renamed its
file. No other score in this repository was taken against the wrong text.

SEEN-096's clarify record, re-asked unchanged through the fixed code against the ticket that now
exists, scores **0.79** where it scored **0.46** while the gate was reading the pre-split ticket that
asked for three tools. That is 0.33 of measurement error on a record nobody had changed, and it is
still a hundredth short of the 0.8 threshold. Both halves are recorded at record 6: the record was
never as bad as the gate said, and it is not yet good enough either.

The last criterion is a correction to SEEN-100, delivered three hours earlier the same day. Its fourth
rule told a session to write a named unknown into `open_questions` with a resolution; the code layer of
the clarify gate requires `open_questions` to be empty. This ticket's own clarify record was refused
for following that advice, which is as short as a feedback loop gets. The rule now says to write it in
`decisions`, as the decision to proceed with the observation that will settle it, and the record that
followed the corrected rule cleared at 0.85 carrying two named unknowables.
