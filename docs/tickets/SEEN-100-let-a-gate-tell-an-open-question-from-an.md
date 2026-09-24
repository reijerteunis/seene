---
id: SEEN-100
title: "Let a gate tell an open question from an unknowable one"
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
status: doing
---
# SEEN-100: Let a gate tell an open question from an unknowable one

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 1 point (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

The `clarified` question asks whether all material questions in a clarify record are resolved, and it
cannot tell a question nobody has answered from one that cannot be answered until the work is done.
On SEEN-096 the record scored 0.67; adding an honest decision saying that codegraph's documented
behaviour can only be verified by installing it dropped the score to 0.46, a confident no. The honest
record scored worse than the quiet one, which is the wrong incentive to put in front of a session that
is deciding how much to write down.

Every ticket that installs, integrates or verifies something external has this shape. SEEN-088 had it
with the Jev API, SEEN-087 with graphify, SEEN-096 with codegraph, and SEEN-098 will have it with
repowise.

Give the question criteria that make the distinction: a record is clarified when every question that
could be answered by reading, deciding or asking has been, and when anything that can only be settled
by doing the work is named as such with what will settle it. An unknown that is named, with the
observation that will resolve it, is evidence of clarity rather than a hole in it.

Then re-ask the question against three records already written, SEEN-096's, SEEN-088's and SEEN-091's,
and record the scores before and after, so the change is measured rather than assumed.

## Acceptance criteria

- [ ] The clarified question's criteria distinguish a question nobody has answered from one only the work can settle, and say that a named unknown with its resolving observation counts as clarified
- [ ] SEEN-096's clarify record, unchanged, scores higher with the new criteria than the 0.46 it scored with its honest decision included
- [ ] The three re-asked records and their before and after scores are recorded in the journal
- [ ] docs/harness/skill.md tells a session to name what only the work can settle, rather than leaving it out
- [ ] The threshold is not changed: this is a question that was asking the wrong thing, not a bar in the wrong place

## Depends on

- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates

## Blocks

- none

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Opened on 24 September 2026 from SEEN-096's clarify stage, where six attempts read 0.67, 0.68, 0.62, 0.66, 0.67 and 0.46, and the last followed an honest decision about what the ticket could not resolve in advance. Recorded in that ticket's journal at record 6.
- The same calibration pattern as solution_complete in SEEN-006, where the question rather than the threshold was wrong.
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
