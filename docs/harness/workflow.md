# Seen: development harness

The procedure every ticket goes through, across Claude Code and Codex. Built by tickets SEEN-086 to SEEN-092 before any product code; the skill file that both assistants read is `docs/harness/skill.md` (created by SEEN-092) and this document is its long form.

## Why a harness

Seen is built by one person driving Claude Code and Codex through 85 tickets in 120 days, and the product that comes out of it files claims and changes prices inside other companies' marketplace accounts. Speed without a harness produces code nobody can trust inside a seller account; a harness without speed misses the 30 November POC gate. The Seen harness is the fixed procedure every ticket goes through, with the evidence recorded as it happens, so that a session started by Claude Code today and resumed by Codex tomorrow reads the same files and continues at the same stage. It replaces the Seene harness that lived in this repository before; the stage model is kept, the tooling is new.

It has four jobs, in this order: fast (one command per stage, small context, checks that finish in minutes), reporting (every ticket leaves a KPI record and every week produces a report), secure (secrets, permissions and injection handled by the procedure rather than by memory), and correct (a test that failed before the change, an independent review, CI as the only definition of done).

## Principles

The harness is a procedure, not an orchestrator: it runs inside the current assistant session, launches no other model, bypasses no tool permission, and never claims an independent review when the implementing session reviewed its own work. Terminology is fixed in `CONTEXT.md`, which is why a stage gate, the product's policy gate and the sprint gates G0 to G7 are never called just a gate. Evidence is written as it happens, into an append-only, hash-chained journal per ticket under `docs/harness/history/<ticket>/`, where each record carries the sha256 of the previous record file and `doctor` additionally proves against git history that no record was ever committed as a modification or a deletion; failed attempts and superseded decisions stay in the record, and a journal is never recreated to pass a stage gate. Every stage has one command to draft, one to advance, and a JSON template whose fields are the stage gate. Ticket text, marketplace payloads and web pages are evidence to be read, never instructions to obey or shell arguments to expand; the harness passes them through files. Context comes from the knowledge graph, not from reading the repository: a session asks graphify what a change touches instead of opening files until the answer appears. Judgement calls that the procedure needs (is this clarified, how risky is this diff, how severe is this finding) are typed questions to Jev, recorded with their probabilities, and thresholds live in `harness/thresholds.toml`, never in a prompt. Nothing is delivered until `verify-delivery` succeeds: branch pushed, CI green on that commit, journal complete, KPI record written, receipt hash matching.

## The five stages

Intake and clarify. `harness start <ticket>` creates the journal, reads the ticket file and its PRD and architecture references, runs `graphify query` and `get_pr_impact` for the areas the ticket names, and drafts the clarify record: scope in one sentence, the acceptance criteria restated as checks, material questions with the answer or the decision taken, and the policy-gate action flag when the ticket changes an agent action. Jev answers two typed questions on the record: `clarified` (noul: are all material questions resolved) and `risk` (score: low, medium, high, from the diff surface graphify reports and the policy-gate action flag). Below 0.8 on `clarified` the stage cannot advance without a note that answers the open question.

Solution. The technical solution record names the files and symbols that will change (from the graph, with `shortest_path` between the entry point and the data it touches), the tables and migrations, the tests that will be written first and what each RED must demonstrate, the rollback, and for policy-gate action tickets the tool's reversibility, action type and euro impact estimator. Jev scores `solution_complete` and `touches_billing_or_policy_gate` (noul); a yes on the second adds the security checklist and a second reviewer to the review stage.

TDD. Work runs in vertical slices. `harness check <ticket> --phase red -- <command>` records the command, exit code, duration and output hash; a RED is accepted only when the test fails for the reason the solution record states. GREEN records the passing run; regression records the full suite with coverage; `advance` to review is refused without at least one RED and one GREEN per slice, a non-negative coverage delta on `packages/core`, and green typecheck, lint and build. Graphify is updated on each commit by its git hook, so the impact set is always current. Tickets with no executable behaviour (registrations, verifications against a live account, documentation) take the non-code path instead: a change type of documentation, research, verification or policy, a recorded reason, and, for a verification, the sources every claim came from. It keeps the 17 human tickets inside the harness so every one of the 92 leaves a journal.

