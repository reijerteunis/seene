# Shared Seene ticket workflow

This is the canonical procedure for both Claude Code and Codex. The generated tool skills only
enter this workflow. Use the five stages for implementation requests; ordinary questions and
read-only investigations do not create a run. The founder requested these stages and persistent
decision history on 5 September 2026 (D-014).

## Before starting or resuming

1. Read the [company and product context](../agents/context.md), the
   [working agreement](../agents/working-agreement.md), the requested ticket, the relevant
   product and technical decisions, and actual dependency results. The ticket file defines
   scope; it is not permission to spend, deploy or access customer data.
2. Run `python3 harness/run.py doctor`. It verifies that the two generated skill copies still
   match [skill.md](skill.md), that the templates parse, that documentation links resolve and
   that every existing journal still verifies. Fix what it reports before working.
3. Inspect the Seene Git root, branch, status and configured remote. Preserve unrelated
   changes. Start on a dedicated branch such as `codex/SEENE-001-foundation`; this naming
   convention also works when Claude Code performs the work. Do not work in Quorum. On a fresh
   clone, use the established baseline; do not invent a base branch if the repository has no
   agreed one.
4. Use one writer per working directory. A second tool may resume after the first has stopped.
   The command lock protects journal writes, not simultaneous code editing. Separate concurrent
   tickets need separate Git worktrees and an integration review; this version does not manage
   those worktrees.
5. Run `python3 harness/run.py list` and `status <ticket>` to find an existing run. If it
   exists, continue at the recorded stage and attempt; `status` reports the stage, attempt,
   branch, evidence template and next step. Read all unresolved decisions, review findings and
   handoff notes with `history <ticket>`. Starting again with the same ID is refused. If the run
   is delivered, create a follow-up ticket rather than rewriting the completed record.
6. A new run requires an initial Git commit. Resolve the ticket path from the current index and
   run:

```sh
python3 harness/run.py start SEENE-001 --ticket docs/tickets/first-delivery/SEENE-001-project-foundation.md --actor codex
```

Use actor values such as `claude`, `codex`, `codex:self-review` or a human's supplied name.
Labels are self-reported, not verified identities. The start event snapshots the ticket and the
base commit.

## How to preserve evidence

Each stage ends by passing completed evidence to `advance`. Get the right template with:

```sh
python3 harness/run.py draft SEENE-001
```

This copies the current stage's [template](templates/) into the Git-ignored `.harness-drafts/`
and lists the check events recorded in the current stage and attempt, so you can fill in real
sequence numbers instead of guessing them. Fill the draft with actual evidence: the gate refuses
any value left as template example text, and refuses check numbers that do not match the
required phase, stage and attempt.

Use `note` immediately for a substantive decision, a user answer, a blocked question, a
discovered dependency, a changed assumption or a handoff. Supply a UTF-8 Markdown file:

```sh
python3 harness/run.py note SEENE-001 --file .harness-drafts/decision.md --actor codex
```

Use the [decision and handoff template](templates/note.md). Record the decision, concise
rationale, alternatives, evidence, owner or source of authority and implications. Record
observable facts and useful reasoning summaries, not private model reasoning or a full chat
transcript. An unresolved question belongs in a note before waiting for the user. Never
manufacture an answer or treat elapsed time as consent.

Every stage ends with a local Git checkpoint containing the run history and the ticket's
relevant changes. Also checkpoint before handing work to another tool or leaving a blocked
stage. Use explicit paths with `git add -- <paths>` and inspect the staged diff. Conventional
commit subjects include the ticket ID, for example `docs(SEENE-001): record technical solution`.
Code and test commits may be split further; do not rewrite prior decision commits to make
history appear cleaner.

Do not commit secrets, customer traffic samples, credentials, environment files or private chat
exports. `check` records a command and up to 64 KiB of combined output; use only commands and
fixtures safe to retain in Git. Larger output is explicitly marked truncated. Link to restricted
evidence by an approved identifier when needed; the committed journal should contain a safe
summary. Never put secrets on a command line.

## 1. Ticket gathering, understanding and grilling

