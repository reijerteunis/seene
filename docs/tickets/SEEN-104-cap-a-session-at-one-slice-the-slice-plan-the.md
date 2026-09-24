---
id: SEEN-104
title: "Cap a session at one slice: the slice plan, the budget and the handoff pack"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-099, SEEN-103, SEEN-091]
status: done
---
# SEEN-104: Cap a session at one slice: the slice plan, the budget and the handoff pack

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

The baseline in docs/harness/reports/context-tools-baseline.json says 40,600 output tokens and 18.5 tool calls per point, so a three-point ticket worked start to receipt in one session is 120,000 output tokens and a context that compacts at least once, and compaction is where evidence quietly becomes summary. Make the slice the unit of context and keep the ticket the unit of delivery (one branch, one pull request, one receipt). harness/thresholds.toml gains a [session] section: max_points_per_slice = 2, max_slices_per_ticket = 4, output_token_budget = 60000, handoff_token_limit = 2000. The solution template gains slices (name, points, files, the RED each must demonstrate); advance from solution refuses a slice above the cap, a plan above the slice cap (the ticket is too big and is split, as SEEN-089 and SEEN-096 were) and a code-mode record without a plan. harness handoff <ticket> writes .harness-drafts/<ticket>-handoff.md (stage, current slice, criteria restated as checks, files, decisions taken, graph answers already recorded, the next command) and appends a handoff record carrying the pack's sha256; harness status --brief prints the pack; harness budget <ticket> reads the current session's output tokens and tool calls from the session logs the way cost.py already does and reports them against the budget. The tdd gate records the session id of every check so the KPI can count sessions per ticket and tokens per slice. The skill then says: PRD and architecture are read once, at clarify; every later session starts from the handoff pack; one slice per session, then handoff and a fresh session. The decision that matters: a fresh context per slice is cheaper than a compacted one, and the handoff pack is the only thing that crosses the boundary.

## Acceptance criteria

- [x] advance from solution refuses a slice over max_points_per_slice and a plan over max_slices_per_ticket, naming the slice, and refuses a code-mode solution record without a slice plan
- [x] harness handoff writes the pack under handoff_token_limit, appends a handoff record carrying the pack's sha256, and status --brief prints it; a test proves the pack carries no environment value
- [x] harness budget reports the current session's output tokens and tool calls against the budget, null rather than zero where no session log exists, and names the slice boundary as the next stop when over budget
- [x] kpi.json carries slices, sessions per ticket and output tokens per slice, and harness report --sprint shows tokens per slice beside tokens per point
- [x] docs/harness/skill.md says one slice per session and that later sessions start from the handoff pack, and sync regenerates both copies

## Depends on

- [SEEN-099](SEEN-099-set-the-context-budget-and-measure-the-tools.md): Set the context budget and measure what the tools changed
- [SEEN-103](SEEN-103-declare-non-code-mode-at-the-solution-stage.md): Declare non-code mode at the solution stage, not after it
- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports

## Blocks

- [SEEN-105](SEEN-105-give-the-scout-and-the-reviewer-their-own.md): Give the scout and the reviewer their own context as subagents in both assistants
- [SEEN-106](SEEN-106-enforce-the-harness-with-hooks-in-both.md): Enforce the harness with hooks in both assistants, generated from one source
- [SEEN-107](SEEN-107-let-jev-settle-what-the-review-can-settle.md): Let Jev settle what the review can settle before a model reads the diff
- [SEEN-108](SEEN-108-route-each-slice-to-a-model-and-an-effort-at.md): Route each slice to a model and an effort at solution, by rule first and by Jev second

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

Three slices, one branch, one receipt, which is the shape the ticket argues for. Slice one put the
four numbers in `harness/thresholds.toml`, the slice plan in the solution template with the two caps
in `gates._slice_plan`, and the session in the record envelope. Slice two built `harness/handoff.py`,
the `handoff` record kind and `status --brief`. Slice three added `harness budget`, the three KPI
figures, the sprint report row and the sixth rule in the skill.

**The session id is a digest, never the value.** `secrets.SECRET_NAME` matches SESSION, so
`journal.append` already refused any record carrying `CLAUDE_CODE_SESSION_ID`, and it was right to.
A record now carries twelve hex characters of its sha256, which is all the KPI needs: the question is
whether two records came from the same session, not what the session is called. The envelope gained
the field rather than the check record, so a session that clarified and handed off without running a
test is counted too, and `HARNESS_VERSION` went to 2, which is the one thing it exists for.

**The ticket measured itself and the figure is the argument.** Worked in one session against its own
advice, `harness budget` reported 214,671 output tokens and 114 tool calls against the 60,000 it had
just written, on the session that wrote it. The handoff pack on this journal came out at 993 tokens
at the second boundary and 1,057 at the third, against a limit of 2,000, so the pack is a fifth of
its allowance with every section present. The clarify stage is where the tokens went: eleven harness
modules read to answer what the ticket touches, and four readings of a gate.

