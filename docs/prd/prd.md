# Seen: product requirements (MVP)

| | |
|---|---|
| Status | Draft 1, 23 September 2026 |
| Owner | Ruud (product and engineering) |
| Scope | MVP: Sprint 0 to Sprint 7, 28 September 2026 to 29 January 2027 |
| Sources | Council verdict (22 Sep), idea 01 deep dive, decision tab, API capability research, `docs/architecture.md`, `docs/development-plan.md`, `docs/harness/workflow.md` |
| Company | Seen, tryseen.com (working name during the council rounds: Channel Trade Ledger) |

## 1. Summary

Seen is an AI agent that runs a brand's trading relationship with online marketplaces end to end, and keeps the settlement record that both the brand and the marketplace can read. It connects to the brand's seller accounts through the marketplaces' official APIs (Bol, Amazon, eBay, Kaufland, Otto, with Shopify as the shop system), ingests orders, shipments, returns and settlements into one trade record, finds the money the marketplace kept in error, files or prepares the claims, and then takes over the daily work of the marketplace channel: reconciliation, listing compliance, buyer and marketplace correspondence, pricing against reconciled net margin, and sponsored placements.

The entry product is free and pays for itself: a 90-day settlement audit that costs the brand nothing, followed by recovery at 25% of every credit that actually lands in the brand's account. Modules are switched on afterwards, one at a time, at a monthly fee. Nothing is charged upfront and nothing is charged that cannot be pointed to in the brand's own settlement data.

The MVP proves three things by 29 January 2027: that the audit finds recoverable money on European marketplaces at a measured rate, that the agent can act inside a brand's accounts safely under a policy gate and earn autonomy, and that brands convert from recovery to paid modules.

## 2. Problem

Marketplaces carry 61% of European e-commerce and set the rules of the relationship. They charge commission and fixed fees, deduct for returns and damages, lose parcels, run the advertising auction, and decide what compensation applies. The rules tighten every year: Bol cut lost-parcel and return compensation to 25% of item value, Amazon reimburses lost inventory at manufacturing cost inside 60-day windows, eBay's advertising attribution change turned a 10% stated ad rate into 8-9% of total revenue for many sellers.

On the brand side nobody holds the reconciled record. Settlement files, invoices, orders and returns arrive in different shapes per marketplace and are rarely matched line by line, so fee errors, missing compensation and duplicate charges are never noticed, and the ones that are noticed are filed late or not at all. The average multi-marketplace seller loses two days a week to manual fixes; 52% run the channel on spreadsheets. Marketplace managers and agencies are paid to grow the channel, not to audit it, and every marketplace that opens (Otto and Kaufland to EU sellers in 2026) adds another portal with its own rules and no tooling.

The result is a brand that cannot say what its margin per marketplace is after the marketplace has taken its cut, and money that leaks every month without a name.

## 3. Goals and non-goals

Goals for the MVP, in order of priority:

1. Recover money a brand is owed, on Bol, eBay and Amazon first, with every euro billed traceable to a credit in an ingested settlement line.
2. Establish the trade record as the single reconciled source of what was ordered, shipped, returned, charged and paid, per marketplace.
3. Run agent actions inside the brand's accounts only through a policy gate that decides autonomous, approval or refuse, with an append-only audit trail written before any side effect, and a trust ramp that earns autonomy per action type.
4. Convert recovery customers into paid modules (Reconcile, Comply, Serve, Price, Grow), each built as tools, schedules and policy rows on the same record.
5. Produce the day-120 metrics pack that the seed round is raised on.

Non-goals for the MVP (see also section 14): browser automation of any kind; holding or moving money; refunds, purchase orders, account settings or delistings as agent actions; Zalando, Cdiscount, ManoMano and Autodoc Marketplace connectors; a retailer-side product beyond a read-only view; a mobile app; SSO; repricing on Amazon before the ceiling governor has run a month on eBay and Bol; a general dashboard product.

## 4. Users and buyers

