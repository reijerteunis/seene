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
status: review
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
| Status | review |

## Description

Add harness/jev.py calling POST https://thejevai.com/v1/systemone with model typesafe/jev-1.13, the stage record as state, and typed questions: clarified (noul), risk (score low, medium, high), solution_complete (noul), touches_billing_or_policy_gate (noul), finding severity (score low, medium, high, blocking), must_fix (noul), is_destructive (noul). Wire harness decide <ticket> --question <name> and call the questions automatically on advance for the stage they belong to; thresholds live in harness/thresholds.toml. Every call writes the question, the probabilities, the threshold and the outcome to the journal. When JEV_API_KEY is missing or the API fails, the harness asks the human, records the fallback, and continues. The decision that matters: Jev is a decision layer for the procedure only; it never edits code, never touches a marketplace and never decides a product action.

## Acceptance criteria

- [x] harness decide SEEN-088 --question risk returns a score with per-option probabilities and appends a decision record with model, question, probabilities, threshold and outcome
- [x] advance from clarify is refused when clarified is below the policy threshold (0.8 by default) and the refusal names the open question from the record
- [x] advance from solution adds the security checklist and a second-reviewer requirement to the review template when touches_billing_or_policy_gate is yes
- [x] With JEV_API_KEY unset, every decision point prompts the human and records fallback: human in the journal instead of failing
- [x] The key is read from .env.local only; a unit test asserts that no decision record contains the key or any environment value

## Outcome

Delivered on 23 September 2026, receipt
`10215e20c985c47f5b35bff8f1b79529441e13f27f2eea5286e7b7bc1262c661`, pull request #3. 25 journal
records, two attempts, one return.

**The live call is unverified.** The credential in this shell is rejected by the API with
`401 Invalid API key`, and the two distinct 401 messages establish that the endpoint authenticates
through the Authorization header while this key is not valid for it (record 3). The request and
response bodies are therefore written to the shape the ticket describes and verified only against a
stub. A valid Jev credential in `.env.local` is all that is outstanding; nothing else changes.

**The fallback is not a stopgap, and this ticket is its own evidence.** Records 21 and 22 are human
answers, and record 22 carries the real failure it fell back from (`HTTPError: 403`). Records 11 and
19 carry judgements recorded as `unavailable`, which block nothing and are countable by SEEN-091.

**Three defects the tests and the gates caught.** Every blocking question was treated as one that
must clear its threshold, which inverted `must_fix`: a review finding nothing to fix would have been
refused and one finding a blocking defect would have passed. Every existing test would have called
the live API, because a credential sits in this shell and the default transport is the real one.
Requiring a recorded judgement before every advance would have made the harness unusable without a
key, contradicting the ticket's own "records the fallback, and continues".

**And the gate refused this delivery once.** `.env.example` entered the tree after review attested
it, and `verify-delivery` would not write a receipt over an unreviewed file. It was removed rather
than the gate overridden; documenting the credential belongs to SEEN-090.

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
