---
id: SEEN-105
title: "Give the scout and the reviewer their own context as subagents in both assistants"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-104, SEEN-092, SEEN-098]
status: review
---
# SEEN-105: Give the scout and the reviewer their own context as subagents in both assistants

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

Two readers fill a session: the research at clarify and solution (graph answers, PRD sections, the files a change touches) and the review, which has to read the diff, the journal and the criteria. Both move into subagents with a context window of their own that return a bounded answer to the session working the ticket. harness/agents/ holds one source per agent: seen-scout (read-only tools plus the three graph MCP servers; returns a brief of at most 400 words with file paths, the answers it found and the questions it could not answer), seen-reviewer (fresh context, no Edit or Write; reads the diff, the journal and the criteria and returns findings in the review template's JSON with file, line, claim and failure scenario), and seen-implementer (optional: one slice per invocation, the handoff pack as its task, Edit, Write and the test runner). harness sync generates .claude/agents/<name>.md (name, description, tools, model, permissionMode, omitClaudeMd) and .codex/agents/<name>.toml (name, description, developer_instructions, sandbox_mode, model) from that source, and doctor reports drift the way it does for the skill copies. In Claude Code the skill invokes them by name (@agent-seen-reviewer; the scout can also run as a skill with context: fork and agent: Explore); in Codex the skill says to spawn them explicitly, because Codex spawns a subagent only when asked, and [agents] max_depth stays at 1. The review record carries the reviewer's session id and the review gate refuses a review from the implementer's own session. The decision that matters: a subagent is a context boundary, not independence by itself; the review by the other assistant stays required for tickets that change an agent action or touch billing.

## Acceptance criteria

- [x] harness sync writes .claude/agents/seen-scout.md, seen-reviewer.md and .codex/agents/seen-scout.toml, seen-reviewer.toml from harness/agents/, and doctor reports a copy edited by hand
- [x] The scout returns a brief of at most 400 words for a Sprint 0 ticket and harness note records it with the session id it came from; a brief over the limit is refused with the count
- [x] The review gate refuses a review record whose reviewer session id equals the implementer's, and accepts one from a subagent or from the other assistant
- [x] Tickets that change an agent action or touch billing still require a review from the other assistant, enforced at the review gate and proven with a fixture
- [x] (as amended) One ticket worked with the scout and the reviewer shows the main session's output tokens per point below the SEEN-099 baseline, recorded in the sprint report

## Amendments

- **24 September 2026, Ruud: criterion 5 is amended.** SEEN-105 delivers the
  measurement, the attribution and the report row; the figure itself is read from
  the sprint 0 report once the first ticket worked with both agents from its first
  session has delivered, which is SEEN-106. The reason is in the journal at records
  8 and 15 and was raised as F3 by the review at note 39: this ticket's own first
  session was spent before either agent existed, so no figure it could produce
  would be the figure the criterion asks for. The measurement, not the number, is
  what this ticket owed.


## Depends on

- [SEEN-104](SEEN-104-cap-a-session-at-one-slice-the-slice-plan-the.md): Cap a session at one slice: the slice plan, the budget and the handoff pack
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.

## Outcome

Delivered on 24 September 2026 across four attempts. The four planned slices and
the handoff defect found while working slice 1 were proved in attempt 2, and one
rework slice in each of attempts 3 and 4 after the two review rounds, which
`kpi.slices` counts as seven proven against four planned, with three returns
counted as rework. Two sessions, both of them the same one by the digest: the
clarify session that opened the ticket and the session that worked it.

**What was built.** `harness/agents.py` holds what each agent may do and
`harness/agents/<name>.md` holds what each is told; `sync` renders
`.claude/agents/<name>.md` with the camel-case frontmatter Claude Code reads and
`.codex/agents/<name>.toml` with the keys Codex reads, and `doctor` reports a copy
edited by hand, a missing copy, a missing source and an agent file no source
generates. `harness note --from <agent>` records a brief with its agent and word
count and refuses one over the 400-word cap in `[agents]` with both numbers. The
review gate takes a third disclosure, `subagent`, with `reviewer_session` beside
it, and refuses a session that wrote any record on the ticket or the session
running the advance; where a ticket touches billing or the policy gate the review
still comes from the other assistant, named as one of the tools in `[actors]`.
`kpi.measure` carries `subagents` and the sprint report divides those tickets'
output tokens per point on their own beside the SEEN-099 baseline.

**What the work settled that the ticket had assumed.** A Claude Code subagent
inherits its parent's `CLAUDE_CODE_SESSION_ID`, observed at record 7 with the
digest identical in both and `AI_AGENT` set in both. The harness therefore cannot
derive a reviewer's context, and every place this ticket says session id means a
declared value. The gate refuses what it can see and says in its own code that it
cannot detect a value typed to pass; the control that stands there is the
cross-tool review.

**Evidence.** Record 26 is a real 381-word brief from `seen-scout` against
SEEN-009. Notes 39 and 47 are two real reviews by `seen-reviewer`, each in a
context of its own, and both returned the ticket: eleven findings the first time,
three of them high, and eight the second, four of them medium. F2 would have
shipped a gate that refuses the review it demands, because the other assistant
records a `return` when it sends work back and the rule read that as authorship.
F1 would have sent every resuming session to the wrong slice. G1 and G2 were
introduced by the fix to F2 and caught by the second pass: reading authorship from
the actor's role turned an over-refusal into an under-refusal, and the mirror image
had been left standing at the `independent` rule, where a second tool merely having
recorded anything counted as independence. Authorship is now read from the stage a
record was written at, which is where the work happened rather than what the actor
called itself.

That the reviewer this ticket built found, on this ticket, two holes in the control
the ticket exists to strengthen, and then found the holes the first round's fixes
opened, is the strongest evidence the ticket has that the agents pay for
themselves. It is also the reason the review of a ticket that changes an agent
action or touches billing still goes to the other assistant: both rounds were the
same model reading the same repository, and neither round would have caught a
mistake both rounds share.

**What is unverified, and by whom.** The Codex keys (`name`, `description`,
`developer_instructions`, `sandbox_mode`, `model`) come from this ticket's own text
and have never been read by a Codex release: no Codex session has run on this
repository. `doctor` checks that a copy matches its source, not that Codex accepts
it, and the first Codex session settles it. `[agents] max_depth = 1` lives in
`.codex/config.toml`, which this repository deliberately does not track, so the
skill tells a session to set it rather than asserting it is set.

**The limitation this ticket does not close.** The reviewer holds Bash, because it
cannot read a diff without it, and Claude Code has no read-only Bash. On that side
the reviewer is held to reading by its instructions and by holding no Edit and no
Write, and nothing refuses a write it makes through a shell; `sandbox_mode` closes
that on the Codex side only. It is F9 of the first review, accepted rather than
fixed, and it belongs to SEEN-106, which puts hooks in front of both assistants.

**Two things found while working, fixed here.** `handoff` counted slices from
accepted greens, so slice 1's second green after a correction sent the pack to
slice 3 with slice 2 unworked: `--slice-done` lets the session that worked the
slice say so, the record carries the inference beside the declaration, and
`status --brief` reads the declaration back. And `reject_placeholders` compared a
record against examples for fields `for_mode` had dropped, which would have refused
a non-code record for leaving `tests_first` alone.

**Criterion 5** is amended above, on Ruud's authority, recorded in the journal at
note 50 with the option he chose and the two he did not. The measurement and the
attribution are delivered and tested, and `[context] agents_available_from` keeps
this ticket out of the row its own amendment points at, because a ticket that
installed a tool was not worked with it. The figure is read from the sprint 0
report when SEEN-106 delivers.
