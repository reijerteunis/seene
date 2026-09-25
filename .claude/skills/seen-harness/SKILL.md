---
name: seen-harness
description: >
  The procedure every Seen ticket goes through: clarify, solution, tdd, review, deliver, with the evidence recorded as it happens. Use when starting, resuming, reviewing or delivering any SEEN ticket, or when asked how the harness works.
---

<!-- Generated from docs/harness/skill.md by `python3 harness/run.py sync`. Do not edit this
     file: `doctor` compares it against the source and refuses when they differ. -->

# The Seen harness

Every ticket goes through five stages, and the evidence is recorded as it happens. The journal is the
source of truth for resuming: a session started by Claude Code and picked up by Codex reads the same
files and continues at the recorded stage.

Run `python3 harness/run.py status <ticket>` first. It says which stage the ticket is in and what to
run next.

## The five stages

| Stage | What it establishes | The command |
|---|---|---|
| clarify | The scope, the acceptance criteria restated as checks, and every material question answered | `draft`, fill it in, `advance` |
| solution | The mode, the files, the tests to write first, the rollback, the risks | `draft`, fill it in, `advance` |
| tdd | A red that failed for the stated reason, a green, a regression, coverage | `check --phase red\|green\|regression`, `coverage`, `handoff` at each slice boundary, `advance` |
| review | The diff read against the criteria, findings with a failure scenario each | `review triage`, `check --phase qa`, `advance` or `return` |
| deliver | The branch pushed, CI green on that commit, the receipt written | `verify-delivery`, then `verify-merge` before merging |

`return` sends a ticket back to an earlier stage and counts as rework. `reopen` voids a receipt before
the work is merged, when a defect is found after delivery. Both are recorded with a reason.

## Six rules you cannot infer

**Evidence lives in `.harness-drafts/`.** `draft` puts it there and `advance` reads it from there.
Anywhere else it is an untracked file in the tree, so submitting it changes the fingerprint review
attested and delivery refuses the ticket for a change the harness itself caused.

**Write the ticket's `## Outcome` before leaving review.** The reviewed-tree fingerprint covers the
ticket file, so an outcome added afterwards makes `verify-delivery` refuse. Only the receipt hash
cannot be written earlier, and it belongs in the pull request body.

**Name what only the work can settle.** A clarify record that leaves out an unknown reads as if there
were none. Write it in `decisions`, as the decision to proceed with the observation that will settle
it, and the stage gate counts it as resolved rather than as a hole. `open_questions` must be empty to
advance: it is the list of what is still open, not the list of what is known to be unknowable.

**A ticket with no behaviour to prove says so at solution.** Set `mode` to `non-code` there and
`tests_first` may be empty; the tdd stage then uses its own template, with a change type of
documentation, research, verification or policy and a reason. The two stages must agree, so changing
your mind means a note and a `return`, not a different word at the next gate. Registrations,
verifications against a live account and policy decisions are all non-code.

**One slice per session.** The ticket is still the unit of delivery, one branch and one receipt, but
the slice is the unit of context. The solution record plans the slices (name, points, files, the RED
each must demonstrate); a slice is at most 2 points and a ticket at most 4, and a plan that needs
more is a ticket to split rather than a session to stretch. Work one slice, then `harness handoff
<ticket>` and stop. The PRD and the architecture are read once, at clarify; every session after that
starts from the pack, which `harness status <ticket> --brief` prints and which carries the stage, the
slice in front of you, the criteria as checks, the decisions taken, the graph answers already
recorded and the next command. `harness budget <ticket>` says where the session stands against its
token budget; nothing refuses on it, because only you can end a session. A fresh context is cheaper
than a compacted one, and compaction is where evidence quietly becomes summary.