The buyer at a consumer brand is the commercial or channel director, measured on marketplace GMV, margin after fees and ad spend, and on not adding headcount. They already pay an agency 3-10% of marketplace revenue or a marketplace manager at EUR 53-74k loaded. For an automotive aftermarket supplier the buyer is the aftermarket or key-account sales lead, not a D2C role; their problem is fitment data, listing compliance across eBay, Amazon and Autodoc, unauthorised resellers, and settlements they have never reconciled.

The daily user is whoever runs the channel today: the marketplace manager, the agency operator or the founder. They approve actions in the inbox during the trust ramp, read the findings and claims views, and receive the monthly statement. The finance lead reads the statement and the finance export and is the person who notices when the recovery share appears on an invoice. During the pilot one named person per brand must be able to approve actions in the first weeks.

In year two a marketplace account manager becomes a user through a scoped read-only view of a brand's open claims and evidence. That view exists in the MVP only to prove the second side is reachable.

Ideal customer profile: EUR 3-15m revenue, EUR 1-5m marketplace GMV, two or more of Bol, eBay, Amazon, Kaufland, Otto, on Shopify, Shopware or Magento, feeding through Channable or ChannelEngine. Disqualifiers: under EUR 1m marketplace GMV, arbitrage resellers, Amazon-only sellers, brands whose agency holds the credentials, settlement data that lives only in PDFs.

## 5. Product principles

These seven rules decide every design question in the backlog and are restated in `docs/architecture.md`.

API-native only. Every marketplace action goes through an official API, or is handed to a human as a prepared one-click submission. No browser automation, because eBay's user agreement and Amazon's policies forbid it and because a scraper is the one thing a marketplace can switch off.

Everything is an event on the trade record. Orders, shipments, returns, settlement lines, findings, claims, credits, price changes and messages are rows keyed to one tenant, one marketplace and one external id. No state hides in a job.

Deterministic code reconciles, the model reasons. Matching, fee expectation and euro arithmetic are code with tests. Classification, evidence assembly, claim drafting, correspondence and exception handling are the model behind a fixed set of tools.

Every action passes one policy gate. Each tool declares its marketplace, reversibility, euro impact and action type; the gate decides autonomous, approval or refuse from the tenant's caps and the trust ramp.

Audit before side effect. Agent runs, tool calls, gate decisions, approvals and outcomes are written to an append-only log before the action executes, never after.

One tenant, one boundary. Row-level security by tenant on every table, credentials per connection in Secret Manager, EU region, deletion on request.

Bill only what the record shows. A credit is billable only when it appears as an ingested settlement line linked to a claim. Headroom captured is counted from ingested orders. The meter and the ledger are the same rows.

## 6. Scope by module

Recover is the entry and the only module that runs for every customer. Free 90-day audit across every connected marketplace: every fee, commission, deduction, lost shipment and return credit the brand was owed and did not receive, with the deadlines that still apply, delivered as a PDF with a per-marketplace scorecard and a line-by-line annex. From day eleven the agent groups findings into claims with hashed evidence, files them by API where a marketplace offers one (eBay payment disputes and Post-Order cases, Kaufland tickets) and prepares a one-click case pack where it does not (Bol, Amazon, Otto), tracks every claim to credit, refusal or expiry, and matches credits back to claims. Priced at 25% of credits received, invoiced monthly, nothing upfront.

Reconcile makes the audit continuous: every settlement matched to orders, margin per marketplace after fees, fee-change alerts, a finance-ready monthly statement and a CSV export. EUR 390 a month.

Comply holds listings and content to each marketplace's spec: required attributes, images, GPSR contact data, fitment coverage for parts, content drift detection, unauthorised-seller monitoring from competing offers. Fixes are proposed with a diff and applied through the content APIs. EUR 690 a month.

Serve handles buyer and marketplace correspondence: Amazon Messaging, eBay messaging, Kaufland tickets, Otto messaging, and a forwarded mailbox for Bol, which has no messaging API. Replies are drafted inside the tenant's policies; returns and cancellations are decided through the returns APIs; deadlines such as eBay's five-day dispute window are tracked. EUR 690 a month.

