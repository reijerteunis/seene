---
id: SEEN-037
title: "File the first ten claims across two marketplaces from the inbox"
epic: E3
epic_name: "Claims rail and evidence"
sprint: 2
sprint_dates: "26 Oct - 6 Nov 2026"
gate: G2
estimate: 2
executor: human
changes_agent_action: false
marketplaces: [bol, amazon, ebay]
depends_on: [SEEN-028, SEEN-029, SEEN-030, SEEN-035]
status: todo
---
# SEEN-037: File the first ten claims across two marketplaces from the inbox

| | |
|---|---|
| Epic | E3 Claims rail and evidence |
| Sprint | 2 (26 Oct - 6 Nov 2026), gate G2 |
| Estimate | 2 points (one point is about two hours with Claude Code) |
| Executor | human (registration, verification or real-data run) |
| Changes an agent action | no |
| Marketplaces | bol, amazon, ebay |
| Status | todo |

## Description

Work the approval inbox for the friendly brand and one pilot: approve or edit the drafted claims, contest eBay disputes by API, confirm Bol and Amazon case packs and submit them on the partner platform and Seller Central, and record the case ids. Note every point where the draft or the pack needed a change.

## Acceptance criteria

- [ ] At least 10 claims submitted across at least two marketplaces by 6 November
- [ ] Every submitted claim has an approvals row, an audit event chain and an external case id where the marketplace issues one
- [ ] At least one credit matched to a claim in an ingested settlement line
- [ ] Edits made to drafts listed as eval cases or prompt issues

## Depends on

- [SEEN-028](SEEN-028-contest-ebay-payment-disputes-and-cases-by-api.md): Contest eBay payment disputes and cases by API
- [SEEN-029](SEEN-029-build-the-bol-assisted-case-pack-with-tracking.md): Build the Bol assisted case pack with tracking
- [SEEN-030](SEEN-030-build-the-amazon-assisted-case-pack-with-report.md): Build the Amazon assisted case pack with report tracking
- [SEEN-035](SEEN-035-build-the-approval-inbox-with-approve-edit-and.md): Build the approval inbox with approve, edit and reject

## Blocks

- none

## Context

- Product requirements: [docs/prd/prd.md](../prd/prd.md)
- Architecture: [docs/architecture.md](../architecture.md)
- Development plan and gates: [docs/development-plan.md](../development-plan.md)
- Epic goal: File claims by API where a marketplace allows it and as one-click case packs where it does not, track each to a credit in an ingested settlement line, and keep hashed evidence.
