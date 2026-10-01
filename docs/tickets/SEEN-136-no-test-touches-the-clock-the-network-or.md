---
id: SEEN-136
title: "No test touches the clock, the network or randomness unfaked, and a flaky test is a defect"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 2
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-089, SEEN-097]
status: todo
priority: P1
---
# SEEN-136: No test touches the clock, the network or randomness unfaked, and a flaky test is a defect

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |
| Priority | P1 (correctness and speed programme, see docs/harness/workflow.md) |

## Description

A test that fails once in five runs costs more than a test that fails every time: the session reruns it, the review reads the rerun, the cost KPI counts both, and nobody learns anything. Make the test environment hermetic by construction. The vitest setup installs a fixed clock and fake timers for every test, and a test that wants real time opts out by name; fast-check runs with a recorded seed so a property failure replays; a network guard fails any test that opens a socket outside the Prism mocks on localhost, which is the runtime twin of SEEN-090's lint on marketplace hosts in test code. CI runs the suites in shuffled order with retries set to zero, so hidden coupling between tests shows up on main and not inside a session, and the order seed is printed so a failure replays. A test that fails and then passes on rerun is recorded in the journal as flaky by a hook and blocks the merge until it is fixed or deleted; it is never retried silently. Database-backed suites start from a fresh template database on the compose stack from SEEN-097, so state never leaks between suites. The decision that matters: a flaky test is a defect in the test, and the harness treats it as one instead of paying for the rerun.

## Acceptance criteria

- [ ] The vitest setup installs a fixed clock and fake timers by default, seeds fast-check and records the seed in the journal, and a test that needs real time opts out by name
- [ ] A test that opens a socket outside the Prism mocks on localhost fails naming the host, proven with a fixture
- [ ] CI runs the suites in shuffled order with retries set to zero and prints the order seed so a failure replays
- [ ] A test that fails and then passes on rerun is recorded in the journal as flaky and blocks the merge until it is fixed or deleted; the weekly report counts flaky tests per sprint
- [ ] Each database-backed suite starts from a fresh template database on the compose stack

## Depends on

- [SEEN-089](SEEN-089-enforce-tdd-and-ci-quality-gates-in-the-harness.md): Enforce the TDD gates in the harness
- [SEEN-097](SEEN-097-set-up-the-local-docker-development-environment.md): Set up the local Docker development environment

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
