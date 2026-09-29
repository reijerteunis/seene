-- Trade record v1, part 3 of 8: the commerce and billing tables, the marketplaces
-- catalogue and the key that binds a connection to it. SEEN-008.
--
-- Parts 1 and 2 created the tenancy, the policy helper seen.current_tenant(), the
-- orders and settlements, and the findings, claims and agent tables. These five are
-- what the Price module observes and what billing states: a competitor snapshot is
-- what a marketplace's offers looked like at one moment, a price change is what the
-- governor did about it, a headroom entry is what that change captured, and an
-- invoice and a statement are what the tenant is told and charged. Same rules as
-- before: tenant_id and row-level security on every table through the loop at the
-- foot of this file, amounts as integer cents in bigint with a three-letter
-- currency code beside them, vocabularies as text with their values in a column
-- comment rather than a constrained type.
--
-- The arithmetic is deliberately not here. Headroom is a price delta times the
-- units sold while featured, and that multiplication is a pure function with tests
-- in packages/core, not a generated column: deterministic code reconciles, and the
-- figure that is billed is written by the code that can be tested, so the two
-- factors and the product are all three columns rather than one expression the
-- database evaluates where no test can see it.
--
-- Forward only, as parts 1 and 2: the local stack is reset rather than rolled back.

-- Price: what was observed, what was changed, what it captured ----------------

create table public.competitor_snapshots (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  listing_id uuid not null references public.listings (id) on delete cascade,
  -- The competing offers as the marketplace returned them at this observation:
  -- seller, condition, price and delivery promise per offer, in the shape the
  -- connector read. Kept whole because a snapshot is evidence of what was seen,
  -- and a later ticket that wants a different field should not need a backfill.
  offers jsonb not null default '[]'::jsonb,
  -- Whether the brand's own offer held the featured position (the buy box) at this
  -- observation. Null when the marketplace does not say.
  best_offer boolean,
  -- The best competing price at this observation, in integer cents, lifted out of
  -- offers because the governor and the headroom meter compare on it and should
  -- not each parse the payload.
  best_offer_price_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  observed_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.competitor_snapshots is
  'What the competing offers on one listing looked like at one moment, on the tiered clock '
  'the Price module reads. No external id and so no upsert key: a snapshot is an observation '
  'and two observations of the same offers are two rows.';

create table public.price_changes (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  listing_id uuid not null references public.listings (id) on delete cascade,
  -- from and to in the ER diagram's words, spelled with the column they measure
  -- because `from` and `to` are reserved words and a quoted column name would be
  -- quoted in every query that ever reads it.
  from_price_cents bigint,
  to_price_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- Why the governor moved it: which rule fired, in the governor's own vocabulary
  -- (SEEN-072), so a price move can be explained to the tenant afterwards.
  reason text,
  -- The band check the governor performed before the move: the band, the floor and
  -- the ceiling it compared against, and whether the move passed. Recorded because
  -- a move that passed a check and a move nobody checked must be distinguishable.
  band_check jsonb not null default '{}'::jsonb,
  buy_box_before boolean,
  buy_box_after boolean,
  applied_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.price_changes is
  'One price move on one listing, with the band check that permitted it and the buy box '
  'before and after. The gate decision that allowed it is an agent_actions row and an '
  'audit_events row; this table holds what changed, not whether it was allowed.';

create table public.headroom_entries (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  price_change_id uuid not null references public.price_changes (id) on delete cascade,
  -- One row per price change per day, which is what the architecture counts
  -- headroom in. A date and not a timestamp: the day is the unit.
  counted_on date not null,
  -- The delta the change achieved per unit, in integer cents.
  price_delta_cents bigint,
  -- Units sold that day while the brand's offer was featured. Zero is a real
  -- answer and is not the same as no entry at all.
  units_sold integer,
  -- The delta times the units, in integer cents: what was captured that day and
  -- what the meter reports. Written by the tested function in packages/core rather
  -- than computed here, because euro arithmetic is code with tests.
  headroom_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, price_change_id, counted_on)
);

comment on table public.headroom_entries is
  'Headroom captured per price change per day: the meter and the ledger are the same table, '
  'so nothing else may state a headroom figure.';

-- Billing: what the tenant is charged and what it is told --------------------

create table public.invoices (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- Stripe's own ids, which are the authority on what was actually charged. The
  -- invoice is created in Stripe and mirrored here; nothing here charges anybody.
  stripe_invoice_id text,
  stripe_customer_id text,
  period_start date,
  period_end date,
  -- The recovery share lines: one entry per credited claim, each carrying the
  -- claim id, the credited amount and the share charged on it.
  --
  -- The ER diagram draws INVOICE }o--o{ CLAIM, a many-to-many, which would be a
  -- junction table. There is none, because the ticket's 29 tables do not name one
  -- and inventing a table nobody depends on yet is a guess at SEEN-040's shape;
  -- the lines carry the claim ids, so the relation is readable either way and
  -- SEEN-040 may normalise it when it knows what it needs. Recorded here so the
  -- divergence from the diagram is a decision and not an oversight.
  recovery_share_lines jsonb not null default '[]'::jsonb,
  -- The module subscription lines: which module, for which period, at what price.
  module_lines jsonb not null default '[]'::jsonb,
  total_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- draft, open, paid, void or uncollectible: Stripe's own vocabulary, mirrored
  -- from the webhook rather than invented here.
  status text not null default 'draft',
  issued_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, stripe_invoice_id)
);