Price sets prices from reconciled net margin per marketplace, not from a typed minimum: competitor snapshots (Bol Competing Offers, Amazon competitive pricing and featured-offer expected price, eBay Browse by GTIN), a cost-layer model per product, and a governor with tenant bands, a per-marketplace ceiling relative to the brand's own trailing price, cooldowns and meaningful increments. Moves up toward the competitive ceiling when the brand sits below the competition, down to win the buy box when margin allows. EUR 490 a month plus 10% of headroom captured.

Grow reads ad reports from Amazon Ads, Bol Advertising and eBay Promoted Listings, attributes ad cost into margin per marketplace, produces a weekly report and proposes campaign budgets through the gate. No autonomous campaign creation in the MVP. EUR 990 a month plus 5% of ad spend.

The full channel agent, all five modules for up to five marketplaces, is EUR 2,390 a month (EUR 1,990 without Price).

## 7. User journeys

Connect (day 0). The brand grants API access to its seller accounts and shop system: Bol client credentials, an eBay OAuth consent, an Amazon SP-API authorisation, Kaufland and Otto keys, a Shopify custom app. Where an API does not expose settlement history, the brand uploads 90 days of settlement, invoice and returns exports. Thirty minutes of the brand's time; the agent starts ingesting immediately.

Audit (day 1 to 10). Ingest runs for 90 days of history. The reconciliation engine matches settlement lines to order lines, computes fee expectations from the fee schedule and the Commissions API, and raises findings with amount, rule, confidence, evidence references and deadline. The audit PDF is generated and sent. The report is the brand's to keep whatever it finds.

Recover (day 11 onward). The agent drafts claims from findings. During the trust ramp every claim goes to the approval inbox, where the brand's approver can approve, edit or reject with a diff. Approved claims are filed by API or handed back as a one-click case pack. Outcomes are tracked; a credit appears as a new settlement line and is matched to its claim. Once an action type reaches 95% approval over 50 decisions it runs autonomously inside the tenant's euro caps.

Statement (monthly). A signed statement lists euros identified, filed, credited and refused, defects fixed, hours removed, and every action in the audit log. The invoice carries the recovery share computed from credited claims only, plus any module lines.

Expand (from day 60). The brand switches on modules one at a time from the customer console. Each module adds scheduled tasks, tools and policy rows; none adds a table the record does not already have.

## 8. Functional requirements

Connections and ingest. FR-1: one connector per marketplace behind a shared interface with a capability matrix declaring which capabilities are API, assisted or none. FR-2: ingest orders, shipments, returns, settlements, fees and invoices with idempotent upserts keyed on tenant, marketplace and external id; re-running any window produces zero duplicates. FR-3: raw payloads are archived before parsing. FR-4: rate limits are respected per marketplace from response headers with exponential backoff, and one marketplace's limits cannot stall another's queues. FR-5: sync cadences run on a scheduler: orders hourly, settlements daily, competing offers on a tiered clock. FR-6: where an API does not expose a stream, the customer uploads exports and the parser produces the same rows.

Reconciliation and findings. FR-7: fee schedules per marketplace and category live in code with effective dates. FR-8: every order line carries a fee expectation (commission, fixed fee, ad cost). FR-9: settlement lines are matched to order lines by external reference first, then by order id and amount within a window. FR-10: detectors are pure, tested functions for commission overcharge, fixed-fee error, duplicate charge, lost shipment without compensation, return compensation shortfall, FBA lost or damaged inventory without reimbursement, refund without return, and ad charge above expectation. FR-11: a finding carries type, amount, confidence, evidence references, deadline and a status of open, claimed, credited, refused or expired. FR-12: the audit PDF is generated per tenant with a per-marketplace scorecard and a line-by-line annex. FR-13: the recoverable pool per marketplace is a measured metric, never a benchmark.

