---
id: SEEN-063
title: "Add reply_message tool bound to tenant service policies"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 5
executor: claude-code
changes_agent_action: true
marketplaces: [bol, amazon, ebay, kaufland, otto]
depends_on: [SEEN-033, SEEN-034, SEEN-061, SEEN-062]
status: todo
---
# SEEN-063: Add reply_message tool bound to tenant service policies

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | yes: goes through the policy gate, see PRD section 8 (FR-19 to FR-27) |
| Marketplaces | bol, amazon, ebay, kaufland, otto |
| Status | todo |

## Description

Add reply_message to packages/agent: it drafts a reply for a thread inside the tenant's service policies (return terms, cancellation terms, tone, refusal list of topics the agent never answers) stored on policies, declares action type message_reply and reversible false, and sends through the marketplace connector or, for mail threads, through Postmark from the tenant's forwarding address, after the gate decision. Design decision: the refusal list is evaluated in code before the model drafts, so a refused topic never reaches the marketplace.

## Acceptance criteria

- [ ] A reply touching a refusal-list topic returns escalate and no message is sent
- [ ] Draft quotes the tenant's return terms when the thread asks about returns in an eval of 20 threads
- [ ] Sent replies are stored as messages with drafted_by agent and sent_at
- [ ] Replies for a tenant with Serve disabled are refused with reason module_disabled

## Depends on

- [SEEN-033](SEEN-033-implement-policy-gate-v1-with-caps-and.md): Implement policy gate v1 with caps and reversibility
- [SEEN-034](SEEN-034-build-agent-runtime-v1-with-the-fixed-tool-set.md): Build agent runtime v1 with the fixed tool set and cost accounting
- [SEEN-061](SEEN-061-ingest-message-threads-from-amazon-ebay.md): Ingest message_threads from Amazon, eBay, Kaufland and Otto
- [SEEN-062](SEEN-062-parse-the-forwarded-mailbox-via-postmark.md): Parse the forwarded mailbox via Postmark inbound into threads

## Blocks

- [SEEN-067](SEEN-067-show-serve-threads-and-drafts-in-the-inbox.md): Show Serve threads and drafts in the inbox

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