comment on table public.invoices is
  'What the tenant was charged, mirrored from Stripe. A recovery share line exists only for a '
  'claim credited by an ingested settlement line: a credit is billable through that link and '
  'nothing here or in the console may write a billable event directly.';

create table public.statements (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- The invoice this statement accounts for, null for a period that was reported
  -- and not charged.
  invoice_id uuid references public.invoices (id) on delete set null,
  period_start date,
  period_end date,
  -- Where the storage provider holds the rendered PDF, and its hash, so the
  -- document a tenant was sent months ago is provably the one on file. The bytes
  -- are never in this database.
  storage_path text,
  sha256 text,
  -- What the statement states, in integer cents: recovered in the period and
  -- charged on it. Both are sums the code in packages/core computes from the
  -- credited claims, stored because a statement is a document that cannot change
  -- its figures after it was sent.
  total_recovered_cents bigint,
  total_charged_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, period_start, period_end)
);

comment on table public.statements is
  'The monthly statement as sent: the period, the document and the figures it states. The ER '
  'diagram has no statement entity; the prose at the foot of the trade record does, beside '
  'invoices, and this is that table.';

-- The paths the Price module and billing read on.
create index competitor_snapshots_listing_observed_at_idx
  on public.competitor_snapshots (listing_id, observed_at);
create index competitor_snapshots_tenant_observed_at_idx
  on public.competitor_snapshots (tenant_id, observed_at);
create index price_changes_listing_applied_at_idx on public.price_changes (listing_id, applied_at);
create index price_changes_tenant_applied_at_idx on public.price_changes (tenant_id, applied_at);
create index headroom_entries_price_change_id_idx on public.headroom_entries (price_change_id);
create index headroom_entries_tenant_counted_on_idx
  on public.headroom_entries (tenant_id, counted_on);
create index invoices_tenant_period_idx on public.invoices (tenant_id, period_start);
create index statements_invoice_id_idx on public.statements (invoice_id);

