# Seen: MVP development plan

Eight two-week sprints from 28 September 2026 to 29 January 2027 and the gate each one has to pass. Tickets per sprint are listed in [docs/tickets/README.md](tickets/README.md).

## Shape of the plan

Eight two-week sprints from Monday 28 September 2026 to Friday 29 January 2027, preceded by four harness days from Thursday 24 September, with a two-week holiday buffer over Christmas. Day 120 of the MVP falls on Tuesday 26 January 2027. The plan is sequenced so that every sprint ends with something a customer touches: the first three sprints build only what the free audit and the recovery loop need, because those are what the POC gate on 30 November measures; the modules come after, one per sprint, in the order a customer would switch them on. The bake-off from the decision tab still stands: offers out by Friday 25 September, decision rule on 31 October. Sprint 0 and Sprint 1 are the "build the free artefact semi-manually on real data" step from that tab, done properly: the audit engine is product code from the first day because the audit is the sales process.

## Team and capacity

The harness comes first. Seven tickets (SEEN-086 to SEEN-092, 27 build points) build the Seen harness from 24 September, four days before Sprint 0 opens, and SEEN-007 and SEEN-008 depend on the last of them, so no product ticket opens until the harness is green. That is why Sprint 0 carries 68 build points on a 16-day calendar instead of 40 on 10 days. The harness is described in `docs/harness/workflow.md`.

One builder (Ruud, driving Claude Code, full days from 28 September once the Partao position is settled), one business partner on sales, design partners and the automotive network, no hires before the POC gate. Estimates are in points, where one point is roughly two hours of builder attention with Claude Code doing the typing, so a two-week sprint holds about 40 points of build plus the human tasks. Human tasks (registrations, contracts, sales conversations, approvals in the pilot inbox) carry a separate executor flag and are not counted against the build capacity. If a second builder joins in Sprint 3 or later, the modules from Sprint 4 onward are the parallel track; Sprints 0 to 2 are sequential by nature.

## Sprint calendar

| Sprint | Dates | Theme | Ends with |
|---|---|---|---|
| Sprint 0 | 24 Sep - 9 Oct | Harness first (from 24 Sep), then foundations, three read connectors, ingest, day-0 registrations | The Seen harness green (CLI, graphify, Jev gates, TDD and CI gates, security controls, KPI reports) before any product ticket opens; then one friendly brand's Bol, eBay and Amazon accounts ingesting into the trade record; raw archive; developer registrations and role requests filed |
| Sprint 1 | 12 - 23 Oct | Reconciliation engine, fee expectations, findings, audit PDF | Three real 90-day audits delivered as PDFs; the recoverable amount per marketplace measured on real settlement files |
| Sprint 2 | 26 Oct - 6 Nov | Claims rail, evidence, approval inbox, policy gate v1, audit log, credit matching | First claims filed (eBay by API, Bol and Amazon as one-click case packs); every action approved from the inbox and logged; credits matched to claims |
| Sprint 3 | 9 - 20 Nov | Reconcile module, Stripe billing, statements, Shopify | First invoice issued against credits received; the monthly statement; Reconcile switched on for one tenant |
| Sprint 4 | 23 Nov - 4 Dec | Comply v1, Kaufland connector, listing fixes by API | Listing defects found and fixed with a diff on Bol, Amazon and eBay; Kaufland ingesting and filing tickets; POC gate review on 30 Nov |
| Sprint 5 | 7 - 18 Dec | Serve v1, forwarded mailbox, trust ramp, Otto connector | Buyer and marketplace correspondence drafted and sent inside policy; first claim type running autonomously after 50 approved decisions |
| Buffer | 21 Dec - 1 Jan | Holiday; pilot inbox monitored, no releases | Clean backlog, retro, second-builder decision |
| Sprint 6 | 4 - 15 Jan | Price module v1: competitor snapshots, net-margin model, governor, headroom meter | Prices moving inside bands on one tenant's eBay and Bol listings; headroom captured counted from ingested orders |
| Sprint 7 | 18 - 29 Jan | Grow v1, retailer read-only view, hardening, day-120 metrics | Day-120 metrics pack for the seed narrative; load, security and restore drills passed |

