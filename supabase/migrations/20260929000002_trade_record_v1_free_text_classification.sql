-- Trade record v1, part 7 of 10: every column that can hold a sentence says
-- whether a buyer is in it. SEEN-008, F20.
--
-- What parts 1 to 3 wrote and what the test over them could not see. Six columns
-- are named buyer_name and buyer_address, each says in its own comment that it is
-- PII owing a 30-day expiry, and schema.test.ts read them back out of the
-- catalogue by asking for the columns whose name begins with `buyer`. The set it
-- searched for a column the inventory had missed was therefore the set of columns
-- already named for the buyer, and "no column named for the buyer is missing from
-- the list" is a sentence about itself. It is CODEX-02's shape a third time: a
-- deny-list that has to anticipate how the next thing is spelled.
--
-- Three columns hold a buyer's name and address by their own documented purpose
-- and none of them is spelled `buyer`. claims.claim_text is the text a marketplace
-- was told, as submitted, and a claim about a lost parcel cannot be made without
-- naming the person it was sent to. messages.body and message_threads.subject are
-- what a buyer typed, which is where a buyer writes their own delivery address.
-- None was in the inventory, none carried a comment, and SEEN-083's expiry job
-- would not have found one of them.
--
-- So the question is asked the way the tenancy clauses are asked, with a finite
-- answer. Every column in schema public whose type can hold prose is a candidate,
-- which is a hundred and twenty of them, arrays of text included; each one's own
-- comment begins either `Buyer PII` or `Not buyer PII` and a reason; and a
-- candidate that begins with neither fails the assertion and names itself. An
-- author who adds a column meets that failure rather than a silent pass, and the
-- only way through it is to have thought about the column.
--
-- Why a hundred and eleven reasons written by hand. The review that found this
-- expected most of the candidates to be bounded by a check constraint to a fixed
-- value set, which would have settled them without anybody's opinion. Not one is.
-- Part 2 decided that deliberately and says so, because "a value nobody
-- anticipated must land in the record and be reconciled, not rejected at ingest",
-- so status, mode, marketplace and direction are unconstrained text with their
-- vocabulary in a comment. The currency columns carry the only check in the
-- schema and it bounds a length rather than a value set. Constraining the
-- vocabularies to make this file shorter would be paying for a test with an
-- ingest that rejects rows, so the reasons are written out instead and each is
-- one a reviewer can disagree with on the merits.
--
-- The classification lives in the column's own comment and not in a list in
-- packages/core, because a list is a copy of the schema kept by hand and the copy
-- is what drifts, and because SEEN-083 deletes from this database rather than
-- from a TypeScript file. packages/core/db/tables.ts keeps BUYER_PII_COLUMNS, and
-- the assertion reads it against what the schema declares in both directions.
--
-- The six comments parts 1 and 2 already wrote are not repeated here: a comment
-- restated in two migrations is two comments that drift apart. This file adds the
-- three that were missing and classifies the hundred and eleven that hold no
-- buyer.
--
-- F31, from the fifth review, is the second way a classification goes wrong: not
-- by missing a column but by giving a reason that is false.
-- `message_threads.external_thread_id` said the identifier was one the rail
-- assigned, which holds on the four marketplace rails and does not hold on mail,
-- where a thread opened by a buyer is identified by the Message-ID the buyer's
-- own mail system generated, sending host and all.
-- `messages.external_message_id` said the same thing and is exposed once per
-- message rather than once per thread. Both stay `Not buyer PII`, and both now
-- say that this is an obligation on SEEN-062 rather than a fact about the column:
-- the mail rail stores a digest of the Message-ID and never the id itself, which
-- still deduplicates and still threads, and carries no host and no local part.
-- That is the form `audit_events.payload` and `claim_events.detail` already take
-- here. What keeps it honest is in packages/core/db/tables.ts, which lists the
-- four classifications that rest on a promise and requires each to name the
-- ticket the promise falls to, in both directions. No test can tell a true
-- reason from a false one, which is why this one survived four reviews.
--
-- Nothing here grants a privilege, creates a relation or changes a row. A comment
-- is the whole of this migration.

