---
id: SEEN-111
title: "Hold a slice to the context it was routed to, and price it before it is worked"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-105, SEEN-108]
status: doing
---
# SEEN-111: Hold a slice to the context it was routed to, and price it before it is worked

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

The machinery for splitting a ticket and handing each piece to a subagent already exists, and nothing holds a session to using it. `_slice_plan` refuses a slice over 2 points and a plan over 4, `harness route` writes an `implementer_task` per slice naming the model and the RED, and `seen-implementer` holds the Edit and Write tools. `grep implementer_task harness/*.py` returns two lines, both in `routing.py`: the function that writes the instruction and the line that puts it in the record. No gate, no hook and no check reads it. The harness plans the delegation and then nobody is answerable for it.

SEEN-110 is the evidence. Its plan was one slice of two points, which was a fair estimate at about 250 lines across eight files, and the session that worked it spent 140,000 output tokens against a budget of 60,000 without spawning a single subagent. A detector reading points would have said two points, proceed. What actually cost the context was research, code, documents, a RED, a GREEN and a mid-slice `return` in one place, plus three runs of a 1,084-test suite whose output came back to the caller in full each time. So the gap is not that the harness cannot see a big task: it is that the unit it measures size in is a forecast a person wrote, and the delegation it plans is advisory.

Three things, in the order they pay. First the declaration: a check already says which model tier it ran under, and the same disclosure says which agent, so the tdd gate can refuse a slice whose RED and GREEN were recorded in the orchestrating session's own context. Second the price: SEEN-091 and SEEN-099 already collect output tokens and tool calls per point per delivered ticket, so after the calibration window there is a distribution to read, and the solution stage can say what a plan of this shape has cost before it is worked rather than after. Third the cheapest saving of the three: `harness check` truncates the output it stores and still returns the whole record to its caller, so a regression costs the session its entire transcript when its exit code, its counts and its tail would do.

Two things have to be settled before any of it is designed around, and both are recorded as findings rather than assumed. A Claude Code subagent inherits its parent's session id, which is why `check --model` and `reviewer_session` are disclosures and not proofs; `sessions.spending` reads the log for `identifier()`, so a subagent's output tokens may land in the parent's figure and delegation may not move the number at all. And slices cannot run in parallel as the tdd gate stands, because it requires `previous_green < red < green <= regression`, so slice 2's RED must be recorded after slice 1's GREEN: subagents buy context, not wall clock, until that ordering is relaxed for slices on disjoint files. Whether to relax it is out of scope here and is named as a question, not answered.

Nothing in this ticket refuses on the budget. The threshold's own comment says only the person at the keyboard can end a session, and a refusal in the middle of a slice leaves work done and unrecorded, which is the one state the journal cannot represent.

## Acceptance criteria

- [ ] A check declares the agent it ran under, beside the tier it already declares, and the tdd gate refuses a slice whose RED and GREEN were recorded in the orchestrating session's own context once `[routing] shadow` is off, naming the slice, the route record and the two checks, proven by a RED
- [ ] Whether a subagent's output tokens land in its parent's figure is settled from a real session log, recorded as a finding with the log's own evidence, and `harness budget` either reports the parent's and the subagents' spending apart or states that it cannot tell them apart
- [ ] The solution stage reports what a plan of this shape has cost, read from the delivered KPI records rather than from its points, and names the split when the prediction exceeds the session budget; it refuses nothing while fewer tickets have delivered than `[calibration]` names, and an absence is reported as an absence rather than as a low figure
- [ ] `harness check` can return its record without the captured output, so a full regression costs the caller its exit code, its counts and its last lines instead of its whole transcript, and the journal still holds everything it held before
- [ ] The budget still refuses nothing, and the ticket's Outcome records why rather than leaving it to be rediscovered
- [ ] That slices cannot run in parallel while the tdd gate orders every RED after the previous GREEN is recorded as an open question with the gate's own line quoted, and is not answered here

## Slices

1. The agent declaration and the gate that holds a slice to a context of its own, with the subagent-token question settled from a real log first, because the gate's message depends on which figure is readable (1 point)
2. The predicted cost at the solution stage, read from the delivered KPI records, reporting and never refusing (1 point)
3. The quiet check, and the two documents that describe all of it (1 point)

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-108](SEEN-108-route-each-slice-to-a-model-and-an-effort-at.md): Route each slice to a model and an effort at solution, by rule first and by Jev second

## Blocks

- [SEEN-112](SEEN-112-run-a-ticket-from-clarify-to-merge-in-one-go.md): Run a ticket from clarify to merge in one go, asking only what it cannot decide

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- The harness as built: [docs/harness/workflow.md](../harness/workflow.md), for the session cap, the three agents and the context budget
- SEEN-110's journal, `docs/harness/history/SEEN-110/`: the session this ticket came out of, where the plan was two points and the spend was 140,000 against 60,000, and record 8 for the return a mid-slice replan cost
- `harness/thresholds.toml`, `[session]`: `max_points_per_slice`, `max_slices_per_ticket`, `output_token_budget` and the comment saying why nothing refuses on the last of them
- `harness/routing.py:272`, `implementer_task`: the instruction the route writes and nothing reads
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
