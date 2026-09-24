---
id: SEEN-086
title: "Build the Seen harness CLI with staged journal and receipts"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: []
status: done
---
# SEEN-086: Build the Seen harness CLI with staged journal and receipts

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | done |

## Description

Create harness/run.py (Python 3.12, standard library only) with the five stages clarify, solution, tdd, review, deliver and the commands doctor, start, status, history, draft, note, check, advance, return, verify-delivery. Records go to docs/harness/history/<ticket>/NNNN.json as append-only, hash-chained files; drafts live in the gitignored .harness-drafts/. Each stage has a JSON template in harness/templates/ whose required fields are the gate, and thresholds and checklists live in harness/policy.toml, not in prompts. The decision that matters: the journal is the source of truth for resume, so a session started by Claude Code and resumed by Codex reads the same files and continues at the recorded stage.

## Acceptance criteria

- [ ] start creates docs/harness/history/<ticket>/0001.json with the ticket path, actor and stage clarify, and refuses to start a ticket that already has a journal
- [ ] advance refuses a stage file missing any required field of its template and names the field; a passing advance appends a record whose prev_hash equals the sha256 of the previous record
- [ ] doctor verifies the hash chain of every journal and exits non-zero on a broken chain or an edited record
- [ ] status prints the current stage, branch, last actor and the next command for a ticket in under 200 ms
- [ ] python3 -m unittest discover -s harness/tests passes and runs in CI

## Depends on

- none

## Blocks

- [SEEN-087](SEEN-087-install-graphify-build-the-repo-graph-and-wire.md): Install graphify, build the repo graph and wire it into both assistants
- [SEEN-096](SEEN-096-add-codegraph-and-route-the-graph-command.md): Add codegraph and route the graph command to it
- [SEEN-098](SEEN-098-add-repowise-and-carry-risk-into-the-gate.md): Add repowise and carry its risk answer into the gate
- [SEEN-088](SEEN-088-integrate-jev-ai-typed-decisions-into-the.md): Integrate Jev AI typed decisions into the harness gates
- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce TDD and CI quality gates in the harness
- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-091](SEEN-091-collect-harness-kpis-per-ticket-and-produce.md): Collect harness KPIs per ticket and produce weekly and sprint reports
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