Claims. FR-14: the claims rail has three modes: api (the agent files and tracks), assisted (the agent prepares text, evidence and a deep link; a human submits in one click; the agent tracks), and track (outcome only). FR-15: eBay payment disputes are contested and evidenced by API; Kaufland claims are filed as tickets by API. FR-16: Bol and Amazon case packs contain the claim text, the evidence bundle and the deep link into the seller portal, and are confirmed as submitted by a human before tracking starts. FR-17: evidence is stored with a sha256 hash and source; claim events record every state change. FR-18: a credit is a settlement line linked to a claim, matched by external case id first and by order id and amount within 5% and 60 days second; a settlement line can credit at most one claim.

Agent runtime and policy gate. FR-19: the runtime is a tool-calling loop per task with a fixed tool set: read_finding, read_evidence, draft_claim, submit_claim, add_evidence, reply_message, propose_listing_fix, apply_listing_fix, propose_price, apply_price, request_approval, escalate. FR-20: each tool declares reversibility, action type and a euro impact estimator. FR-21: the gate reads the tenant's policy for the action type and returns autonomous, approval or refuse with a reason; default policy for a new tenant is approval for every action type. FR-22: caps in the MVP are EUR 1,000 per claim and EUR 5,000 filed per tenant per day; refunds, purchase orders, account settings and delistings are refused regardless of policy. FR-23: autonomy is granted per action type at 95% approval over at least 50 decisions and revoked on any refused execution. FR-24: every run records model, tokens, cost and duration; cost per claim is visible in the ops console.

Approval and audit. FR-25: the approval inbox shows the proposed action with a diff, and supports approve, edit and reject; an edited approval records both versions. FR-26: audit events are append-only (no update or delete for any role), hash-chained per tenant, and written before the side effect; the runtime cannot execute a tool until the proposed event is committed. FR-27: the audit log is filterable by tenant, action type, marketplace and outcome.

Correspondence (Serve). FR-28: message threads and messages are ingested from Amazon Messaging, eBay messaging, Kaufland tickets and Otto messaging, and from a Postmark inbound mailbox for Bol with thread matching by order id. FR-29: replies are drafted inside tenant policies (returns, cancellations, tone, a refusal list) and go through the gate. FR-30: deadlines per marketplace are tracked and surfaced before they lapse.

Listings (Comply). FR-31: listing spec rules per marketplace check required attributes, images, GPSR contact data and fitment coverage for parts. FR-32: content hashes detect drift; fixes are proposed with a before-and-after diff and applied through Bol Offers and Product Content, Amazon Listings Items and Feeds, and eBay Inventory. FR-33: competing offers are scanned for unauthorised sellers of the brand's products.

Pricing (Price). FR-34: competitor snapshots are collected per listing with a tiered refresh (featured-offer expected price for high-velocity SKUs only). FR-35: a net-margin model per product and marketplace subtracts commission, fixed fee, ad cost and expected returns from price. FR-36: the governor refuses any move outside the tenant's bands, above the per-marketplace ceiling relative to the brand's trailing price, inside a cooldown, or in increments below the marketplace's meaningful step. FR-37: price changes record the buy-box state before and after; headroom entries count price delta times units sold while featured, from ingested orders. FR-38: pricing acts on one brand's own data only; competitor data is never pooled across tenants into a shared model.

Advertising (Grow). FR-39: ad reports are read from Amazon Ads, Bol Advertising and eBay Promoted Listings and attributed into margin per marketplace. FR-40: budget proposals go through the gate; the MVP creates no campaigns autonomously.

Billing and statements. FR-41: Stripe customers with SEPA and card; invoices carry recovery-share lines computed only from credited claims and module lines per tenant. FR-42: the monthly statement PDF lists identified, filed, credited, refused, defects fixed, hours removed and the action log, and is signed. FR-43: modules are switched on and off per tenant from the customer console; a module switch changes policies, schedules and tool availability and nothing else.

