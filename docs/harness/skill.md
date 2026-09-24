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
| solution | The files, the tests to write first, the rollback, the risks | `draft`, fill it in, `advance` |
| tdd | A red that failed for the stated reason, a green, a regression, coverage | `check --phase red\|green\|regression`, `coverage`, `advance` |
| review | The diff read against the criteria, findings with a failure scenario each | `check --phase qa`, `advance` or `return` |
| deliver | The branch pushed, CI green on that commit, the receipt written | `verify-delivery`, then `verify-merge` before merging |

`return` sends a ticket back to an earlier stage and counts as rework. `reopen` voids a receipt before
the work is merged, when a defect is found after delivery. Both are recorded with a reason.

## Four rules you cannot infer

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

codegraph's watcher runs inside the MCP server your session starts, not as a daemon, so the harness
syncs the index before every codegraph query and records that it did. In a shell with no assistant
attached, the index is as old as the last sync until something asks.

## What the harness will refuse

A RED that did not fail. A slice citing a check from another attempt. Coverage that fell. A record
carrying the value of an environment variable. A delivery whose checks are not green on the commit it
attests. A merge where anything but the journal, the reports, the coverage baseline or the graph
changed after the receipt. Each refusal says what to do next.

## The worked example

`docs/harness/history/SEEN-092/` is this document's own ticket, start to receipt. Read it beside
`docs/harness/workflow.md`, which carries the reasoning this file leaves out.
