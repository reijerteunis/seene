---
id: SEEN-088
title: "Integrate Jev AI typed decisions into the harness gates"
epic: E10
epic_name: "Development harness"
sprint: 0
sprint_dates: "24 Sep - 9 Oct 2026"
gate: G0
estimate: 3
executor: claude-code
changes_agent_action: false
marketplaces: []
depends_on: [SEEN-086]
status: todo
---
# SEEN-088: Integrate Jev AI typed decisions into the harness gates

| | |
|---|---|
| Epic | E10 Development harness |
| Sprint | 0 (24 Sep - 9 Oct 2026), gate G0 |
| Estimate | 3 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | none |
| Status | todo |

## Description

Add harness/jev.py calling POST https://thejevai.com/v1/systemone with model typesafe/jev-1.13, the stage record as state, and typed questions: clarified (noul), risk (score low, medium, high), solution_complete (noul), touches_billing_or_policy_gate (noul), finding severity (score low, medium, high, blocking), must_fix (noul), is_destructive (noul). Wire harness decide <ticket> --question <name> and call the questions automatically on advance for the stage they belong to; thresholds live in harness/thresholds.toml. Every call writes the question, the probabilities, the threshold and the outcome to the journal. When JEV_API_KEY is missing or the API fails, the harness asks the human, records the fallback, and continues. The decision that matters: Jev is a decision layer for the procedure only; it never edits code, never touches a marketplace and never decides a product action.

## Acceptance criteria

- [ ] harness decide SEEN-088 --question risk returns a score with per-option probabilities and appends a decision record with model, question, probabilities, threshold and outcome
- [ ] advance from clarify is refused when clarified is below the policy threshold (0.8 by default) and the refusal names the open question from the record
- [ ] advance from solution adds the security checklist and a second-reviewer requirement to the review template when touches_billing_or_policy_gate is yes
- [ ] With JEV_API_KEY unset, every decision point prompts the human and records fallback: human in the journal instead of failing
- [ ] The key is read from .env.local only; a unit test asserts that no decision record contains the key or any environment value

## Depends on

- [SEEN-086](SEEN-086-build-the-seen-harness-cli-with-staged-journal.md): Build the Seen harness CLI with staged journal and receipts

## Blocks

- [SEEN-090](SEEN-090-add-harness-security-controls-secrets.md): Add harness security controls: secrets, permissions, injection, supply chain
- [SEEN-092](SEEN-092-sync-the-harness-skill-to-claude-code-and-codex.md): Sync the harness skill to Claude Code and Codex and retire the Seene leftovers

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Give every ticket one fast, evidence-recording procedure across Claude Code and Codex, with graphify for context, Jev for typed gate decisions, CI as the definition of done, security controls built into the stages, and a KPI record per ticket.
