---
id: SEEN-117
title: "The spec session writes the RED; the implementer cannot touch it"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-105, SEEN-106, SEEN-111]
status: todo
priority: P0
---
# SEEN-117: The spec session writes the RED; the implementer cannot touch it

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P0 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

When the same context writes the failing test and then makes it pass, the test bends toward the implementation, and the review has to read both to know whether anything was proven. Split them. A seen-spec subagent (fresh context, the slice plan and the criteria as its task, Write on test files only) writes the failing tests each slice's RED names, with the reason each must fail; the implementer subagent then runs with harness guard refusing any edit to those files. The review reads the spec against the criteria and the diff against the spec, and a finding of the kind the spec should have caught goes to the spec, not the implementation. The decision that matters: the RED is a contract written by a session that does not know how the code will be written, which is the only way a RED can be evidence.

## Acceptance criteria

- [ ] harness/agents/ carries seen-spec and harness sync generates both assistants' copies, with Write limited to the test paths the slice names
- [ ] The spec subagent writes the failing tests for a slice before the implementer is spawned, and the tdd gate refuses an implementer check whose RED was written in the implementer's session
- [ ] harness guard refuses an implementer edit to a spec file, with the reason, proven with a hook-input fixture
- [ ] The review record separates spec findings from implementation findings, and the weekly report counts both
- [ ] One Sprint 0 ticket worked this way shows fewer returns than the sprint median, recorded in the report

## Depends on

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-106](SEEN-106-enforce-the-harness-with-hooks-in-both.md): Enforce the harness with hooks in both assistants, generated from one source
- [SEEN-111](SEEN-111-hold-a-slice-to-the-context-it-was-routed-to.md): Hold a slice to the context it was routed to, and price it before it is worked

## Blocks

- [SEEN-137](SEEN-137-one-worked-example-per-acceptance-criterion.md): One worked example per acceptance criterion before the solution stage, so the RED is a transcription

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
