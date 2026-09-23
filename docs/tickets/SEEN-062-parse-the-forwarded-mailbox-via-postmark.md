---
id: SEEN-062
title: "Parse the forwarded mailbox via Postmark inbound into threads"
epic: E7
epic_name: "Modules: Reconcile, Comply, Serve"
sprint: 5
sprint_dates: "7 - 18 Dec 2026"
gate: G5
estimate: 5
executor: claude-code
changes_agent_action: false
marketplaces: [bol]
depends_on: [SEEN-004, SEEN-027, SEEN-061]
status: todo
---
# SEEN-062: Parse the forwarded mailbox via Postmark inbound into threads

| | |
|---|---|
| Epic | E7 Modules: Reconcile, Comply, Serve |
| Sprint | 5 (7 - 18 Dec 2026), gate G5 |
| Estimate | 5 points (one point is about two hours with Claude Code) |
| Executor | Claude Code |
| Changes an agent action | no |
| Marketplaces | bol |
| Status | todo |

## Description

Implement the Postmark inbound webhook in apps/api: parse forwarded mail, strip signatures and quoted text, identify the marketplace and the order or case id with per-marketplace patterns (Bol first, since it has no messaging API), attach the mail to an existing thread or claim or open a new thread, and store attachments as evidence. Unmatched mail lands in an ops queue rather than being dropped.

## Acceptance criteria

- [ ] A forwarded Bol customer question is matched to its order and thread by order id in a fixture set of 50 mails with at least 90% matched
- [ ] A Bol compensation confirmation mail attaches to the claim as a claim_event
- [ ] Attachments are stored in the evidence store with sha256
- [ ] Unmatched mail appears in the ops console queue with a reason

## Depends on

- [SEEN-004](SEEN-004-set-up-postmark-inbound-domain-and-stripe.md): Set up Postmark inbound domain and Stripe account
- [SEEN-027](SEEN-027-build-the-claims-rail-with-api-assisted-and.md): Build the claims rail with api, assisted and track modes
- [SEEN-061](SEEN-061-ingest-message-threads-from-amazon-ebay.md): Ingest message_threads from Amazon, eBay, Kaufland and Otto

## Blocks

- [SEEN-063](SEEN-063-add-reply-message-tool-bound-to-tenant-service.md): Add reply_message tool bound to tenant service policies

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: Switch on continuous reconciliation, listing compliance fixes and buyer correspondence per tenant as scheduled tasks, tools and policy rows on the same record.
