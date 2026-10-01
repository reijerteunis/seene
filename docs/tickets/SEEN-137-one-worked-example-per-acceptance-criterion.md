---
id: SEEN-137
title: "One worked example per acceptance criterion before the solution stage, so the RED is a transcription"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 1
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-088, SEEN-117]
status: todo
priority: P1
---
# SEEN-137: One worked example per acceptance criterion before the solution stage, so the RED is a transcription

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 1 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

The tickets state what must be true and leave the concrete case to whoever writes the test, and that gap is where the clarify rounds and half the returns come from: the spec session guesses an input, the implementer guesses another, the reviewer argues with both. Close it at clarify. The clarify template carries examples, one per acceptance criterion, each a concrete input and the expected output in the domain's own terms (a settlement line with these amounts yields this finding with this euro impact; this policies row and this action are refused with this reason), and the clarify gate refuses a code-mode record with a criterion that has none. Jev's clarified question gets the examples as state, so a criterion whose example does not exercise it scores as unclarified. The spec session from SEEN-117 turns the examples into the RED one for one, and the review reads the tests against the examples rather than against its own reading of the criterion. Examples are data the ticket owns, so a change to one is a change to the ticket, recorded as a note. The decision that matters: an example is the cheapest artefact in the procedure and the only one every stage can read the same way, so it is written first, by the stage that has the founder's attention.

## Acceptance criteria

- [ ] The clarify template carries examples, one per acceptance criterion, with a concrete input and expected output, and the clarify gate refuses a code-mode record with a criterion that has none
- [ ] Jev's clarified question receives the examples as state and its criteria say a criterion without an example that exercises it is unclarified
- [ ] The spec session's RED names the example each failing test transcribes, and the tdd gate refuses a RED whose tests cite no example
- [ ] A change to an example after clarify is recorded as a note on the ticket and shown in status

## Depends on

- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates
- [SEEN-117](SEEN-117-the-spec-session-writes-the-red-the-implementer.md): The spec session writes the RED; the implementer cannot touch it

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
