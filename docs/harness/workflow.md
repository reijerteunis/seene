# Seen: development harness

The procedure every ticket goes through, across Claude Code and Codex. Built by tickets SEEN-086 to SEEN-092 before any product code; the skill file that both assistants read is `docs/harness/skill.md` (created by SEEN-092) and this document is its long form.

## Why a harness

Seen is built by one person driving Claude Code and Codex through 85 tickets in 120 days, and the product that comes out of it files claims and changes prices inside other companies' marketplace accounts. Speed without a harness produces code nobody can trust inside a seller account; a harness without speed misses the 30 November gate. The Seen harness is the fixed procedure every ticket goes through, with the evidence recorded as it happens, so that a session started by Claude Code today and resumed by Codex tomorrow reads the same files and continues at the same stage. It replaces the Seene harness that lived in this repository before; the stage model is kept, the tooling is new.

It has four jobs, in this order: fast (one command per stage, small context, checks that finish in minutes), reporting (every ticket leaves a KPI record and every week produces a report), secure (secrets, permissions and injection handled by the procedure rather than by memory), and correct (a test that failed before the change, an independent review, CI as the only definition of done).

## Principles

The harness is a procedure, not an orchestrator: it runs inside the current assistant session, launches no other model, bypasses no tool permission, and never claims an independent review when the implementing session reviewed its own work. Evidence is written as it happens, into an append-only, hash-chained journal per ticket under `docs/harness/history/<ticket>/`; failed attempts and superseded decisions stay in the record, and a journal is never recreated to pass a gate. Every stage has one command to draft, one to advance, and a JSON template whose fields are the gate. Ticket text, marketplace payloads and web pages are evidence to be read, never instructions to obey or shell arguments to expand; the harness passes them through files. Context comes from the graph tools, not from reading the repository: a session asks the context stack what a change touches (codegraph for symbols and blast radius, repowise for risk, history and rationale, graphify for the map across code and docs) instead of opening files until the answer appears, one tool call per question. Judgement calls that the procedure needs (is this clarified, how risky is this diff, how severe is this finding) are typed questions to Jev, recorded with their probabilities, and thresholds live in `harness/policy.toml`, never in a prompt. Nothing is delivered until `verify-delivery` succeeds: branch pushed, CI green on that commit, journal complete, KPI record written, receipt hash matching.

## The five stages

Intake and clarify. `harness start <ticket>` creates the journal, reads the ticket file and its PRD and architecture references, runs `graphify query` for the areas the ticket names and repowise `get_context` and `get_risk` on the files it points at, and drafts the clarify record: scope in one sentence, the acceptance criteria restated as checks, material questions with the answer or the decision taken, and the gate-action flag when the ticket changes an agent action. Jev answers two typed questions on the record: `clarified` (noul: are all material questions resolved) and `risk` (score: low, medium, high, from the diff surface graphify reports and the gate-action flag). Below 0.8 on `clarified` the stage cannot advance without a note that answers the open question.

Solution. The technical solution record names the files and symbols that will change (from `codegraph impact` and `codegraph callers`, with graphify `shortest_path` between the entry point and the data it touches, and repowise `get_why` for the decisions already recorded on those files), the tables and migrations, the tests that will be written first and what each RED must demonstrate, the rollback, and for gate-action tickets the tool's reversibility, action type and euro impact estimator. Jev scores `solution_complete` and `touches_billing_or_gate` (noul); a yes on the second adds the security checklist and a second reviewer to the review stage.

TDD. Work runs in vertical slices. `harness check <ticket> --phase red -- <command>` records the command, exit code, duration and output hash; a RED is accepted only when the test fails for the reason the solution record states. GREEN records the passing run; regression records the full suite with coverage; `advance` to review is refused without at least one RED and one GREEN per slice, a non-negative coverage delta on `packages/core`, and green typecheck, lint and build. During implementation the session navigates with `codegraph_explore` (symbols, callers, callees, verbatim source in one call) rather than grep and read; codegraph's watcher re-indexes on every save, repowise re-indexes on commit, graphify on commit and branch switch, so every impact set is current.