-- Buyer PII: the three the inventory did not have ----------------------------

comment on column public.claims.claim_text is
  'Buyer PII. The text a marketplace was told, as submitted, and a claim about a parcel that '
  'never arrived cannot be made without naming the person it was sent to and the address it '
  'was sent to. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump. '
  'Two rules meet in this column and SEEN-008 settles neither. It is kept verbatim because it '
  'is the record of what a marketplace was actually told, and buyer PII expires after 30 days: '
  'expiring it destroys that record, and keeping it breaks the rule. There are two ways out '
  'and SEEN-027 and SEEN-083 have to choose between them. Redact the buyer''s details in place '
  'once the 30 days are up, keeping the rest of the submitted text and marking the row as no '
  'longer verbatim, which is a record that says what was removed from it. Or never interpolate '
  'the buyer''s name and address into this column at all, filing them as evidence rows the '
  'claim refers to, which leaves the column verbatim for good and moves the expiry to '
  'evidence.buyer_name and evidence.buyer_address, where it already runs. The decision belongs '
  'to those two tickets and to their journals, not to this migration.';

comment on column public.message_threads.subject is
  'Buyer PII. What the thread is about in the words of whoever opened it, which on an inbound '
  'thread is the buyer: a subject line carrying an order number and the buyer''s own name is '
  'the ordinary case, not the odd one. Written by SEEN-061 from the marketplace messaging APIs '
  'and by SEEN-062 from the forwarded mailbox, so it is correspondence and never a vocabulary '
  'of ours. Written only as far as a claim or a reply needs it and expired after 30 days by '
  'SEEN-083. Encryption at rest is the storage layer only: the volume this database sits on, '
  'and the Supabase EU project once the SEEN-007 go decision is taken. The value itself is '
  'cleartext, so a pg_dump taken for a restore drill and any query as service_role read every '
  'tenant''s buyer data as typed. Nothing here encrypts the value itself, and no ticket owns '
  'doing so: column-level encryption is owed and unowned, a decision beyond SEEN-008 and one '
  'owed before SEEN-082 takes the first restore-drill dump.';

comment on column public.messages.body is
  'Buyer PII. What a buyer typed, which is where a delivery address arrives in a message about '
  'a parcel that never came, and what the agent typed back to them. Written by SEEN-061 from '
  'the marketplace messaging APIs, by SEEN-062 from the forwarded mailbox and by SEEN-063 when '
  'a reply is sent. Written only as far as a claim or a reply needs it and expired after 30 '
  'days by SEEN-083. Encryption at rest is the storage layer only: the volume this database '
  'sits on, and the Supabase EU project once the SEEN-007 go decision is taken. The value '
  'itself is cleartext, so a pg_dump taken for a restore drill and any query as service_role '
  'read every tenant''s buyer data as typed. Nothing here encrypts the value itself, and no '
  'ticket owns doing so: column-level encryption is owed and unowned, a decision beyond '
  'SEEN-008 and one owed before SEEN-082 takes the first restore-drill dump.';

-- Not buyer PII: the hundred and eleven, with the reason for each -------------
-- In the catalogue's own order, table by table, so a reader comparing this file
-- with the assertion's failure list reads the two in the same sequence.

comment on column public.agent_actions.action_type is
  'Not buyer PII. The action type the tool declared, which is the policies row the gate read. '
  'The value set is the tool set''s and no part of it comes from outside this repository.';
comment on column public.agent_actions.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.agent_actions.decision is
  'Not buyer PII. What the gate decided: autonomous, approval or refuse, and nothing else.';
comment on column public.agent_actions.input_hash is
  'Not buyer PII. The hash of the tool''s input rather than the input, which is how the same '
  'proposal is recognised across a retry without a second copy of what it contained. A hash '
  'of an address is not an address, though it does match one.';