## Gates

Gates are what the sprint has to prove before the next one starts; a missed gate moves the following sprint, it never trims the gate.

| Gate | Date | Proof |
|---|---|---|
| G0 Harness and ingest | 9 Oct | The harness passes its own dry run (one trivial ticket through all five stages and verify-delivery, journal and KPI record committed); orders, shipments, returns and settlement lines for 90 days from Bol, eBay and Amazon for one brand, idempotent re-runs produce zero duplicates, raw payloads archived, Amazon role requests and eBay growth check filed |
| G1 Audit | 23 Oct | Three audit PDFs delivered to three brands; findings carry amount, rule, evidence refs and deadline; the recoverable pool per marketplace is a measured number, not the US benchmark |
| G2 Recovery loop | 6 Nov | At least ten claims filed across two marketplaces; eBay disputes contested by API; Bol and Amazon case packs submitted by a human in one click; every action has an approval and an audit event; a credit matched to a claim in an ingested settlement |
| Bake-off | 31 Oct | Two signed pilots with cash or credits committed, per the decision tab; if not reached, the November conversation is about reach, not features |
| G3 Meter | 20 Nov | Stripe invoice generated from credited claims only; monthly statement signed and sent; Reconcile on for one paying tenant |
| POC gate | 30 Nov | Three brands connected and audited, credits received in at least two, one paid module started |
| G4 Comply | 4 Dec | Listing fixes applied by API on three marketplaces with before and after diffs; Kaufland tickets filed by API |
| G5 Autonomy | 18 Dec | One claim type at 95% approval over 50 decisions and running without approval inside caps; Serve replies sent on Amazon and eBay, Bol correspondence via mailbox |
| G6 Price | 15 Jan | Governor refuses moves outside bands and ceilings in tests; live price changes on one tenant with buy-box outcome recorded; headroom entries reconcile to orders |
| G7 Day 120 | 29 Jan | Metrics pack: brands live, euros identified, filed, credited, module MRR, autonomy rate per action type, gross margin per tenant, agent cost per claim; restore drill and pen-test findings closed |

## Day-0 checklist (human, before or during Sprint 0)

Amazon SP-API developer registration for a public application with the Finance and Accounting, Product Listing, Pricing and Buyer Communication roles requested on day 0 because approval takes weeks; the Amazon Ads API application filed the same day. eBay developer account, production keys, OAuth consent flow and the Application Growth Check request. Bol partner platform API credentials for the friendly brand and the client-credentials flow. Kaufland and Otto seller API keys come from each customer at connection time. Shopify custom app on the friendly brand's store. Postmark inbound domain for the forwarded mailbox. Stripe account with SEPA and card, EU VAT settings. GCP project in europe-west4, Supabase project in the EU, domain and DNS. Legal: Partao contract read for IP and non-compete, a data processing agreement and Amazon data protection policy compliance statement for pilots, terms for the recovery share (billable on credits received only).

## Not in the MVP

Zalando, Cdiscount, ManoMano and Autodoc Marketplace connectors (after day 120, in the order customers ask); the retailer-side product beyond a read-only view of open claims; purchase orders, refunds, account settings and delistings as agent actions (never in the MVP); repricing on Amazon until the Fair Pricing ceiling governor has run a month on eBay and Bol; a mobile app; SSO; anything a browser bot would need.

## Risks to the plan

Amazon role approval slower than Sprint 2: file on day 0, run Sprint 2 on eBay and Bol, fold Amazon in when approved. Bol compensation form with no structured fields: the case pack becomes copy-ready text and evidence files, still one click plus paste. Fewer than three friendly brands by 12 October: the partner's automotive network is the fallback list, and the audit runs on exported settlement files where an API key is late. Recovery pool on Amazon under 0.5%: the audit still finds Bol and eBay money, and the module conversion carries the plan; the day-120 pack reports the measured pool honestly.

