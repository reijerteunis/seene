---
id: SEEN-103
title: "Declare non-code mode at the solution stage, not after it"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086]
status: done
---
# SEEN-103: Declare non-code mode at the solution stage, not after it

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

The solution template carries `tests_first` as a non-empty list, so the solution gate requires it of
every ticket. Non-code mode, which declares that a ticket has no executable behaviour to prove, is
declared one stage later at tdd. A registration, verification, research or policy ticket therefore has
to write tests it will never run in order to reach the stage where it says it has no tests.

SEEN-102 is the first non-code ticket the harness has seen. SEEN-086 was exempt as the bootstrap and
every ticket since has been code, so the hole has been there since the harness was built and could not
show until now. Sprint 0 alone has six human tickets waiting behind it.

Move the declaration: the solution template carries `mode`, defaulting to `code`, and the solution gate
requires `tests_first` only when the mode is `code`. The tdd stage keeps its own `mode` field, and the
two must agree, because a ticket that plans no tests and then records a code TDD has changed its mind
without saying so.

## Acceptance criteria

- [x] The solution template carries mode, and the gate rejects a mode that is neither code nor non-code
- [x] A solution record in non-code mode advances with tests_first empty
- [x] A solution record in code mode still refuses without tests_first, naming the field
- [x] A tdd record whose mode differs from the solution record's is refused, naming both
- [x] Every solution record already written stays valid: the absence of mode reads as code

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Opened on 24 September 2026 from SEEN-102's solution stage, recorded in that ticket's journal at record 5.
- The third ticket in this epic to park behind a gate that was wrong rather than a record that was, after SEEN-096 parked for SEEN-100 and again for SEEN-101.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

`mode` is declared at the solution stage, shipping as `code` in the template so the common case is the
default and a ticket with no executable behaviour is the one that has to say something. The solution
gate drops `tests_first` from the fields it requires when the mode is `non-code`, which is the same
move the tdd stage makes with a whole second template, at one field's cost instead of two templates to
keep in step.

The tdd gate gains one refusal: a mode that disagrees with the solution record's. A ticket that plans
no tests and then records a code TDD has changed its mind, and the refusal says to write a note and
return rather than to change the word at the next gate.

**Two things the tests found that the design had wrong.** `latest_evidence` returning nothing was
being read as a record saying `code`, so a tdd gate evaluated with no solution record refused every
non-code ticket; absent is not a claim about mode, and it is now told apart from silent. And the
criterion about records written before the field existed was tested as though a new record could omit
`mode`: it cannot, because the template asks for it, and what stays valid is the nine already written,
which `mode_of` reads as code. The test says that instead.

Adding a required template field broke 55 tests in one run, all of them fixtures that predate the
field. That is the field doing its job. The shared `solution_evidence` fixture declares `code`, and the
one non-code coverage test got its own class with its own setUp, because a setUp shared with code
tickets cannot declare non-code.

**Nothing else is hiding behind this.** All six templates were read against their four gates at
record 3: `tests_first` is the only field a gate required before the ticket could say it did not
apply. `slices` has the same shape and was already solved by the non-code template.

This is the third gate in this epic to be wrong rather than the record it was judging, after SEEN-100
and SEEN-101, and the first one found by a ticket that was not writing code.