comment on column public.agent_actions.outcome is
  'Not buyer PII. What came back: accepted, refused, pending or credited.';
comment on column public.agent_actions.tool is
  'Not buyer PII. The name of a tool in the fixed tool set. A name outside that set is not an '
  'action the runtime can take.';

comment on column public.agent_runs.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.agent_runs.model is
  'Not buyer PII. The model the run was executed on, named as this repository names it.';
comment on column public.agent_runs.trigger is
  'Not buyer PII. The queue and job that produced the task, which is our own scheduling.';

comment on column public.approvals.decided_by is
  'Not buyer PII. Who decided, and they are the tenant''s own operator rather than a buyer. '
  'Personal data of a user of the account, deleted when the tenant is and not thirty days '
  'after an order.';
comment on column public.approvals.decision is
  'Not buyer PII. approve, edit or reject, the three the approval inbox offers.';

comment on column public.audit_events.actor is
  'Not buyer PII. agent, system, or the tenant''s own operator who acted.';
comment on column public.audit_events.event_type is
  'Not buyer PII. What happened, from the runtime''s own vocabulary.';
comment on column public.audit_events.payload is
  'Not buyer PII, and it falls to SEEN-032 and SEEN-034 to keep it so. The gate records what '
  'it decided and the identifiers it decided about, never the buyer''s own words: a draft '
  'reply or a claim text copied in here would be buyer data in an append-only table, and no '
  '30-day expiry can reach it without breaking the guarantee the audit trail exists for. The '
  'draft belongs in messages.body and the submitted text in claims.claim_text, where the '
  'expiry job can find both.';

comment on column public.claim_events.detail is
  'Not buyer PII, and it falls to SEEN-027 to keep it so. What happened to the claim and when, '
  'by reference: the submitted text stays in claims.claim_text, where the expiry job looks, '
  'and a copy here would be a second one nobody is looking for.';
comment on column public.claim_events.event_type is
  'Not buyer PII. drafted, submitted, reminded, accepted, refused or credited.';

comment on column public.claims.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.claims.external_case_id is
  'Not buyer PII. The marketplace''s own case, dispute or ticket id, which the deadline watch '
  'follows.';
comment on column public.claims.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';
comment on column public.claims.mode is
  'Not buyer PII. api, assisted or track: how the claim is filed.';
comment on column public.claims.rule is
  'Not buyer PII. The entitlement being asserted, named from the templates in packages/core.';
comment on column public.claims.status is
  'Not buyer PII. draft, submitted, accepted, refused, credited or expired.';
comment on column public.claims.submitted_by is
  'Not buyer PII. The agent run or the person who submitted the claim, and the person is the '
  'tenant''s own operator rather than a buyer.';

comment on column public.competitor_snapshots.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.competitor_snapshots.offers is
  'Not buyer PII. The competing offers as the marketplace returned them: sellers, conditions, '
  'prices and delivery promises. A seller is a business on the other side of an offer and is '
  'never the buyer of an order.';

comment on column public.connections.country is
  'Not buyer PII. The country the connection trades in, as a code.';
comment on column public.connections.credential_ref is
  'Not buyer PII, and not a credential either: the name the secrets provider resolves at job '
  'time. The credential itself is never in this database and never in code.';
comment on column public.connections.last_sync is
  'Not buyer PII. One position per stream, so a connector resumes where it stopped.';
comment on column public.connections.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';
comment on column public.connections.scopes is
  'Not buyer PII. The scopes the marketplace granted this connection. It is an array of text '
  'and is a candidate for that reason: a list of strings holds an address as readily as one '
  'string does, and a classification that only looked at text would have walked past it.';
comment on column public.connections.status is
  'Not buyer PII. pending, active or failed: the state of the connection itself.';

comment on column public.evidence.sha256 is
  'Not buyer PII. The hash of the stored document, so a document produced months later is '
  'provably the one the claim was filed with.';
