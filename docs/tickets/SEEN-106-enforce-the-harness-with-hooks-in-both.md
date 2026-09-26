---
id: SEEN-106
title: "Enforce the harness with hooks in both assistants, generated from one source"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-092]
status: review
---
# SEEN-106: Enforce the harness with hooks in both assistants, generated from one source

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

The skill tells a session what to do; a hook makes the assistant unable to do otherwise, and both assistants run the same lifecycle events with the same JSON shape (Claude Code in .claude/settings.json, Codex in .codex/hooks.json). harness/hooks.json is the single source; harness sync generates both copies, keeping the graphify hook-guard entries and the permissions, and doctor reports drift. The hooks, each a harness command reading the hook's JSON on stdin: SessionStart runs harness status --brief for the ticket of the current branch and injects it as additionalContext, so a session starts from the handoff pack rather than from the PRD; UserPromptSubmit runs harness budget and injects a warning once the session is over budget; PreToolUse on Edit, Write and MultiEdit runs harness guard <path>, which blocks with a reason (exit 2) an edit to code while the ticket is at clarify or solution, an edit on a branch that is not the ticket's, and an edit outside the files the accepted slice names, and allows the ticket file and .harness-drafts/ at every stage; PreCompact runs harness handoff --auto so the pack exists before the context is summarised; SubagentStop for seen-reviewer validates the findings JSON and drafts the review record; Stop runs harness doctor --quick for the ticket. The decision that matters: enforcement lives in harness commands with tests and fixtures, and the hook files are generated, never edited by hand.

## Acceptance criteria

- [x] harness sync generates the hooks section of .claude/settings.json and .codex/hooks.json from harness/hooks.json, preserving the graphify hooks and the permissions, and doctor reports a hand edit of either copy
- [x] harness guard blocks an edit to packages/ or apps/ while the ticket is at clarify or solution, an edit on a non-ticket branch and an edit outside the accepted slice's files, each with a reason, and allows the ticket file and .harness-drafts/ at every stage, proven with hook-input fixtures for both assistants
- [x] SessionStart injects the handoff pack and UserPromptSubmit injects a budget warning once the session is over budget, proven with fixtures
- [x] PreCompact writes the handoff pack before compaction, and a test proves it is written when the trigger is auto
- [ ] The hooks run in a Codex session: /hooks lists them and a blocked edit is refused there too, recorded as a verification in the journal

## Outcome

Delivered across two attempts. Attempt 1 built the three pieces, attempt 2 fixed the eight
findings its review returned. Four of the five criteria are met on recorded evidence; the fifth
needs a live Codex session and is the reason this ticket is still at review.

`harness/hooks.json` is the one source for six lifecycle events. `harness/hooks.py` renders each
assistant's entries from it, merges them into `.claude/settings.json` and `.codex/hooks.json`,
and compares only what the harness owns, so graphify's two read guards, repowise's three context
loaders and the whole permissions block survive a sync untouched. Ownership is the command
prefix rather than a marker key, because neither assistant documents its hook schema as
extensible. The consequence worth keeping: a hand edit to a command stops the entry being ours,
so `drift` compares both ways, reporting an edited command as missing and a harness-looking
entry no source names as unnamed rather than disowning either in silence.

`harness/guard.py` is one pure decision with four rules and no fifth, reached either by
`harness guard <path>` typed by a person or by the PreToolUse hook. Absence allows and says why:
a guard that refused on a missing journal would refuse the first edit of every ticket, and that
absence is already refused by the gate that comes next. `GuardRefusal` maps to exit 2, which is
how both assistants spell deny, while every other `HarnessError` stays at 1.

`harness hook <event> --client` reads the payload on stdin and prints that client's envelope. It
calls the pack, the budget, the guard, the handoff and the quick self-check, and adds no rule of
its own: an event that needed new judgement would be a rule invented by a hook, which is the one
thing a hook must never be. The Codex envelope is verified rather than assumed. codex-cli 0.156.1
carries a JSON Schema for every hook event, and the binary prints twenty-three of them across the
twelve events it names; they give the same payload fields and the same response shape Claude Code
documents, so the two envelopes are one envelope here.

### What the two attempts taught, which is the part worth keeping

The review found a defect neither the author nor the implementer saw, and it was created by
treating a partly generated file as a generated one. `generated_paths()` answered two different
questions with one list: for the slice check, is this generated so a change in it is not
unplanned; for the fingerprint, is this generated so a change in it is not evidence. Those
coincide for a wholly generated copy and diverge exactly where one is partly generated, which
`.claude/settings.json` is. Excluding it from the fingerprint meant the permission allowlist and
`defaultMode` could be widened between a triage and a review advance with nothing refusing it,
and `hooks.drift` cannot see them because nothing generates them. The sets are now separate, and
the test for it walks a project to review, widens a permission and advances: before the fix it
passed, which is the scenario executed rather than its shape asserted.

The second was a reason rather than a behaviour. Attempt 1 withheld PreCompact and SubagentStop
from Codex because Codex documented neither; attempt 1's own slice 3 then disproved that from the
schemas and recorded it, leaving a decision standing on a reason known false, with a passing test
holding it in place. The review's judgement was that one of the two had to be corrected before
merge, and the behaviour was the one to correct: once the schemas are the evidence there is no
reason left to write. Both events now go to both clients.

Three smaller repairs came from the same review. An automatic pack written by PreCompact was read
by `kpi._closes` as a slice boundary and overwrote a declared boundary's figures, which are what
SEEN-109's calibration decides the routes on; the fix is in the reader, because inferring a
boundary mid-slice is correct for the pack. `_subagent_stop` refused an absent payload field as
though the answer had carried no review record, failing closed where every other handler in the
module fails open. And criterion 2's fixtures reached only one of the guard's rules through a
payload; the other four are now covered, and a rename is asserted on both sides. That last one
produced no RED, because every case passed at first run: it is evidence added, not a defect
fixed, and inventing a failure to record would have been a falsification.

### What is not done, and what cannot be

Criterion 5 is unmet. It asks what an interactive Codex session prints for `/hooks`, whether a
guarded edit is refused there, and whether `.agents/settings.json` is read by anything. Every
question the Codex binary could answer is answered and recorded; the session itself has not run,
and nothing this repository can do settles whether Codex loads a project-level `.codex/hooks.json`.
That verification is Ruud's, and the ticket does not leave review without it.

Two things are recorded rather than repaired. The journal holds no slice boundary between
attempt 1's slices 2 and 3, because all three ran in one session, so `kpi.slice_windows` charges
both to slice 2 and the two-point slice 3 reads as having cost nothing. A boundary that did not
happen cannot be written afterwards: the journal is append-only and backdating one is the
falsification ADR 0001 exists to prevent. Its cause is fixed for every later ticket by the F3
change, and attempt 2 wrote a pack at its own boundary. Separately, `CLAUDE.md`'s command list
was missing `handoff`, `budget`, `route` and `review` before this ticket and still is; only the
two commands this ticket added were put in, because the other four are not this ticket's defect
and it is already at eight points of plan against a three-point estimate.

Which is the honest closing note: two attempts, eight points planned, nine mechanisms behind five
criteria. The hooks were two tickets, and the evidence for that is the two attempts rather than
an argument.

## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