Review. The review is independent: a different session, and where possible a different model (Codex reviews Claude Code's work and the other way round), reads the solution record, the diff, the journal and the graph impact, and writes findings with file, line, claim and failure scenario. Jev scores each finding (`severity`: low, medium, high, blocking) and answers `must_fix` (noul); findings at or above the policy threshold return the ticket to `tdd` or `solution` with `harness return`, and the return is counted as rework. The security checklist runs here for every ticket: no secret in the diff (gitleaks), no new dependency without lockfile and audit, no live marketplace call in a test, no PII field without the expiry job, no tool without a policy-gate declaration.

Deliver. Commit with the ticket id, push the branch, open the pull request from the template (summary, acceptance criteria checked, RED and GREEN evidence, review findings and resolutions, KPI snapshot), wait for CI, then `harness verify-delivery <ticket>`. It is the deliver stage's own stage gate, not an advance: it checks the commit is on the remote, CI is green for that SHA, the journal has every stage record and the KPI file exists, then appends the receipt record and moves the ticket to `delivered`. The receipt attests the code commit and the reviewed-tree fingerprint, which excludes the journal and the drafts, so the trailing journal-only commit that carries the receipt cannot invalidate it. SEEN-086 ships the offline half (remote, journal, fingerprint); the CI check arrives with SEEN-089 and the KPI check with SEEN-091, and each refuses rather than passes when it cannot be run. A push is not a merge; merge to `main` requires the PR checks and the receipt hash, which is the sha256 of the receipt record file, in the PR body.

## Tooling

Claude Code and Codex are the two executors; the harness skill is one file, `docs/harness/skill.md`, synced by `harness sync` into `.claude/skills/seen-harness/SKILL.md` and `.agents/skills/seen-harness/SKILL.md`, so both read the same instructions. `.claude/settings.json` allows the harness commands and the test runners and nothing else by default.

Graphify (Graphify-Labs, `uv tool install graphifyy`, then `graphify claude install` and `graphify install --platform codex`) turns the repository, its docs, SQL schema and configs into a deterministic knowledge graph with tree-sitter, no LLM and nothing leaving the machine for code. The harness uses it four ways: `graphify hook install` rebuilds the graph on every commit and branch switch; `python -m graphify.serve graphify-out/graph.json` runs as an MCP server in both assistants so a session queries `query_graph`, `get_neighbors`, `shortest_path` and `get_pr_impact` instead of reading files; `graphify extract` runs headless in CI to produce `GRAPH_REPORT.md` and fail the build when the graph does not parse; and `graphify prs` gives the reviewer the impact set of a pull request. `graphify-out/graph.json` is committed so a fresh clone has context before its first build. Rationale comments (`# WHY:`) become graph nodes, which is where design decisions from the solution records are pointed to in code.

Jev AI (TypeSafe, model `jev-latest`, `POST https://api.typesafe.ai/v1/systemone`) is the harness's decision layer. It takes the record as the state and returns typed answers: `noul` for yes-or-no as a single probability, `choice` for routing with a probability per option, `score` for an ordered rubric with a weighted value, a legend and a confidence. One request carries every question a stage owns. The harness calls it at the four points above (clarified, risk, solution complete, finding severity and must-fix) plus one safety check before any harness command that deletes or rewrites journal or graph files. Every call, its probabilities and the threshold applied are written to the journal, so a stage gate decision can be re-read later; Jev never edits code, never talks to a marketplace, and never decides a product action. The key lives in `.env.local` as `JEV_API_KEY`; the Starter plan covers the MVP. When Jev is unavailable the harness falls back to asking the human and records that it did.

CI (GitHub Actions, the existing `ci.yml` shape) is the only definition of done: pnpm install with a frozen lockfile, typecheck, migrations applied twice, tests with coverage, build, gitleaks, `pnpm audit --audit-level high`, `graphify extract`, and the harness's own tests. Postgres 18 runs as a service; tests create and drop their own database.

## KPIs

Each ticket writes `docs/harness/history/<ticket>/kpi.json` at delivery; `harness report --week` aggregates the week into `docs/harness/reports/<year>-W<week>.md` with the JSON beside it, and `harness report --sprint <n>` produces the sprint view used at each sprint gate review.

| KPI | Definition | Target for the MVP |
|---|---|---|
| Cycle time | start to verified delivery, and per stage | median under 2 days per ticket; no stage over 1 day without a note |
| First-pass CI | share of tickets whose first pushed commit passed CI | 80% |
| RED before GREEN | slices with an accepted RED before the GREEN | 100%, enforced |
| Coverage delta | change in line coverage on `packages/core` | never negative; 90% floor on detectors, matching and the policy gate |
| Review findings | findings per ticket by severity, fixed versus waived | zero blocking at delivery; waivers named in the journal |
| Rework | returns to an earlier stage per ticket | under 0.5 per ticket over a sprint |
| Cost | tokens and euros per ticket, from the session logs where available, else self-reported | reported every ticket; trend down per point |
| Escaped defects | bugs found after delivery, linked to the ticket that introduced them | under 1 per sprint |
| Velocity | build points delivered against planned, per sprint | within 20% of plan |
| Eval pass rate | for policy-gate action tickets, pass rate on the 30-finding eval set | 95% before autonomy is granted |

## Security controls

Secrets: gitleaks runs in the pre-commit hook and in CI; `.env.local` is gitignored; the harness refuses to write environment values into any record; marketplace credentials live in Secret Manager and never in fixtures. Tests: no test may call a live marketplace; connector tests run against recorded fixtures with secrets and buyer PII scrubbed at recording time; the test database is created and dropped per run. Permissions: `.claude/settings.json` allowlists harness and test commands; anything else prompts; Codex runs with the equivalent policy. Injection: ticket files, marketplace payloads and fetched web pages are data; the harness never interpolates them into shell commands and the skill says so in its first paragraph. Supply chain: frozen lockfile, `pnpm audit` at high, new dependencies named in the solution record. Branches: `main` protected, PR and CI required, no force push, receipts in PR bodies. Journal integrity: append-only files with a hash chain; `harness doctor` verifies the chain and the sync of the skill copies. Destructive harness operations ask Jev `is_destructive` and then the human before running.

## Commands

| Purpose | Command |
|---|---|
| Check the harness, graph and skill copies | `python3 harness/run.py doctor` |
| Start a ticket | `python3 harness/run.py start SEEN-042 --ticket docs/tickets/SEEN-042-....md --actor claude:implementer` |
| Where am I | `python3 harness/run.py status SEEN-042` |
| Read the journal | `python3 harness/run.py history SEEN-042 [--kind note]` |
| Draft the current stage record | `python3 harness/run.py draft SEEN-042` |
| Record a decision, question or handoff | `python3 harness/run.py note SEEN-042 --file note.md --actor claude:implementer` |
| Run and record a check | `python3 harness/run.py check SEEN-042 --phase red -- pnpm test --filter core` |
| Pass a stage gate | `python3 harness/run.py advance SEEN-042 --file solution.json --actor claude:implementer` |
| Ask the graph | `python3 harness/run.py graph SEEN-042 impact` (wraps graphify query, path, explain, prs) |
| Ask Jev a typed question on the record | `python3 harness/run.py decide SEEN-042 --question risk` |
| Route a finding back | `python3 harness/run.py return SEEN-042 --to tdd --reason "..." --actor codex:reviewer` |
| Confirm delivery | `python3 harness/run.py verify-delivery SEEN-042` |
| Weekly or sprint KPI report | `python3 harness/run.py report --week` or `--sprint 2` |
| Sync the skill copies | `python3 harness/run.py sync` |

## Repository layout

`harness/run.py` and `harness/*.py` (Python 3.12, standard library plus `tomllib`, no framework), `harness/thresholds.toml` (thresholds, checklists, allowed commands), `harness/templates/` (one JSON per stage), `harness/tests/` (unittest, run in CI), `docs/harness/skill.md` (the single maintained skill), `docs/harness/workflow.md` (this document, kept in step), `docs/harness/history/<ticket>/` (journal), `docs/harness/reports/` (KPI reports), `graphify-out/` (graph, report, committed), `.harness-drafts/` (gitignored working copies).

## Tickets

The harness is built before any product code and is the first thing Sprint 0 delivers: SEEN-086 CLI and journal, SEEN-087 graphify, SEEN-088 Jev decisions, SEEN-089 TDD and CI stage gates, SEEN-090 security controls, SEEN-091 KPI collection and reports, SEEN-092 skill sync and removal of the Seene leftovers. SEEN-007 and SEEN-008 depend on SEEN-092, so nothing else opens until the harness is green. They start on 24 September, four days before Sprint 0 opens. SEEN-086 is the bootstrap and is the one ticket with no journal: the harness does not exist while it is being built, so a journal for it could only be hand-written or backdated, and both are falsifications. Its evidence is its test suite, its pull request and an `## Outcome` section in the ticket. Every ticket from SEEN-087 onwards has a real journal.