comment on column public.evidence.source is
  'Not buyer PII. Which rail produced the document: the marketplace API, a carrier, the '
  'tenant, or a report the agent assembled.';
comment on column public.evidence.storage_path is
  'Not buyer PII itself, and a pointer at something that is. A proof of delivery names the '
  'person it was delivered to inside the file, and this column is only where that file is '
  'kept. Expiring what this row carries therefore means deleting the object as well as '
  'clearing evidence.buyer_name and evidence.buyer_address, and reaching into storage is '
  'SEEN-083''s to do: nothing in this schema can.';

comment on column public.fee_expectations.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.fee_expectations.source is
  'Not buyer PII. Where the expectation came from: the encoded fee schedule or the '
  'marketplace''s own API.';

comment on column public.findings.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.findings.evidence_refs is
  'Not buyer PII. The rows and documents behind the finding, by id, before a claim exists to '
  'hang evidence rows from.';
comment on column public.findings.finding_type is
  'Not buyer PII. The detector''s own rule name, owned by SEEN-019 and SEEN-020.';
comment on column public.findings.status is
  'Not buyer PII. open, claimed, credited, refused or expired.';

comment on column public.headroom_entries.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';

comment on column public.invoices.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.invoices.module_lines is
  'Not buyer PII. Which module, for which period, at what price in integer cents.';
comment on column public.invoices.recovery_share_lines is
  'Not buyer PII. One entry per credited claim: the claim id, the credited amount and the '
  'share charged on it. Ids and integer cents, never the text of the claim.';
comment on column public.invoices.status is
  'Not buyer PII. Stripe''s own vocabulary, mirrored from the webhook: draft, open, paid, void '
  'or uncollectible.';
comment on column public.invoices.stripe_customer_id is
  'Not buyer PII. Stripe''s id for the tenant, who is the customer on this invoice. A buyer of '
  'an order is not a party to it at all.';
comment on column public.invoices.stripe_invoice_id is
  'Not buyer PII. Stripe''s own id for the invoice, which is the authority on what was '
  'charged.';

comment on column public.listings.content_hash is
  'Not buyer PII. The hash of the listing content as the marketplace holds it, so drift is a '
  'comparison rather than a diff of every field.';
comment on column public.listings.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.listings.external_offer_id is
  'Not buyer PII. The marketplace''s own offer id.';
comment on column public.listings.fitment_coverage is
  'Not buyer PII. Which vehicles or models the part is listed as fitting.';
comment on column public.listings.spec_issues is
  'Not buyer PII. The listing defects the Comply rules found, which are facts about the '
  'listing and not about anybody who bought from it.';

comment on column public.marketplaces.capabilities is
  'Not buyer PII. One entry per capability of the routing table, valued as that table states '
  'it.';
comment on column public.marketplaces.fee_schedule is
  'Not buyer PII. Commission and fixed-fee rates per category, read by the fee expectations.';
comment on column public.marketplaces.marketplace is
  'Not buyer PII. One of the six identifiers this catalogue defines.';
comment on column public.marketplaces.name is
  'Not buyer PII. The marketplace''s own display name.';

comment on column public.message_threads.channel is
  'Not buyer PII. marketplace or mail: which rail the thread is carried on, and therefore '
  'which one a reply goes back out through.';