-- The marketplaces catalogue -------------------------------------------------
--
-- The problem, stated because the answer only makes sense beside it. The
-- architecture calls marketplaces a static catalogue: six rows, the same for
-- everyone, the routing table of docs/architecture.md turned into data the claims
-- rail and the connectors read. But public.marketplaces is a tenant table like
-- every other one, created that way in part 1 and given the same policy by the
-- same loop, and under that policy a row belongs to exactly one tenant. A single
-- global row would have a tenant_id of nobody and would therefore be invisible to
-- everybody: seeded, present, and unreadable by every request that needs it.
--
-- What was chosen. The catalogue is seeded once here, into
-- seen.marketplace_catalogue, and copied into public.marketplaces per tenant: by a
-- trigger when a tenant is created, and by the backfill below for the tenants that
-- already exist. So `pnpm db:reset` leaves a seeded catalogue on an empty database
-- with no tenants at all, which is criterion 1, and every tenant reads the six
-- marketplaces through the one tenancy policy with no exception spelled anywhere,
-- which is criterion 2. The copy is not redundancy for its own sake either: a fee
-- schedule is negotiated per contract, so a tenant's row is the place its own
-- schedule will land (SEEN-016), and the seed deliberately does not overwrite
-- fee_schedule when it runs again.
--
-- What was rejected, and why. A sentinel tenant id for the catalogue rows would
-- put a magic uuid into every query that reads a marketplace and into every
-- policy that has to let it through. A second, permissive select policy on
-- marketplaces would be an exception to the one tenancy expression, and an
-- exception in a policy is where a leak hides; criterion 2's uniformity is worth
-- more than six duplicated rows per tenant. A Postgres enum for the six
-- identifiers was rejected at the solution stage, because adding a marketplace
-- would then rewrite a type in use by twenty-nine tables.
--
-- Why the source lives outside public. seen.marketplace_catalogue belongs to no
-- tenant, so it has no tenant_id, and a table in public without tenant_id would
-- fail criterion 2's test, rightly: the answer is not to weaken that test but to
-- keep reference data out of the schema the test governs. Only the public schema
-- is exposed through the Data API (supabase/config.toml), no privilege on this
-- table is granted to anon, authenticated or service_role, and row-level security
-- is enabled on it with no policy at all, so nothing but the table's owner and the
-- security definer functions below can read it.

create table seen.marketplace_catalogue (
  marketplace text primary key,
  name text not null,
  -- One entry per capability of the routing table, valued as the table states it:
  -- {"mode": "api" | "assisted" | "code" | "none" | "none found" | "n/a",
  --  "detail": the rest of the cell, or null}. Never booleans: assisted and none
  --  are different answers and the claims rail routes on the difference.
  capabilities jsonb not null,
  created_at timestamptz not null default now()
);

comment on table seen.marketplace_catalogue is
  'The static marketplaces catalogue, seeded from the capability routing table in '
  'docs/architecture.md and copied into public.marketplaces per tenant. Outside public so it '
  'is outside the Data API and outside the tenancy rule it could not satisfy, because it '
  'belongs to no tenant. packages/core/db/marketplaces.test.ts parses the document at test '
  'time and compares it against these rows, so an edit to the table in the document fails the '
  'test rather than leaving the catalogue quietly behind it.';

alter table seen.marketplace_catalogue enable row level security;