**The route is read, never chosen.** Once the solution record is accepted, `harness route <ticket>`
decides per slice which model and which effort implement it, from the plan and the risk answers on
record. Rules first, and a rule is never Jev's to answer: a slice that changes an agent action,
touches billing or the policy gate, does money arithmetic in `packages/core`, carries a migration or
an RLS policy, or touches credentials goes to the strongest model at high effort with no request
made. Everything else is one request carrying `implementation_model` and `implementation_effort`
once per slice, and a slice nobody could answer for goes to the strongest model rather than the
cheapest. The route lands in a `route` record, the handoff pack names what the slice in hand runs
on, and `sync` writes it into `seen-implementer`'s copies for both assistants. **It is read from the
pack and never chosen inside the session**, which is the point: the session that would benefit from
a stronger model is the last one that should be picking it. `[routing] shadow` is true until
SEEN-109's window decides, so today the route is recorded and what a slice actually runs on is
unchanged; with it off, the tdd gate refuses a check recorded under any other model and names both.

**One ticket, one branch.** Every writing command refuses unless the branch is `claude/<ticket>-…` or
`codex/<ticket>-…`, and refuses on `main`. Drifting onto another branch mid-ticket records evidence
about a tree that belongs to different work.

## Asking the graphs

`harness graph <ticket> <mode>` records the answer as a note. Two tools, because they know different
things:

| Mode | Tool | The question |
|---|---|---|
| `impact --about <symbol>` | codegraph | What breaks if I change this |
| `explain --about <symbol>` | codegraph | What is this and what surrounds it |
| `path --from <a> --to <b>` | graphify | How these two ends connect |
| `prs` | graphify | What the open pull requests touch |
| `why --about <thing>` | repowise | Why the code is shaped this way |
| `health` | repowise | Where the code is worst and why |
| `risk` | repowise | How dangerous this change looks against the repo's own past |

codegraph's watcher runs inside the MCP server your session starts, not as a daemon, so the harness
syncs the index before every codegraph query and records that it did. In a shell with no assistant
attached, the index is as old as the last sync until something asks. repowise's index updates when
`repowise update` runs; nothing does it for you.

The `risk` question at the clarify gate is given repowise's change-risk answer as evidence: the
percentile against this repository's own commits, the tests that may break, the missing co-changes. If
repowise is not installed the decision still happens, with the absence recorded as an absence rather
than as a low score.

## The three agents

Two readers and a writer fill a session: the research at clarify and solution,
the review, which has to hold the diff, the journal and the criteria at once,
and the slice itself. Each has a context of its own. The implementer is the one
agent that holds Edit and Write, and the one whose model and effort are not its
own: they are the route's, which is why `sync` rewrites its copies at every
slice boundary and `doctor` compares them.

| Agent | What it is for | What comes back |
|---|---|---|
| `seen-scout` | One scoped question, answered from the graphs. Read-only, no Bash | A brief of at most 400 words: what it could not answer, then the answer with its paths, then what it did not check |
| `seen-reviewer` | The diff against the ticket's criteria and its journal, in a context that did not write the code | Findings in the review record's shape, with a failure scenario each |
| `seen-implementer` | One slice: the RED first, then the code that turns it green | What changed, with the record numbers of the RED and the GREEN |

`harness/agents.py` holds what each agent may do and `harness/agents/<name>.md`
holds what each is told. `sync` generates `.claude/agents/<name>.md` and
`.codex/agents/<name>.toml` from them, and `doctor` reports a copy edited by hand,
exactly as it does for this skill. Claude Code invokes one by name, as
`@agent-seen-scout` or through the Agent tool. Codex spawns a subagent only when it
is told to, so the session says so explicitly. A subagent may not spawn another,
which is `[agents] max_depth = 1` in your own `.codex/config.toml`: this repository
does not track that file, so `doctor` cannot check the setting and the session sets
it on its own machine.

Record a brief with `harness note <ticket> --file <brief> --from seen-scout`. It
refuses a brief over the cap and names the count, and it records the agent, the
word count and the session that wrote the record. The scout cannot write a file,
so the session writes the brief down: what is in the journal is the agent's
content, transcribed.