comment on column public.message_threads.external_thread_id is
  'Not buyer PII, and it falls to SEEN-062 to keep it so on the mail rail. On the four '
  'marketplace rails this is the marketplace''s own thread id, assigned by the rail and chosen '
  'by nobody. Mail has no such id: a thread is identified by the root message''s own Message-ID, '
  'and where the buyer opened the thread that id was generated by the buyer''s mail system '
  'rather than by the rail that received it. By convention it carries the sending host to the '
  'right of the at sign and a local part the sending client chose, so it can name a provider, a '
  'company, or an account. The reason this column carried until F31, that the rail assigned the '
  'identifier, was true on four rails and false on the fifth. '
  'So SEEN-062 stores a digest of the root Message-ID and never the id itself. A digest is '
  'stable, so recognising a message the mailbox delivers twice and threading a reply onto what '
  'it answers both still work, and it carries neither a host nor a local part. '
  'Why a constraint on the writer and not the buyer PII classification. One column serves both '
  'rails, so marking it PII would expire marketplace thread ids that hold nothing about '
  'anybody; and expiry is the wrong instrument here in any case, because this id is what makes '
  're-ingest idempotent, so clearing it after 30 days turns every older thread into a new thread '
  'on the next sync and the record grows a duplicate per thread per sync. CLAUDE.md asks for '
  'buyer data to be kept only as far as a claim needs it, and what a claim needs is to know that '
  'two messages are one message, not which provider the buyer uses. Never writing the data is '
  'the stronger reading of that rule than writing it and deleting it thirty days later. '
  'What it costs, plainly: this is prevention with no detection. A digest and a raw Message-ID '
  'are both opaque text and nothing in this schema can tell them apart, and a check constraint '
  'on the shape would fix a digest format SEEN-062 has not chosen yet and would reject rows at '
  'ingest, which part 2 refused as a principle. So it is a promise made to a ticket nobody has '
  'written, and packages/core/db/tables.ts holds the promise in place rather than the behaviour.';
comment on column public.message_threads.status is
  'Not buyer PII. What SEEN-061 has done with the thread, in its own vocabulary.';

comment on column public.messages.direction is
  'Not buyer PII. inbound or outbound.';
comment on column public.messages.drafted_by is
  'Not buyer PII. agent, or the tenant''s own operator who wrote or edited the reply. Null on '
  'an inbound message, because nobody here drafted it.';
comment on column public.messages.external_message_id is
  'Not buyer PII, and it falls to SEEN-062 to keep it so on the mail rail, for the reason set '
  'out in full at message_threads.external_thread_id and with more of it here. On the '
  'marketplace rails this is the rail''s own id for the message. On mail every inbound message '
  'carries a Message-ID generated by the sender''s system, which on an inbound message is the '
  'buyer''s, rather than only the thread root carrying one: where the thread column is exposed '
  'once per thread, this one is exposed once per message. SEEN-062 stores a digest and never '
  'the id itself, which still recognises a message the mailbox delivers twice and still '
  'resolves an In-Reply-To onto the message it answers. The same promise, with the same absence '
  'of anything in this schema that could detect it being broken.';

comment on column public.order_lines.ean is
  'Not buyer PII. The barcode of the product on the line.';
comment on column public.order_lines.external_line_id is
  'Not buyer PII. The marketplace''s own line id, which is what a settlement line refers to.';
comment on column public.order_lines.sku is
  'Not buyer PII. The brand''s own article number for the product.';

comment on column public.orders.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.orders.external_id is
  'Not buyer PII. The marketplace''s own order id. The order it names was placed by a buyer, '
  'and the id is what the marketplace assigned rather than anything the buyer wrote or is '
  'called.';
comment on column public.orders.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';
comment on column public.orders.status is
  'Not buyer PII. The marketplace''s own order status, mapped by the connector.';

comment on column public.policies.action_type is
  'Not buyer PII. The action type the tools declare, which is the key the gate reads a policy '
  'by.';
comment on column public.policies.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.policies.mode is
  'Not buyer PII. autonomous, approval or refuse.';
comment on column public.policies.price_bands is
  'Not buyer PII. The bands and the per-marketplace ceiling the governor moves a price within, '
  'keyed by marketplace.';

comment on column public.price_changes.band_check is
  'Not buyer PII. What the governor compared before the move, and whether the move passed.';
comment on column public.price_changes.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.price_changes.reason is
  'Not buyer PII. Which rule fired, in the governor''s own vocabulary.';