Consoles. FR-44: the customer console shows connections, findings, claims, the approval inbox, statements and module switches. FR-45: the ops console shows tenants, runs, costs, queue health and the day-120 metrics. FR-46: a marketplace account manager can be given a scoped, read-only link to one tenant's open claims and evidence.

## 9. Marketplace capability routing

| Capability | Bol | Amazon | eBay | Kaufland | Otto | Shopify |
|---|---|---|---|---|---|---|
| Ingest orders, shipments, returns | API | API | API | API | API | API |
| Ingest settlements, fees, invoices | API | API (reports, Finances) | API (Finances) | API (verify detail) | API (receipts) | API (payouts) |
| Detect errors and shortfalls | code | code | code | code | code | n/a |
| File claims with evidence | assisted | assisted | API | API (tickets) | assisted | n/a |
| Track claims to credit | API + mail | API + mail | API | API | API | n/a |
| Fix listings and content | API | API | API | API | API | API |
| Correspondence | mailbox only | API | API (verify) | API | API | n/a |
| Competing offers and price changes | API | API | API | API (verify) | none | own price |
| Sponsored placements | API (separate access) | API (separate approval) | API | none | none | n/a |

The claims rail is the only capability that fragments, so it is one abstraction with three modes and eBay is the first marketplace where the full loop runs by API. Amazon's developer registration, role approvals and Ads API application are the long poles and are filed on day 0.

## 10. Pricing and metering

Audit: free. Recovery: 25% of each credit received, invoiced monthly against credits visible in the brand's own settlements, no monthly fee, no upfront, no minimum, cancel any time. Modules: Reconcile EUR 390, Comply EUR 690, Serve EUR 690, Grow EUR 990 plus 5% of ad spend, Price EUR 490 plus 10% of headroom captured, per month, cancel any month. Full agent EUR 2,390 (EUR 1,990 without Price).

The billable event for recovery is a settlement line of type compensation, correction, reimbursement or dispute payout that is linked to a claim. The billable event for Price is a headroom entry derived from ingested orders. Neither can be created by the agent, an operator or a customer directly; both come only from ingested data.

## 11. Data, security and compliance

Environments: development and the first pilots run on a local Docker environment (Supabase CLI stack, Redis, Mailpit, telemetry collector) and CI runs the same services; the code talks to a secrets provider, a storage provider and telemetry that are switched to their cloud implementations by configuration. Google Cloud is provisioned only after a recorded go decision (SEEN-007), planned in Sprint 2 before external pilot users depend on the inbox. Target hosting on GCP europe-west4: Cloud Run for api, worker and web, Memorystore Redis, Supabase Postgres, Auth and Storage in the EU, Cloud Scheduler, Secret Manager, Cloud Logging and Trace. Every table carries tenant_id with row-level security. Credentials are stored per connection in the secrets provider (.env.local locally, Secret Manager after go-live) and read at job time, never persisted in the database. Amazon's data protection policy governs buyer PII: names and addresses are not persisted beyond what a claim needs, are encrypted at rest and expire after 30 days. Evidence is hashed on write. Backups are daily with point-in-time recovery. Deletion on request removes a tenant's rows and storage within 30 days. Customer data is never shared with a marketplace or another brand; the FeedMind customer list is never used for outreach. Disputes are filed as the brand, from the brand's accounts, within each marketplace's rules and at volumes a human team could file.

## 12. Non-functional requirements

Idempotency on every ingest and every tool execution (input hash). Per-tenant job keys so one tenant's backlog cannot starve another. Rate-limit compliance per marketplace with backoff from headers, tested with a chaos test. OpenTelemetry traces and per-tenant cost logging. Minimum one instance for api and worker. Load test at 50 tenants of ingest before day 120. RLS penetration tests and a restore drill from backup before day 120. Agent cost per claim tracked against the gross-margin model (recovery-only customers 55-70% gross margin, modules 75-85%).

## 13. Success metrics and gates