insert into seen.marketplace_catalogue (marketplace, name, capabilities) values
  ('bol', 'Bol', '{
    "ingest_orders": {"mode": "api", "detail": null},
    "ingest_settlements": {"mode": "api",
      "detail": "Invoices + specifications, Commissions per EAN"},
    "detect_errors": {"mode": "code", "detail": "on ingested data"},
    "file_claims": {"mode": "assisted", "detail": "partner platform form; no API"},
    "track_credit": {"mode": "api",
      "detail": "(credit appears in invoice specification) plus inbound mail"},
    "fix_listings": {"mode": "api", "detail": "Offers, Product Content"},
    "buyer_messages": {"mode": "none", "detail": "by API (assisted via inbox)"},
    "competing_offers": {"mode": "api", "detail": "Competing Offers by EAN, Offers"},
    "sponsored_placements": {"mode": "api", "detail": "Advertising API, separate access"}
  }'::jsonb),
  ('amazon', 'Amazon (SP-API)', '{
    "ingest_orders": {"mode": "api", "detail": "Orders, Reports"},
    "ingest_settlements": {"mode": "api",
      "detail": "settlement, reimbursement, returns and fee reports; Finances"},
    "detect_errors": {"mode": "code", "detail": "on ingested data"},
    "file_claims": {"mode": "assisted",
      "detail": "Seller Central case; no API, confirmed by Amazon"},
    "track_credit": {"mode": "api",
      "detail": "(reimbursement and settlement reports) plus inbound mail"},
    "fix_listings": {"mode": "api", "detail": "Listings Items, Feeds"},
    "buyer_messages": {"mode": "api", "detail": "Messaging, Solicitations"},
    "competing_offers": {"mode": "api",
      "detail": "Product Pricing incl. featured-offer expected price"},
    "sponsored_placements": {"mode": "api", "detail": "Amazon Ads API, separate approval"}
  }'::jsonb),
  ('ebay', 'eBay', '{
    "ingest_orders": {"mode": "api", "detail": "Fulfillment, Post-Order"},
    "ingest_settlements": {"mode": "api", "detail": "Finances: transactions, payouts"},
    "detect_errors": {"mode": "code", "detail": "on ingested data"},
    "file_claims": {"mode": "api",
      "detail": "payment disputes: contest, add evidence; Post-Order cases"},
    "track_credit": {"mode": "api", "detail": "dispute status, Finances"},
    "fix_listings": {"mode": "api",
      "detail": "Inventory, Feed; Trading compatibility for fitment"},
    "buyer_messages": {"mode": "api", "detail": "Trading messaging, verify deprecation"},
    "competing_offers": {"mode": "api", "detail": "Browse by GTIN; Inventory"},
    "sponsored_placements": {"mode": "api", "detail": "Marketing: Promoted Listings"}
  }'::jsonb),
  ('kaufland', 'Kaufland', '{
    "ingest_orders": {"mode": "api", "detail": null},
    "ingest_settlements": {"mode": "api",
      "detail": "reports, invoices; settlement detail to verify"},
    "detect_errors": {"mode": "code", "detail": null},
    "file_claims": {"mode": "api", "detail": "tickets"},
    "track_credit": {"mode": "api", "detail": "tickets"},
    "fix_listings": {"mode": "api", "detail": null},
    "buyer_messages": {"mode": "api", "detail": "tickets"},
    "competing_offers": {"mode": "api", "detail": "virtual buy box, verify"},
    "sponsored_placements": {"mode": "none found", "detail": null}
  }'::jsonb),
  ('otto', 'Otto', '{
    "ingest_orders": {"mode": "api", "detail": null},
    "ingest_settlements": {"mode": "api", "detail": "receipts"},
    "detect_errors": {"mode": "code", "detail": null},
    "file_claims": {"mode": "assisted", "detail": null},
    "track_credit": {"mode": "api", "detail": "receipts"},
    "fix_listings": {"mode": "api", "detail": null},
    "buyer_messages": {"mode": "api", "detail": "messaging"},
    "competing_offers": {"mode": "none found", "detail": null},
    "sponsored_placements": {"mode": "none found", "detail": null}
  }'::jsonb),
  ('shopify', 'Shopify', '{
    "ingest_orders": {"mode": "api", "detail": "truth for stock, product"},
    "ingest_settlements": {"mode": "api", "detail": "Shopify Payments payouts"},
    "detect_errors": {"mode": "n/a", "detail": null},
    "file_claims": {"mode": "n/a", "detail": null},
    "track_credit": {"mode": "n/a", "detail": null},
    "fix_listings": {"mode": "api", "detail": null},
    "buyer_messages": {"mode": "n/a", "detail": null},
    "competing_offers": {"mode": "none", "detail": "own price only"},
    "sponsored_placements": {"mode": "n/a", "detail": null}
  }'::jsonb);

-- The copy, per tenant. Security definer because the row it writes belongs to a
-- tenant the writer may not be: whoever creates a tenant must not have to be that
-- tenant to give it its catalogue, and under the tenancy policy an insert as
-- `authenticated` would be refused for the tenant that was created a statement
-- ago. The function is revoked from public below, so the only caller is the
-- trigger and this migration.
--
-- fee_schedule is not in the update: a tenant's negotiated schedule survives a
-- reseed, which is what a later change to the capabilities of the document will
-- do to every tenant at once.
create or replace function seen.seed_marketplaces(target uuid)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into public.marketplaces (tenant_id, marketplace, name, capabilities)
  select target, c.marketplace, c.name, c.capabilities
    from seen.marketplace_catalogue c
  on conflict (tenant_id, marketplace) do update
    set name = excluded.name,
        capabilities = excluded.capabilities;