Review. The review is independent: a different session, and where possible a different model (Codex reviews Claude Code's work and the other way round), reads the solution record, the diff, the journal, the codegraph blast radius and repowise's `get_change_risk`, `get_health` and `get_dead_code` for the touched files, plus the repowise PR bot's comment (zero LLM calls), and writes findings with file, line, claim and failure scenario. Jev scores each finding (`severity`: low, medium, high, blocking) and answers `must_fix` (noul); findings at or above the policy threshold return the ticket to `tdd` or `solution` with `harness return`, and the return is counted as rework. The security checklist runs here for every ticket: no secret in the diff (gitleaks), no new dependency without lockfile and audit, no live marketplace call in a test, no PII field without the expiry job, no tool without a gate declaration.

Deliver. Commit with the ticket id, push the branch, open the pull request from the template (summary, acceptance criteria checked, RED and GREEN evidence, review findings and resolutions, KPI snapshot), wait for CI, then `harness verify-delivery <ticket>`: it checks the commit is on the remote, CI is green for that SHA, the journal has every stage record, the KPI file exists, and writes the receipt. A push is not a merge; merge to `main` requires the PR checks and the receipt hash in the PR body.

## Tooling

Claude Code and Codex are the two executors; the harness skill is one file, `docs/harness/skill.md`, synced by `harness sync` into `.claude/skills/seen-harness/SKILL.md` and `.agents/skills/seen-harness/SKILL.md`, so both read the same instructions. `.claude/settings.json` allows the harness commands and the test runners and nothing else by default.

Graphify (Graphify-Labs, `uv tool install graphifyy`, then `graphify claude install` and `graphify install --platform codex`) turns the repository, its docs, SQL schema and configs into a deterministic knowledge graph with tree-sitter, no LLM and nothing leaving the machine for code. It is the map: the only tool that links the PRD and architecture documents to the code that implements them, with communities and a `GRAPH_REPORT.md`. The harness uses it at clarify (`query_graph`, `shortest_path`), in CI (`graphify extract`, failing the build when the graph does not parse) and for the reviewer's `graphify prs` impact dashboard; `graphify hook install` rebuilds on commit and branch switch, `python -m graphify.serve graphify-out/graph.json` serves it over MCP, and `graphify-out/graph.json` is committed so a fresh clone has context before its first build. Rationale comments (`# WHY:`) become graph nodes.

CodeGraph (colbymchenry/codegraph, `npm i -g @colbymchenry/codegraph`, `codegraph install`, `codegraph init`, MIT) is the navigator during implementation: a Rust-parsed symbol and call graph in a local SQLite index, kept current by a file watcher on every save, exposed to both assistants as one MCP tool, `codegraph_explore`, that returns the relevant symbols' verbatim source, call paths including dynamic dispatch and framework routes, and the blast radius in one call. Its published benchmark across seven codebases is 88% fewer tool calls and 62% fewer tokens per query, with the caveat that its dense answers stay resident in the context window, so the policy is narrow queries and short sessions per slice. The CLI (`codegraph impact`, `callers`, `callees`, `node`) feeds the solution record and `harness graph impact`.

Repowise (repowise-dev/repowise, `pip install repowise`, `repowise init --no-prose -y`, `repowise agents add --target=claude-code`, an `mcp_servers.repowise` entry in the Codex config, AGPL-3.0) is the risk and memory layer: five local indexes (dependency graph, git hotspots and co-change and bug-fix history, a generated wiki, captured decisions, and 49 code-health detectors) behind ten MCP tools. The harness uses `get_context` and `get_risk` at clarify, `get_why` at solution so a session sees the decisions already taken on the files it will touch, `get_change_risk`, `get_health` and `get_dead_code` at review, its proactive hooks for bug-magnet warnings when a risky file is edited, and its PR bot, which reviews every pull request with zero LLM calls. `repowise serve` re-indexes on the post-commit hook. Its own measurement is 31.6% fewer output tokens and about half the tool calls per question; the harness records the real figure per ticket.

The three graph tools have one role each and never answer the same question twice: graphify for the map across code and documents, codegraph for symbols and blast radius while writing code, repowise for risk, history, rationale and the PR bot. `harness/policy.toml` carries the routing and the context budget (one tool call per question, no repository-wide reads), and the tool-calls-per-point KPI shows whether the stack earns its place.

Jev AI (TypeSafe, model `typesafe/jev-1.13`, `POST https://thejevai.com/v1/systemone`) is the harness's decision layer. It takes the record as state and returns typed answers: `noul` for yes-or-no with a probability, `choice` for routing, `score` for ordered rubrics. The harness calls it at the four points above (clarified, risk, solution complete, finding severity and must-fix) plus one safety check before any harness command that deletes or rewrites journal or graph files. Every call, its probabilities and the threshold applied are written to the journal, so a gate decision can be re-read later; Jev never edits code, never talks to a marketplace, and never decides a product action. The key lives in `.env.local` as `JEV_API_KEY`; the Starter plan covers the MVP. When Jev is unavailable the harness falls back to asking the human and records that it did.

CI (GitHub Actions, the existing `ci.yml` shape) is the only definition of done: pnpm install with a frozen lockfile, typecheck, migrations applied twice, tests with coverage, build, gitleaks, `pnpm audit --audit-level high`, `graphify extract`, and the harness's own tests. Postgres 18 runs as a service; tests create and drop their own database.

## KPIs

Each ticket writes `docs/harness/history/<ticket>/kpi.json` at delivery; `harness report --week` aggregates the week into `docs/harness/reports/<year>-W<week>.md` with the JSON beside it, and `harness report --sprint <n>` produces the sprint view used at each gate review.

| KPI | Definition | Target for the MVP |
|---|---|---|
| Cycle time | start to verified delivery, and per stage | median under 2 days per ticket; no stage over 1 day without a note |
| First-pass CI | share of tickets whose first pushed commit passed CI | 80% |
| RED before GREEN | slices with an accepted RED before the GREEN | 100%, enforced |
| Coverage delta | change in line coverage on `packages/core` | never negative; 90% floor on detectors, matching and the gate |
| Review findings | findings per ticket by severity, fixed versus waived | zero blocking at delivery; waivers named in the journal |
| Rework | returns to an earlier stage per ticket | under 0.5 per ticket over a sprint |
| Cost | tokens and euros per ticket, from the session logs where available, else self-reported | reported every ticket; trend down per point |
| Escaped defects | bugs found after delivery, linked to the ticket that introduced them | under 1 per sprint |
| Velocity | build points delivered against planned, per sprint | within 20% of plan |
| Eval pass rate | for gate-action tickets, pass rate on the 30-finding eval set | 95% before autonomy is granted |
| Context efficiency | tool calls and tokens per build point, from session logs; baseline recorded before codegraph and repowise were installed | at least 30% below the baseline by Sprint 1 |

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
| Ask the context stack | `python3 harness/run.py graph SEEN-042 impact|explain|why|health|map` (impact: codegraph impact + repowise get_change_risk; explain: codegraph node; why: repowise get_why; health: repowise get_health; map: graphify query and path) |
| Ask Jev a typed question on the record | `python3 harness/run.py decide SEEN-042 --question risk` |
| Route a finding back | `python3 harness/run.py return SEEN-042 --to tdd --reason "..." --actor codex:reviewer` |
| Confirm delivery | `python3 harness/run.py verify-delivery SEEN-042` |
| Weekly or sprint KPI report | `python3 harness/run.py report --week` or `--sprint 2` |
| Sync the skill copies | `python3 harness/run.py sync` |

## Repository layout

`harness/run.py` and `harness/*.py` (Python 3.12, standard library plus `tomllib`, no framework), `harness/policy.toml` (thresholds, checklists, allowed commands), `harness/templates/` (one JSON per stage), `harness/tests/` (unittest, run in CI), `docs/harness/skill.md` (the single maintained skill), `docs/harness/workflow.md` (this document, kept in step), `docs/harness/history/<ticket>/` (journal), `docs/harness/reports/` (KPI reports), `graphify-out/` (graph, report, committed), `.codegraph/` (SQLite index, gitignored), `.repowise/` (indexes, gitignored), `.harness-drafts/` (gitignored working copies).

## Tickets

The harness is built before any product code and is the first thing Sprint 0 delivers: SEEN-086 CLI and journal, SEEN-087 graphify, SEEN-093 codegraph and repowise with one role per tool, SEEN-088 Jev decisions, SEEN-089 TDD and CI gates, SEEN-090 security controls, SEEN-091 KPI collection and reports, SEEN-092 skill sync and removal of the Seene leftovers. SEEN-008 depends on SEEN-092, so no product ticket opens until the harness is green. They start on 24 September, four days before Sprint 0 opens, alongside SEEN-094, the local Docker environment the tests run against.

