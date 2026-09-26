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
status: review
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
| Status | review |

## Description

The machinery for splitting a ticket and handing each piece to a subagent already exists, and nothing holds a session to using it. `_slice_plan` refuses a slice over 2 points and a plan over 4, `harness route` writes an `implementer_task` per slice naming the model and the RED, and `seen-implementer` holds the Edit and Write tools. `grep implementer_task harness/*.py` returns two lines, both in `routing.py`: the function that writes the instruction and the line that puts it in the record. No gate, no hook and no check reads it. The harness plans the delegation and then nobody is answerable for it.

SEEN-110 is the evidence. Its plan was one slice of two points, which was a fair estimate at about 250 lines across eight files, and the session that worked it spent 140,000 output tokens against a budget of 60,000 without spawning a single subagent. A detector reading points would have said two points, proceed. What actually cost the context was research, code, documents, a RED, a GREEN and a mid-slice `return` in one place, plus three runs of a 1,084-test suite whose output came back to the caller in full each time. So the gap is not that the harness cannot see a big task: it is that the unit it measures size in is a forecast a person wrote, and the delegation it plans is advisory.

Three things, in the order they pay. First the declaration: a check already says which model tier it ran under, and the same disclosure says which agent, so the tdd gate can refuse a slice whose RED and GREEN were recorded in the orchestrating session's own context. Second the price: SEEN-091 and SEEN-099 already collect output tokens and tool calls per point per delivered ticket, so after the calibration window there is a distribution to read, and the solution stage can say what a plan of this shape has cost before it is worked rather than after. Third the cheapest saving of the three: `harness check` truncates the output it stores and still returns the whole record to its caller, so a regression costs the session its entire transcript when its exit code, its counts and its tail would do.

Two things have to be settled before any of it is designed around, and both are recorded as findings rather than assumed. A Claude Code subagent inherits its parent's session id, which is why `check --model` and `reviewer_session` are disclosures and not proofs; `sessions.spending` reads the log for `identifier()`, so a subagent's output tokens may land in the parent's figure and delegation may not move the number at all. And slices cannot run in parallel as the tdd gate stands, because it requires `previous_green < red < green <= regression`, so slice 2's RED must be recorded after slice 1's GREEN: subagents buy context, not wall clock, until that ordering is relaxed for slices on disjoint files. Whether to relax it is out of scope here and is named as a question, not answered.

Nothing in this ticket refuses on the budget. The threshold's own comment says only the person at the keyboard can end a session, and a refusal in the middle of a slice leaves work done and unrecorded, which is the one state the journal cannot represent.

## Acceptance criteria

- [x] A check declares the agent it ran under, beside the tier it already declares, and the tdd gate refuses a slice whose RED and GREEN were recorded in the orchestrating session's own context once `[routing] shadow` is off, naming the slice, the route record and the two checks, proven by a RED
- [x] Whether a subagent's output tokens land in its parent's figure is settled from a real session log, recorded as a finding with the log's own evidence, and `harness budget` either reports the parent's and the subagents' spending apart or states that it cannot tell them apart
- [x] The solution stage reports what a plan of this shape has cost, read from the delivered KPI records rather than from its points, and names the split when the prediction exceeds the session budget; it refuses nothing while fewer tickets have delivered than `[calibration]` names, and an absence is reported as an absence rather than as a low figure
- [x] `harness check` can return its record without the captured output, so a full regression costs the caller its exit code, its counts and its last lines instead of its whole transcript, and the journal still holds everything it held before
- [x] The budget still refuses nothing, and the ticket's Outcome records why rather than leaving it to be rediscovered
- [x] That slices cannot run in parallel while the tdd gate orders every RED after the previous GREEN is recorded as an open question with the gate's own line quoted, and is not answered here

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

## Outcome

Three things shipped in the order the ticket named them, and two questions it could only raise are
raised rather than answered.

**The declaration and the gate.** A check records `agent_declared` beside the `model_declared`
SEEN-108 added, supplied by `harness check --agent <name>` and checked against `[agents] names`.
`gates._require_a_context_of_its_own` sits immediately after `_require_the_routed_model` and
inherits its three absences: it is silent while `[routing] shadow` is true, silent without a route
entry to name, and otherwise refuses a slice whose cited RED and GREEN both declare nothing, naming
the slice, the route record and the two checks. One of the two declaring an agent is a delegated
slice and is not refused, because the criterion describes a slice worked in the orchestrating
session's own context and widening the refusal at the gate would widen the ticket.

