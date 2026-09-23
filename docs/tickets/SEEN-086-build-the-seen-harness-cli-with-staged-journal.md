---
id: SEEN-086
title: "Build the Seen harness CLI with staged journal and receipts"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 8
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: []
status: doing
---
# SEEN-086: Build the Seen harness CLI with staged journal and receipts

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), sprint gate G0 |
| Estimate | 8 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | doing |

## Description

Create the harness package (`harness/`, Python 3.12 floor, standard library only) with the five stages clarify, solution, tdd, review, deliver, the terminal stage delivered, and the commands doctor, start, status, history, draft, note, check, advance, return, verify-delivery. Records go to `docs/harness/history/<ticket>/NNNN.json` as append-only, hash-chained files; drafts live in the gitignored `.harness-drafts/`. Each stage has a JSON template in `harness/templates/` whose required fields are the stage gate, and thresholds and checklists live in `harness/thresholds.toml`, not in prompts. The decision that matters: the journal is the source of truth for resume, so a session started by Claude Code and resumed by Codex reads the same files and continues at the recorded stage.

This is the first commit of the repository after the Seene project is removed, so it also carries the `.gitignore` and a minimal `.github/workflows/ci.yml` that runs the harness tests and nothing else. SEEN-089 extends that workflow; SEEN-086 creates it.

## Design decisions

Taken on 23 September 2026 before implementation, in a grilling session over this ticket. The glossary they use is `CONTEXT.md`.

- **Three layers, one job each.** The stage template declares which fields must be present, harness code declares the relations between records (ordering, attempt, references), and `harness/thresholds.toml` declares the numbers and vocabularies. A value belongs in the threshold file only when changing it is a legitimate decision that should not require a code change.
- **Every key in a template is required.** A key whose template value is an empty list may stay empty. A submitted value that is still byte-identical to the template's example text counts as missing, not as filled. Required-ness applies to top-level keys; rules about entries inside a list live in code.
- **The word gate is qualified everywhere.** Stage gate for this harness, policy gate for the product, sprint gate for G0 to G7. `policy.toml` is named `thresholds.toml` for the same reason.
- **Records are hashed as file bytes.** `prev_hash` is the sha256 of the previous record file exactly as it sits on disk, so the chain is verifiable with `shasum -a 256` and no harness. A record carries no hash of itself. Writes are byte-deterministic and atomic (temporary file, fsync, `os.link`, unlink).
- **Git is the notary.** The chain catches accidents and makes tampering expensive; `doctor` additionally fails when any record under `docs/harness/history/` has ever been committed as a modification or a deletion, which is the part the chain alone cannot prove.
- **Record envelope, fixed now:** `sequence`, `ticket`, `timestamp`, `harness_version`, `kind`, `stage`, `attempt`, `actor`, `head`, `prev_hash`, `data`. Kinds: start, note, check, advance, return, receipt. Fields later tickets need are written from the first record (`duration_ms` and `output_sha256` on checks, `decisions: []` on advances), because an append-only format cannot be retrofitted. `harness_version` stays at 1 until SEEN-092.
- **`deliver` has no advance out of it.** `verify-delivery` is its stage gate: it appends the receipt record and sets the stage to `delivered`. In SEEN-086 it is offline apart from `git ls-remote` and never requires `gh`. The CI-green check arrives with SEEN-089 and the KPI check with SEEN-091; when they arrive, an unusable `gh` makes delivery refuse, never pass.
- **The receipt attests the tree minus the journal.** The reviewed-tree fingerprint excludes `docs/harness/history/` and `.harness-drafts/`, so the trailing journal-only commit that carries the receipt cannot invalidate the receipt. The receipt's own sha256 goes in the pull request body, which is edited through the API and costs no commit.
- **Non-code mode.** `tdd-non-code.json` covers the 17 human tickets and any documentation change: `change_type` of documentation, research, verification or policy, a `reason`, and, for verification, `sources` naming where every claim came from. It keeps registration and API-verification tickets inside the harness so that every one of the 92 tickets leaves a journal.
- **`status` is cheap by design.** At most one git call, never a tree fingerprint, never the network. The 200 ms budget is enforced in tests as those two properties plus a loose one-second ceiling, because a wall-clock assertion in CI is flaky by construction.
- **`check` always appends, `advance` appends only on success.** A failed check is a fact about the work; a malformed evidence file is a typo. Rework is counted by explicit `return` records.
- **Actors are self-reported.** `<tool>:<role>` from the threshold file, recorded as a claim, never authenticated. `independence: independent` is refused when every record in the journal carries the same actor prefix, which catches the lazy case without pretending to prove the honest one.
- **No automatic repair.** A stale lock is reported with its PID, age and command for a human to remove. A missing or malformed `thresholds.toml` is fatal rather than defaulted. `doctor` reports every problem it finds and then exits non-zero.
- **A journal directory holds records and an allowlist, nothing else.** The reader matches exactly `NNNN.json` and refuses anything else it finds, except `kpi.json` (SEEN-091) and an `attachments/` subdirectory. A tampered journal shows up in practice as `0007.json.bak` or `0008 (copy).json` from a bad merge, not as a forged chain, and an allowlist catches those. Attachments (saved API responses backing a verification ticket) are referenced from a record by relative path and sha256 rather than chained, since they arrive with their record rather than after it.
- **One ticket, one branch, enforced.** Every writing command (start, note, check, advance, return, verify-delivery) refuses unless the current branch matches `^(claude|codex)/<ticket-id>-`, and refuses on `main` and on a detached HEAD. No override until a case needs one. The expensive mistake is not starting on the wrong branch, it is drifting onto another branch mid-ticket and recording evidence about a tree that belongs to different work.
- **This ticket is the bootstrap and has no journal.** The harness does not exist while it is being built, so a journal for SEEN-086 could only be hand-written or backdated, and both are falsifications. Its evidence is the test suite, the pull request body and an `## Outcome` section in this file. Every ticket from SEEN-087 onwards has a real journal.
- **The estimate moved from 5 to 8 points** when non-code mode, the git-notary check, the markdown link check, the `.gitignore` and the CI workflow entered the scope in the same session.