Each sprint ends with a gate that has to be proven before the next one starts; a missed gate moves the following sprint and never trims the gate. G0 (9 Oct): three marketplaces ingesting 90 days for one brand, zero duplicates on re-run. G1 (23 Oct): three audit PDFs delivered, recoverable pool measured per marketplace. G2 (6 Nov): ten claims filed across two marketplaces, every action approved and logged, a credit matched to a claim. Bake-off (31 Oct): two signed pilots. G3 (20 Nov): a Stripe invoice from credited claims only, Reconcile on for a paying tenant. POC gate (30 Nov): three brands connected and audited, credits received in at least two, one paid module started. G4 (4 Dec): listing fixes applied by API on three marketplaces, Kaufland tickets by API. G5 (18 Dec): one claim type autonomous at 95% over 50 decisions, Serve replies sent. G6 (15 Jan): governor refuses out-of-band moves, live price changes with buy-box outcome, headroom reconciles to orders. G7 (29 Jan): the day-120 metrics pack.

Day-120 targets: ten brands live, EUR 20-25k MRR, EUR 150k or more identified and filed, EUR 60k or more credited, 70% or more of claim actions autonomous, one retailer reading, gross margin per tenant and agent cost per claim reported.

## 14. Release plan

Eight two-week sprints from 28 September 2026, holiday buffer 21 December to 1 January, day 120 on 26 January 2027. Sprint 0 the development harness, the local Docker environment, foundations, three read connectors, ingest and day-0 registrations. Sprint 1 reconciliation engine, findings, audit PDF. Sprint 2 claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching, and the Google Cloud go-live if the go/no-go says so. Sprint 3 Reconcile module, Stripe billing, statements, Shopify. Sprint 4 Comply v1 and Kaufland. Sprint 5 Serve v1, forwarded mailbox, trust ramp, Otto. Sprint 6 Price module v1. Sprint 7 Grow v1, retailer read-only view, hardening, day-120 metrics. The full calendar, gates, capacity assumptions and risks are in `docs/development-plan.md`; the 85 tickets are in `docs/tickets/`.

## 15. Risks

Amazon role approval slower than Sprint 2: file on day 0, run Sprint 2 on eBay and Bol, fold Amazon in when approved. Bol's compensation request has no structured form: the case pack becomes copy-ready text plus evidence files, still one click plus paste. Fewer than three friendly brands by 12 October: the partner's automotive network is the fallback and the audit runs on exported files where an API key is late. Recovery pool on Amazon under 0.5% of GMV after the 2025 policy changes: lead with fees, ad attribution and the non-Amazon marketplaces, and report the measured pool honestly. Upward repricing trips Amazon's Fair Pricing Policy: the ceiling governor is relative to the brand's own trailing price and Price runs on eBay and Bol first. A marketplace ships its own agent: never wedge on Amazon; own the claims no marketplace files against itself and the record both sides read.

## 16. Open questions

Bol OAuth grant type and numeric rate limits per endpoint family; Amazon report names for FBA inventory adjustments and the Finances transactions version; availability of the featured-offer expected-price endpoint in EU marketplaces and the approval lead time for the Finance and Accounting, Buyer Communication, Pricing and Product Listing roles; eBay Trading messaging deprecation status and Finances method names; Kaufland settlement and virtual buy-box endpoints; Otto rate limits; Shopify Payments payout scopes; whether Bol's compensation request has any structured fields the case pack can pre-fill. Each is a human ticket in the sprint where it is first needed.

## 17. Glossary

Trade record: the tenant-scoped set of tables holding orders, shipments, returns, settlements, findings, claims, credits, messages, price changes and audit events. Finding: a detected discrepancy with an amount, a rule and a deadline. Claim: one or more findings submitted to a marketplace. Case pack: the prepared text, evidence and deep link a human submits in one click where no claims API exists. Credit: a settlement line linked to a claim; the only billable recovery event. Policy gate: the component that decides autonomous, approval or refuse for every proposed action. Trust ramp: the per-action-type approval rate that earns autonomy. Headroom: price delta times units sold while featured, the billable event for Price. Module: a set of scheduled tasks, tools and policy rows switched on per tenant.