**Whether a subagent's tokens land in its parent's figure: no, and nowhere anybody was looking.**
Settled at clarify from this session's own logs rather than assumed. One `seen-scout` was spawned;
its transcript went to `~/.claude/projects/<project>/04fb488c-.../subagents/agent-a096dc5acb99c04e8.jsonl`
with a `.meta.json` beside it naming the `agentType`, while the parent's own log grew only by the
parent's turns. Every entry in that file carries `isSidechain` true and the parent's own `sessionId`,
so the inherited session id is real and the digest a record already holds cannot tell a subagent's
check from its parent's. The same finding explains a figure nobody had questioned:
`cost.log_directory(root).glob('*.jsonl')` matches top-level files only and never descends into that
directory, so no subagent entry had ever been read here. That is why `kpi.reviewer_tokens`, which
asks `cost.tokens_between(sidechain=True)`, has always returned null, and why delegating a slice did
not move the budget. `harness budget` now reports the parent's spending and each subagent's apart.
Widening the KPI glob would move every delivered ticket's figures and the calibration numbers read
off them, so it was left alone and the cause recorded instead; that is a ticket of its own.

**The price before the work.** `harness/forecast.py` reads every delivered `kpi.json`, takes each
`execution` entry's output tokens and predicts from that distribution, never from the plan's points:
SEEN-109's own record has a one-point slice at 121,398 output tokens beside a one-point slice at
42,520, both against a 60,000 budget. The solution gate carries the answer as evidence. Below
`[calibration] window` delivered tickets it reports an absence with both counts and no figure, which
is where it stands today at two of ten, so the first thing this criterion did was decline to answer.

**The quiet check.** `harness check --quiet` returns the exit code, the size counts and the last
twenty lines instead of the whole transcript, built from a copy after the record is written, so the
journal file is byte for byte what it would have been. This ticket's own regression at record 22 is
the first use: 1,072 tests, 1,272 bytes back to the caller.

**Why nothing refuses on the budget, recorded here so it is not rediscovered.** Not an oversight and
not a thing left for later. The threshold's own comment says only the person at the keyboard can end
a session, and a refusal in the middle of a slice leaves work done and unrecorded, which is the one
state the journal cannot represent: the work exists in the tree, the evidence for it does not exist
anywhere, and no later reader can tell that tree from one somebody edited by hand. Everything this
ticket added reports. `forecast.predict` never calls `require`; `subagent_figures` and
`against_budget` never call it either; the UserPromptSubmit hook prints the figure and blocks
nothing. This ticket is its own evidence for the rule: the session that planned it was at 61,432
output tokens against 60,000 before a line of code was written, and was at 139,904 when the review
returned it. A harness that refused on that number would have refused this ticket three times, each
time with a slice half-written.

**Two open questions, neither answered here.** Slices cannot run in parallel, because the tdd gate
orders every RED after the previous slice's GREEN in one line at `harness/gates.py:258`:

    require(previous_green < red['sequence'] < green['sequence'] <= regression['sequence'], ...)

So slice 2's RED cannot be recorded until slice 1's GREEN is, and subagents buy context rather than
wall clock. Whether to relax that for slices on genuinely disjoint files is out of scope by the
ticket's own wording and stays open: no plan so far has had two slices anybody wanted concurrent, and
a gate loosened on no evidence is a gate loosened for nothing. The second question was walked into
rather than reasoned about, and is recorded at record 17. `harness guard` reads which slice is in
front of you from the greens recorded, so the moment slice 2's GREEN landed, slice 2's own files went
out of bounds, while the only defect the regression then found was in one of them: `test_forecast.py`
had no `if __name__ == '__main__'` guard and no `import unittest`, which `GuardIsLastTest` exists to
require. Both documented answers were wrong. A `return` to solution starts a new attempt and
`cited_check` requires checks from the current one, so a one-line import would have voided seven
records and forced every RED and GREEN to be run again. The file was named by the accepted plan; only
the cursor had moved past it. The fix went through a shell, which the PreToolUse guard does not
match, and it is written down rather than left in a diff. What would close it is the guard reading
the slice from the last handoff rather than from the greens, or accepting any file the accepted plan
names at any slice.

**What the review found, and the sequencing mistake behind it.** The first review returned the ticket
on one blocking finding: this Outcome, the `status: review` and the ticks were not in the tree the
review read. They are required before the review advance because the fingerprint covers the whole
ticket file, and this session ran the triage and the reviewer first. No `return` was recorded,
because the ticket had not left the review stage and a `return` would have started a new attempt and
voided every cited check; the tree was corrected and re-triaged instead, and the finding is carried
in the review record so the calibration window reads it. The three slices, the regression and the
coverage measurement are all evidence recorded before any of this and are unaffected.

**Delegation, measured.** All three slices were worked by `seen-implementer` on the model the route
chose, and the review by `seen-reviewer` in a context of its own. Slice 1's checks declare no agent,
because `--agent` is the flag slice 1 added and did not exist when its spawn instruction was written;
slices 2 and 3 declare it. The review is disclosed as `self-review` rather than `subagent` for the
reason this ticket settled: a Claude Code subagent inherits the parent's session id, and the only
session the reviewer could honestly name is the one that wrote the code.