Restate the desired behavior and who benefits. Inspect related code, existing contracts and
actual dependency outputs. Identify acceptance criteria, in and out of scope, constraints and
failure cases. Challenge contradictions and hidden assumptions about identity, data
availability, tenant isolation or user intent where relevant to the ticket.

If material details are unclear, ask focused questions, record answers and their consequences,
and revise the ticket. Do not force a grilling session when the ticket is already clear. Routine
implementation choices within authorised scope can be recorded and resolved autonomously.
Blocking questions require answers before advancing.

Complete [clarify.json](templates/clarify.json). `open_questions` must be empty; deferred
non-blocking topics belong in decisions with a reason. Record dependencies and evidence in the
acceptance or decision text, or in additional fields. Advance, then checkpoint the journal:

```sh
python3 harness/run.py advance SEENE-001 --file .harness-drafts/SEENE-001-clarify.json --actor codex
```

## 2. Technical solution

Research the specific change. Inspect local code first; use current primary sources for
changeable vendor or API claims. Compare viable approaches and choose one with a concise
rationale. Record affected modules, interfaces and data contracts, migration and rollback needs,
permission and evidence boundaries, dependencies and operational risks. For UI work, link the
accepted design or record the written contract used instead.

Translate acceptance into a prioritised behavioral test plan and list the actual commands to
run. TDD applies to executable behavior, including harness changes. A documentation, research or
policy ticket can use the narrow non-code path with an explicit reason and meaningful document
or contract checks; do not invent a failing software test for it.

Complete [solution.json](templates/solution.json), advance and checkpoint. Share material design
decisions with the founder, but do not add an approval ceremony when scope and authority are
already clear. An unresolved product decision returns to stage 1.

## 3. TDD: red, green, refactor

Implement one behavior at a time through its public interface:

1. Write one test for the next acceptance behavior.
2. Run it through `check --phase red`. Inspect the failure and record why it demonstrates the
   missing behavior. A missing executable, timeout, unrelated exception or broken test setup is
   not valid RED evidence; the gate rejects those exit codes. Fix the setup first.
3. Write the smallest implementation that passes that test. Run `check --phase green`.
4. Refactor only while green and rerun the affected tests. Record meaningful refactoring
   decisions using `note`.
5. Repeat for the next behavior; do not write the entire test suite first and all
   implementation afterwards.
6. Run the relevant regression checks against the final tree through `check --phase regression`.
   One invocation may use the project's real test or check script to include tests, lint, type
   checks and build as appropriate. Do not claim a check ran when the command did not execute it.

```sh
python3 harness/run.py check SEENE-001 --phase red --actor codex -- python3 -m unittest discover -s harness/tests -v
python3 harness/run.py check SEENE-001 --phase green --actor codex -- python3 -m unittest discover -s harness/tests -v
python3 harness/run.py check SEENE-001 --phase regression --actor codex -- python3 -m unittest discover -s harness/tests -v
```

These example commands test the harness itself; replace them with the ticket's actual commands.
A failing command returns nonzero while still recording the event. The default timeout is 60
seconds; use `--timeout <seconds>` before `--` when a known check needs longer. Do not use
shell-background jobs; timeout management covers the invoked process and is not a containment
system for arbitrary descendants.

Complete [tdd.json](templates/tdd.json) using actual check event numbers. RED/GREEN pairs must
be ordered within the current attempt and must not overlap. The final regression must pass
without modifying project files, on the current tree. Generated test artifacts must be ignored
appropriately, not hidden merely to evade review. A non-code ticket uses
[non-code.json](templates/non-code.json) and still requires a passing regression or document
check. Advance and checkpoint code, tests, documentation and history.

## 4. QA and code review

Review the full ticket diff against the accepted outcome, not only whether tests pass. Check
failure modes, security and tenant boundaries, observability, unnecessary complexity, migrations
and rollback, documentation and relevant UI behavior. Map acceptance criteria to actual
evidence. State whether this is self-review or an independent reviewer. Switching tools can
provide another review perspective, but no second agent is launched automatically.

Run the appropriate QA commands with `check --phase qa`. Record each finding with its severity,
evidence, expected behavior and resolution. Do not edit implementation during review and then
approve it; route the work first:

| Finding | Return to | Work that must be repeated |
| --- | --- | --- |
| Wrong or incomplete requirement; unanswered product question | `clarify` (1) | Clarification, solution, TDD, review |
| Incorrect interface, architecture, data contract or approach | `solution` (2) | Solution, TDD, review |
| Implementation defect, missed case, failing test, code cleanup | `tdd` (3) | Applicable red/green work, regression, review |

```sh
python3 harness/run.py return SEENE-001 --to solution --reason 'The chosen interface cannot enforce client isolation; see recorded finding R-02' --actor claude
```

First record the findings in a note. The return event records its reason and increases the
attempt number; earlier evidence remains readable but can no longer satisfy a gate. If the same
blocking issue repeats without new evidence, stop the loop, record the blocker and ask the
founder for the missing decision. Do not grind indefinitely or close unresolved findings by
changing their label. A genuinely deferred improvement needs a separate ticket and a recorded
scope decision; defects in current acceptance stay blocking.

Complete [review.json](templates/review.json). All listed findings must be resolved, the verdict
must be pass, acceptance evidence must be supplied, and current QA checks must pass. The command
also rejects any project change since the accepted TDD regression. Advance and checkpoint the
reviewed implementation and the complete history.

## 5. Commit and push to Git

The founder supplied `git@github.com:reijerteunis/seene.git` for Seene. Use configured remote
`origin` only after verifying its URL. Push a dedicated ticket branch with the reviewed code,
tests, tickets, applicable documentation and all run events. Do not force-push, merge or deploy
as part of this stage. Respect any stronger permission requirement of the active tool.

1. Inspect status and the staged diff; commit the relevant files and all journal events. The
   working directory must be clean. Check that no unrelated local commit would be published.
2. Push the branch using `git push -u origin HEAD`. A rejected push is a failure. Investigate
   it; if integrating upstream changes alters the reviewed tree, return to the relevant earlier
   stage and repeat the checks.
3. Complete [delivery.json](templates/delivery.json), then run `advance`. It checks the reviewed
   file fingerprint, clean Git state, tracked journal files and the actual remote branch HEAD.
   Its new event is a delivery receipt for that pushed commit.
4. Commit this receipt, for example `docs(SEENE-001): record delivery receipt`, and push again.
   Only history changed, so this does not invalidate code review.
5. Run the read-only final verification:

```sh
python3 harness/run.py verify-delivery SEENE-001
```

The final check confirms that the receipt is committed, that the recorded delivery commit is an
ancestor of HEAD, and that the remote branch matches the current local commit. It writes no
further receipt, avoiding an endless commit/receipt cycle. Stage `done` alone means the receipt
was recorded; delivery is complete only when this final check succeeds. If the receipt push
fails, fix that push and rerun verification; do not create another delivery event. Summarise
branch, final commit, checks and remaining limits for the founder.

A ticket with missing external acceptance evidence remains open even if useful partial work is
committed. Keep the run in its blocked stage and record why; do not call a partial
implementation delivered.

## Changing the harness itself

The harness is executable behavior, so changes to it follow the same five stages. Edit
[skill.md](skill.md) rather than either generated copy, run `python3 harness/run.py sync`, and
use `python3 -m unittest discover -s harness/tests -v` as the regression command. `doctor` must
pass before review. Instruction content belongs in `docs/agents/`; the root `AGENTS.md` and
`CLAUDE.md` stay index-only so that every session does not load every rule.

## Recovery and limits

`status`, `history`, `list` and `doctor` verify the journal's sequence and hashes. Never edit,
renumber or remove old events to repair a failed gate. A truncated or corrupt event stops the
command; preserve the damaged files, compare against Git and record an explicit recovery before
continuing. A killed command may leave `.harness.lock`; inspect the PID it contains and confirm
no writer is active before removing only that stale lock.

The runner is a workflow assistant, not a security sandbox or an autonomous multi-model
scheduler. Human and agent attestations still need scrutiny, especially the non-code exception
and the reason a RED test failed. Existing Git hooks, permissions and repository protections
still apply. Submodules and nested repositories are not supported in the reviewed-file
fingerprint. Rerun the checks and review their scope after repository configuration changes.