**Run `harness review triage <ticket>` before spawning the reviewer.** It settles
what the cheaper passes can settle and writes a `triage` record carrying the depth,
the focus set and the task text to hand the subagent; give the reviewer that text
and nothing else. The task names the ticket file and the journal separately from
the focus set, because they are what a review is against and no focus set can hold
them, and it names what pass one only partly settled with the remainder rather
than closing it. A criterion it can see no evidence for returns the ticket to tdd
and refuses, before any model reads the diff. The review record's `read` list is
what the reviewer actually read, and the gate refuses one that does not cover the
focus set; reading more than the focus set is never refused.

**A subagent is a context boundary, not independence by itself.** A review from one
is disclosed as `subagent` and names the `reviewer_session` it came from, and the
gate refuses a session that wrote any record on the ticket, whichever attempt it
worked in. It cannot refuse a value typed to pass, because a Claude Code subagent
inherits its parent's session id, so the declaration is a disclosure and not a
proof. A review disclosed as `independent` is refused when the tool that reviewed
it is a tool that wrote the work, which is read from the records at the clarify,
solution and tdd stages: a reviewer's own `return`, wherever it was written, is not
authorship.

Where a missed defect costs money, the review still comes from the other assistant.
That is a ticket whose solution record answered `touches_billing_or_policy_gate`
yes, **or** one whose frontmatter or clarify record says `changes_agent_action`:
either one needs a second reviewer, the security checklist, and a reviewer or second
reviewer from the other assistant, named as one of `[actors] assistants`. A person
is in `[actors] tools` and is not the other assistant. `harness draft` asks the gate
this question rather than repeating it, so a draft asks for exactly what the gate
will demand.

The reviewer holds Bash, because it cannot read a diff without it, and Claude Code
has no read-only Bash. On that side it is held to reading by its instructions and
by holding no Edit and no Write, and nothing refuses a write it makes through a
shell; `sandbox_mode` closes that on the Codex side only. Enforcing it on both is
SEEN-106, which puts hooks in front of both assistants. Until then, a review that
changed the tree is a review to throw away: the gate records the fingerprint it
attested, and delivery refuses a tree that moved after it.

## The context budget

Three knowledge tools put three sets of tool schemas into every session before a ticket is read, so
what they buy is bounded:

- **One tool call per question.** A second call answering the same question is a question that was
  not asked properly.
- **A codegraph query names a symbol, not a directory.** A directory is a repository-wide read wearing
  a tool's name.
- **No repository-wide read when a graph can answer.** grep over the tree is the last resort, not the
  first move.

Which tool answers when:

| Stage | Tool | What you are asking |
|---|---|---|
| clarify | repowise | What the history says: why this is shaped this way, how healthy it is, how dangerous this change looks |
| solution | repowise, codegraph | What already exists and what depends on it |
| writing code | codegraph | Callers, callees, impact, a symbol's source |
| review | repowise | What this change touches that has broken before, and which tests guard it |
| across code and documents | graphify | How two ends connect, and what the open pull requests touch |

The budget is 60,000 output tokens a session and 2,000 tokens of handoff pack, both in
`harness/thresholds.toml`. Read the ticket file and the pack, and the records the pack names; a
session that opens a module the slice does not touch has already spent what the cap was protecting.

Whether they pay for the context they occupy is measured, not assumed: `harness report --sprint <n>`
carries output tokens and tool calls per point, and output tokens per slice beside them, against the
baseline captured before any of them existed, with the rule for reading it written in
`harness/thresholds.toml` before the numbers arrived.

## What the harness will refuse

A RED that did not fail. A check recorded under a model the route did not choose, once
`[routing] shadow` is off. A slice citing a check from another attempt. A solution record with no slice
plan, a slice over 2 points or a plan over 4. Coverage that fell. A record or a handoff pack carrying
the value of an environment variable. A delivery whose checks are not green on the commit it
attests. A merge where anything but the journal, the reports, the coverage baseline or the graph
changed after the receipt. Each refusal says what to do next.

## The worked example

`docs/harness/history/SEEN-092/` is this document's own ticket, start to receipt. Read it beside
`docs/harness/workflow.md`, which carries the reasoning this file leaves out.
