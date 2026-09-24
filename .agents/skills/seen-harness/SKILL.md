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
| review | The diff read against the criteria, findings with a failure scenario each | `check --phase qa`, `advance` or `return` |
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

A RED that did not fail. A slice citing a check from another attempt. A solution record with no slice
plan, a slice over 2 points or a plan over 4. Coverage that fell. A record or a handoff pack carrying
the value of an environment variable. A delivery whose checks are not green on the commit it
attests. A merge where anything but the journal, the reports, the coverage baseline or the graph
changed after the receipt. Each refusal says what to do next.

## The worked example

`docs/harness/history/SEEN-092/` is this document's own ticket, start to receipt. Read it beside
`docs/harness/workflow.md`, which carries the reasoning this file leaves out.