comment on column public.products.cost_layers is
  'Not buyer PII. One entry per cost layer with the date it takes effect, in integer cents '
  'with its currency.';
comment on column public.products.ean is
  'Not buyer PII. The barcode the marketplaces key on.';
comment on column public.products.sku is
  'Not buyer PII. The brand''s own article number.';
comment on column public.products.title is
  'Not buyer PII. The product''s own title, which is the brand''s copy and nobody''s name.';

comment on column public.returns.condition is
  'Not buyer PII. What came back and in what state, in the marketplace''s vocabulary.';
comment on column public.returns.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.returns.external_id is
  'Not buyer PII. The marketplace''s own return id, part of the upsert key.';
comment on column public.returns.handling_result is
  'Not buyer PII. What was done with the returned item.';
comment on column public.returns.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';
comment on column public.returns.rma is
  'Not buyer PII. The return authorisation number the marketplace issued.';
comment on column public.returns.status is
  'Not buyer PII. The state of the return, in the marketplace''s vocabulary.';

comment on column public.settlement_lines.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.settlement_lines.description is
  'Not buyer PII. The marketplace''s own words for a charge, copied as read: it names the '
  'charge, the order and the item. No settlement format this ticket read puts a buyer''s name '
  'in one, and if a connector is found to ingest one that does, the column becomes buyer PII '
  'and this is the comment to change.';
comment on column public.settlement_lines.external_id is
  'Not buyer PII. The marketplace''s own line id, part of the upsert key.';
comment on column public.settlement_lines.line_type is
  'Not buyer PII. What kind of line it is: a commission, a shipping charge, a compensation and '
  'the rest, in the marketplace''s vocabulary.';
comment on column public.settlement_lines.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';

comment on column public.settlements.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.settlements.document_refs is
  'Not buyer PII. Where the settlement documents are held, by path.';
comment on column public.settlements.external_id is
  'Not buyer PII. The marketplace''s own settlement id, part of the upsert key.';
comment on column public.settlements.kind is
  'Not buyer PII. Which document this is: a settlement, an invoice or a payout.';
comment on column public.settlements.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';

comment on column public.shipments.carrier is
  'Not buyer PII. The carrier that took the parcel, which is a business.';
comment on column public.shipments.external_id is
  'Not buyer PII. The marketplace''s own shipment id, part of the upsert key.';
comment on column public.shipments.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines.';
comment on column public.shipments.status is
  'Not buyer PII. in_transit, delivered or lost: what the lost-shipment detector reads.';
comment on column public.shipments.tracking_code is
  'Not buyer PII. The carrier''s own code for the parcel. It is a key to the carrier''s record '
  'of the delivery, which does hold the address, and it is not the address.';

comment on column public.statements.currency is
  'Not buyer PII. A three-letter currency code, held to three characters by a check '
  'constraint, which is shorter than any name or any address.';
comment on column public.statements.sha256 is
  'Not buyer PII. The hash of the rendered statement, so the document a tenant was sent months '
  'ago is provably the one on file.';
comment on column public.statements.storage_path is
  'Not buyer PII. Where the rendered statement is held. A statement accounts for credited '
  'claims in figures and names no buyer.';

comment on column public.tenants.name is
  'Not buyer PII. The brand''s own name, which is a business.';
comment on column public.tenants.status is
  'Not buyer PII. The state of the tenant''s account with us.';

comment on column public.users.email is
  'Not buyer PII. The address of a user of the tenant''s own account. Personal data, and '
  'outside the 30-day buyer expiry: it is deleted when the tenant is, not thirty days after an '
  'order.';
comment on column public.users.full_name is
  'Not buyer PII. The name of a user of the tenant''s own account, on the same footing as '
  'users.email: personal data that goes when the tenant does.';
comment on column public.users.role is
  'Not buyer PII. What the user may do in the console.';
comment on column public.users.status is
  'Not buyer PII. The state of the user''s membership of the tenant.';