$$;

comment on function seen.seed_marketplaces(uuid) is
  'Copies the static catalogue into one tenant''s rows of public.marketplaces, leaving that '
  'tenant''s own fee_schedule alone.';

create or replace function seen.seed_marketplaces_for_new_tenant()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform seen.seed_marketplaces(new.tenant_id);
  return null;
end;
$$;

create trigger seed_marketplaces after insert on public.tenants
  for each row execute function seen.seed_marketplaces_for_new_tenant();

revoke all on function seen.seed_marketplaces(uuid) from public;
revoke all on function seen.seed_marketplaces_for_new_tenant() from public;

-- The tenants that already exist, so the catalogue is not a promise to future
-- tenants only. On a fresh `pnpm db:reset` this loop finds none, which is the
-- point of seeding the source table above rather than only the copies.
do $$
declare
  existing uuid;
begin
  for existing in select tenant_id from public.tenants loop
    perform seen.seed_marketplaces(existing);
  end loop;
end;
$$;

-- A connection can only be to a marketplace in the catalogue -----------------
--
-- Left out of parts 1 and 2 deliberately: a key before the seed would have made
-- ingest depend on seeding order. It is a composite key on (tenant_id,
-- marketplace) rather than on marketplace alone, because the catalogue is held
-- per tenant, and that makes the key say something stronger as well: a connection
-- cannot point at another tenant's catalogue row.
--
-- No `on delete` clause, which is load bearing. The default is NO ACTION, whose
-- check is performed at the end of the statement rather than at the row, so the
-- cascade from tenants deletes a tenant's marketplaces and its connections in one
-- statement without the two racing; RESTRICT would refuse mid-statement and make
-- erasure on request impossible. `on update cascade` so renaming an identifier in
-- the catalogue carries the connections with it rather than orphaning them.
alter table public.connections
  add constraint connections_marketplace_fkey
  foreign key (tenant_id, marketplace)
  references public.marketplaces (tenant_id, marketplace)
  on update cascade;

-- Tenancy on every table -----------------------------------------------------
-- The same loop as parts 1 and 2, over this migration's five tables: one policy
-- expression and one updated_at trigger, written once. A table without tenant_id
-- fails the migration here rather than being left open.

do $$
declare
  target text;
begin
  foreach target in array array[
    'competitor_snapshots', 'price_changes', 'headroom_entries', 'invoices', 'statements'
  ]
  loop
    if not exists (
      select 1 from pg_catalog.pg_attribute a
       where a.attrelid = format('public.%I', target)::regclass
         and a.attname = 'tenant_id' and a.attnum > 0 and not a.attisdropped
    ) then
      raise exception 'public.% has no tenant_id column, so it cannot carry the tenancy policy',
        target;
    end if;

    execute format('alter table public.%I enable row level security', target);
    execute format($p$
      create policy tenant_isolation on public.%I
        for all to authenticated
        using (tenant_id = seen.current_tenant())
        with check (tenant_id = seen.current_tenant())
    $p$, target);
    execute format($t$
      create trigger touch_updated_at before update on public.%I
        for each row execute function seen.touch_updated_at()
    $t$, target);
  end loop;
end;
$$;

-- As parts 1 and 2: no table privilege is granted here, and nothing is granted on
-- seen.marketplace_catalogue to any of the three request-bound roles at all. Part 4
-- decides the privileges of every table in the schema, per table and by name.
--
-- There is no second revoke of audit_events here either. It was here only because
-- the grant above it was, and once the grant is gone the revoke is a line that
-- looks like a guarantee and asserts nothing. Part 2 strips the default privileges
-- the table was created with and part 4 strips them again per table; this migration
-- does not touch audit_events.