**Three things the tests found that the design had wrong.** The leak test passed a value that did not
appear in the pack, which is how it emerged that the pack carries the ticket file path and that a
test of a refusal has to use a string the artefact really holds. A criterion assertion was pointed at
the ticket file when a criterion restated as a check lives in the clarify record, which is what the
pack should carry and now does. And the skill writes `harness status <ticket> --brief`, so a test
looking for the literal `status --brief` was looking for something no correctly written document
would contain; it asserts the command and the flag.

**Four fixtures broke, not fifty-five.** Adding a required key to `solution.json` failed only
`test_stage_gates.filled_solution`, because SEEN-103's shared `solution_evidence` absorbed the rest.
That is the shared fixture earning its keep one ticket after it was written.

`sessions.figures` landed in slice two rather than slice three, because the handoff record needs this
session's figures and the record is slice two's. The commit says so and the journal shows it.

**The self-review returned the ticket, and the pack found its own defects.** Three, all in the code
written for slice two, all found by reading what the command actually produced rather than by reading
the diff. The first pack written at the review stage told its reader to go and run the regression and
the coverage, which the journal three records above it already showed done: `current_slice` counts
greens and knew nothing about the stage the pack was being read at. `_section` charged the character
budget for an "and N more" line it then discarded when no entry fitted, so `remaining` went negative
and every later section was dropped even where one short line would have fitted, which is how the
graph answers would have vanished from a full pack. And the pack was written with
`Path.write_text(text)` and read back with `read_text()`, both locale-dependent, while its bytes are
compared against the sha256 the journal carries.

The first RED for the fixes passed vacuously, at record 25: it rendered a pack from a journal with no
greens, so the complete-plan branch it meant to test was never reached. Record 26 is the RED that
failed for the stated reason, after the test recorded a green per planned slice first. Both are in the
journal, which is what an append-only record is for.

Attempt 2 is one slice: red 26, green 27, coverage 28, regression 29 over 399 tests. Rework on this
ticket is 1, and it is the self-review's own, which is the argument for the reviewer subagent
SEEN-105 builds rather than against reviewing at all.

**The KPI misreported this ticket, and the receipt was voided before the merge.** The first
delivery wrote `slices: {planned: 3, proven: 1}` into its own `kpi.json`. Three slices were planned
and all three were proved in attempt 1; the 1 was attempt 2's rework slice, because `kpi.slices` read
only the most recent tdd record while `red_before_green` beside it reads every one. The same figure is
the divisor for output tokens per slice, so the cost per slice came out three times too large. Found
by reading the `kpi.json` the delivery had just written, with the pull request open and unmerged.

`harness reopen` voided the receipt at record 35, which is what SEEN-093 built it for: a receipt is
final when the work is merged, not when it is written. Attempt 3 is one slice, red 36 (1 != 2, and
90,000 against 45,000 on the cost) and green 37, coverage 38, regression 39 over 402 tests. Proved now
counts every accepted tdd record, a re-proved slice included, because each one was worked and each one
cost tokens; proven above planned is rework showing up rather than an error, and the docstring says
so. Rework on this ticket is 2, both of them the self-review's own.

The three tickets before this one in the epic each found a gate that was wrong rather than a record.
This one found two figures that were wrong rather than a gate, and both were found by reading what the
new commands actually printed rather than by reading the diff. That is the argument for a harness that
writes its own evidence: the pack and the KPI record were readable the moment they existed.

### Known and deliberately left

Nothing enforces one slice per session. The solution gate refuses a plan that breaks the caps, and
that is the only wall this ticket builds; `budget` reports, the skill asks, and the hooks that act on
either are SEEN-106. A ticket that claimed to cap a session and shipped no wall would be worse than
one that says which.

Output tokens per slice is a division, not an attribution. Two slices worked in one session, which is
what this ticket did three times, cannot be told apart that way. The handoff records carry each
session's own figures from now on, so a later ticket can refine the measure without re-deriving the
data.

Which variable a Codex session exposes its session id in is not known from this machine.
`SESSION_VARIABLES` is an ordered list of one, null is recorded until one of them is set, and the
first Codex session on this repository settles it.

The `clarified` gate held at 0.76 to 0.77 across four readings while the record gained nine
decisions, and Ruud cleared it by recorded override at record 8, with the readings at record 6 and
the reason at record 7. Reading 2 lowered the score by 0.01 for adding four resolutions, which is the
signature SEEN-100 measured and calibrated against; this is the second ticket in the epic to meet it
after SEEN-100's own record.