## Acceptance criteria

- [ ] start creates docs/harness/history/<ticket>/0001.json holding the ticket path, the full ticket text, the actor and stage clarify, and refuses a ticket that already has a journal
- [ ] advance refuses a stage file missing any required field of its template and names the field, and refuses a value left identical to the template's example text
- [ ] a passing advance appends a record whose prev_hash equals the sha256 of the previous record file on disk, reproducible with shasum -a 256 and no harness
- [ ] check appends a record whatever the exit code, carrying command, phase, exit code, duration_ms and output_sha256, and the tdd stage gate refuses slices citing checks from another stage or attempt or cited out of order
- [ ] the tdd stage accepts mode non-code with a change type and a reason, and requires sources when the change type is verification
- [ ] doctor verifies the hash chain of every journal, fails when any record under docs/harness/history has been committed as a modification or a deletion, checks thresholds.toml, the templates, the gitignore entries, the Python floor and that every relative markdown link in the repository resolves, and reports every problem before exiting non-zero
- [ ] every writing command refuses when the current branch is not claude/<id>- or codex/<id>-, and refuses on main and on a detached HEAD
- [ ] status prints stage, attempt, branch, last actor, chain head and the next command, makes at most one git call, never fingerprints the tree and never touches the network
- [ ] verify-delivery confirms the tip commit is on the remote, that the journal holds one accepted record per stage and that the reviewed-tree fingerprint still matches review, then appends the receipt and sets the stage to delivered, without requiring gh
- [ ] the Seene project is removed in a chore(SEEN-086) commit, .harness-drafts/ and the lock file are gitignored, and .github/workflows/ci.yml runs the harness tests
- [ ] python3 -m unittest discover -s harness/tests passes locally on 3.14 and in CI on 3.12, and no test can write under the repository's own docs/harness/history

## Depends on

- none

## Blocks

- [SEEN-087](SEEN-087-install-graphify-build-the-repo-graph-and-wire.md): Install graphify, build the repo graph and wire it into both assistants
- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates
- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness
- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Glossary: [CONTEXT.md](../../CONTEXT.md)
- Harness workflow: [docs/harness/workflow.md](../harness/workflow.md)
- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
