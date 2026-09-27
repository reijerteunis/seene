-- Trade record v1, part 1 of 4: tenancy, the policy helper, and the order and
-- settlement tables. SEEN-008.
--
-- Everything is an event on the trade record: orders, shipments, returns and
-- settlement lines are rows keyed to one tenant, one marketplace and one external
-- id, never state hidden in a job. One tenant, one boundary: every table carries
-- tenant_id and row-level security, and the policy expression is written once,
-- below, as seen.current_tenant(). Twenty-nine copies of that expression would be
-- twenty-nine places for it to be subtly different.
--
-- Amounts are integer cents in bigint with a three-letter currency code beside
-- them, because floating point money is how a reconciliation drifts. Credentials
-- are never stored here: connections carry a reference the secrets provider
-- resolves at job time.
--
-- Forward only. The local stack is reset rather than rolled back, and nothing is
-- deployed to a cloud project until the SEEN-007 go decision, so a down migration
-- would be code nobody has run.

create schema if not exists seen;
comment on schema seen is
  'Helpers the tenancy policies read. Not exposed through the Data API: only the '
  'public schema is, so a function here is reachable from a policy and not from a request.';

grant usage on schema seen to anon, authenticated, service_role;

-- The tenant of the request now being served, or null when the request carries no
-- tenant at all.
--
-- The claim is named `tenant_id` and is read from `request.jwt.claims`, which is
-- the setting PostgREST fills per request from the verified access token. Nothing
-- else in this repository records that name: it is this migration's decision, and
-- whoever wires Supabase Auth in the web application has to put `tenant_id` into
-- the access token (an access-token hook, or app_metadata copied into the claim)
-- or every policy below will return null and every table will read as empty. That
-- is the intended failure: a tenancy helper that guessed a tenant when the claim
-- was missing would be a leak rather than an error.
--
-- Stable and not immutable, deliberately. The value is fixed within a statement
-- but changes between requests, and immutable would let the planner fold it into
-- a cached plan that a later request for a different tenant then reused.
create or replace function seen.current_tenant()
returns uuid
language sql
stable
parallel safe
set search_path = ''
as $$
  select nullif(
    coalesce(
      (nullif(current_setting('request.jwt.claims', true), '')::jsonb) ->> 'tenant_id',
      ''
    ),
    ''
  )::uuid
$$;

comment on function seen.current_tenant() is
  'The tenant of the current request, from the tenant_id claim in request.jwt.claims, '
  'or null when the request carries no claim. Every row-level security policy in the '
  'trade record compares tenant_id against this and nothing else.';

grant execute on function seen.current_tenant() to anon, authenticated, service_role;

-- updated_at that cannot lie: ingest upserts the same row many times, and a
-- column the writer has to remember to set is a column that is eventually wrong.
create or replace function seen.touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- Tenancy -------------------------------------------------------------------

create table public.tenants (
  tenant_id uuid primary key default gen_random_uuid(),
  name text not null,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.tenants is
  'One brand. Its own primary key is tenant_id, so the tenancy policy reads the same '
  'column name here as on every other table.';

create table public.users (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  email text not null,
  full_name text,
  role text not null default 'member',
  -- The id of the Supabase Auth user, written when the web application signs
  -- somebody in. No foreign key to auth.users: that table belongs to the auth
  -- service, and the ticket that wires Supabase Auth owns the link.
  auth_user_id uuid,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, email)
);

-- A static catalogue rather than an enum: adding a marketplace is a row, where a
-- type in use by twenty-nine tables would be a migration. Seeded per tenant with
-- the capability flags of the routing table by the third migration of this ticket.
create table public.marketplaces (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- bol, amazon, ebay, kaufland, otto, shopify.
  marketplace text not null,
  name text not null,
  -- One entry per capability, valued api, assisted, none, code or n/a, which is
  -- what the claims rail routes on: assisted and absent are different answers.
  capabilities jsonb not null default '{}'::jsonb,
  -- Commission and fixed-fee rates per category, read by the fee expectations.
  fee_schedule jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, marketplace)
);

create table public.connections (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  marketplace text not null,
  country text,
  -- The name the secrets provider resolves at job time. The credential itself is
  -- never in this database and never in code.
  credential_ref text,
  scopes text[] not null default '{}',
  status text not null default 'pending',
  -- The last successful sync per stream: orders, settlements, listings and the
  -- rest, so a connector resumes where it stopped rather than from the start.
  last_sync jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Catalogue ------------------------------------------------------------------

create table public.products (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  sku text not null,
  -- The barcode the marketplaces key on: Bol calls it the EAN and eBay the GTIN,
  -- and it is the same value under both names.
  ean text,
  title text,
  -- One entry per cost layer with the date it takes effect, in integer cents with
  -- its currency, which is what the net-margin model reads.
  cost_layers jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, sku)
);

create table public.listings (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  connection_id uuid not null references public.connections (id) on delete cascade,
  product_id uuid references public.products (id) on delete set null,
  external_offer_id text not null,
  price_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  stock integer,
  -- The hash of the content as the marketplace holds it, so drift is a comparison
  -- and not a diff of every field.
  content_hash text,
  spec_issues jsonb not null default '[]'::jsonb,
  -- Which vehicles or models the part is listed as fitting, for the fitment
  -- coverage the Comply module reads.
  fitment_coverage jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, connection_id, external_offer_id)
);

-- Orders ---------------------------------------------------------------------

create table public.orders (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  connection_id uuid not null references public.connections (id) on delete cascade,
  marketplace text not null,
  -- The marketplace's own order id. With tenant_id and marketplace it is the
  -- upsert key, which is what makes an ingest run idempotent.
  external_id text not null,
  placed_at timestamptz,
  status text,
  -- The currency of every amount on this order's lines.
  currency text not null default 'EUR' check (char_length(currency) = 3),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.order_lines (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  order_id uuid not null references public.orders (id) on delete cascade,
  product_id uuid references public.products (id) on delete set null,
  -- The marketplace's own line id, which is what a settlement line refers to.
  external_line_id text,
  sku text,
  ean text,
  quantity integer not null default 1,
  -- Integer cents in the order's currency.
  unit_price_cents bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.shipments (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  order_id uuid not null references public.orders (id) on delete cascade,
  marketplace text not null,
  external_id text not null,
  carrier text,
  tracking_code text,
  shipped_at timestamptz,
  delivered_at timestamptz,
  -- in_transit, delivered, lost: what the lost-shipment detector reads.
  status text,
  buyer_name text,
  buyer_address text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on column public.shipments.buyer_name is
  'Buyer PII. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump.';
comment on column public.shipments.buyer_address is
  'Buyer PII. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump.';

create table public.returns (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  order_id uuid not null references public.orders (id) on delete cascade,
  order_line_id uuid references public.order_lines (id) on delete set null,
  marketplace text not null,
  external_id text not null,
  rma text,
  condition text,
  handling_result text,
  -- What the marketplace owes back on this return, in integer cents.
  compensation_expected_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  returned_at timestamptz,
  status text,
  buyer_name text,
  buyer_address text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on column public.returns.buyer_name is
  'Buyer PII. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump.';
comment on column public.returns.buyer_address is
  'Buyer PII. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump.';

-- Settlements ----------------------------------------------------------------

create table public.settlements (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  connection_id uuid not null references public.connections (id) on delete cascade,
  marketplace text not null,
  external_id text not null,
  -- payout or invoice: the two shapes a marketplace settles in.
  kind text,
  period_start date,
  period_end date,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  total_cents bigint,
  -- Where the marketplace's own document for this settlement is archived.
  document_refs jsonb not null default '[]'::jsonb,
  settled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.settlement_lines (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  settlement_id uuid not null references public.settlements (id) on delete cascade,
  -- The order line this was matched to, deterministically, by SEEN-018. Null
  -- until it matches, and null forever for a line that refers to no order.
  order_line_id uuid references public.order_lines (id) on delete set null,
  marketplace text not null,
  external_id text not null,
  -- commission, fixed_fee, ad_charge, refund, adjustment, compensation or
  -- correction. Text and not a constrained type: an eighth kind arriving from a
  -- marketplace must land in the record and be reconciled, not rejected at ingest.
  line_type text not null,
  amount_cents bigint not null,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  description text,
  occurred_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.fee_expectations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  order_line_id uuid not null references public.order_lines (id) on delete cascade,
  -- What this line should have cost, from the marketplace fee schedule and the
  -- Commissions API, in integer cents. The detectors compare these against the
  -- settlement lines that actually arrived.
  expected_commission_cents bigint,
  expected_fixed_fee_cents bigint,
  expected_ad_cost_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- schedule or commissions_api: which of the two produced this expectation.
  source text,
  computed_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, order_line_id)
);

-- Idempotent ingest ----------------------------------------------------------
-- The externally sourced tables: one row per (tenant, marketplace, external id),
-- so reading the same page of a marketplace's API twice writes the row once.

create unique index orders_tenant_marketplace_external_id_key
  on public.orders (tenant_id, marketplace, external_id);
create unique index shipments_tenant_marketplace_external_id_key
  on public.shipments (tenant_id, marketplace, external_id);
create unique index returns_tenant_marketplace_external_id_key
  on public.returns (tenant_id, marketplace, external_id);
create unique index settlements_tenant_marketplace_external_id_key
  on public.settlements (tenant_id, marketplace, external_id);
create unique index settlement_lines_tenant_marketplace_external_id_key
  on public.settlement_lines (tenant_id, marketplace, external_id);

-- The paths every module reads on: a tenant's rows, and a parent's children.
create index connections_tenant_id_idx on public.connections (tenant_id);
create index listings_connection_id_idx on public.listings (connection_id);
create index orders_connection_id_placed_at_idx on public.orders (connection_id, placed_at);
create index order_lines_order_id_idx on public.order_lines (order_id);
create index shipments_order_id_idx on public.shipments (order_id);
create index returns_order_id_idx on public.returns (order_id);
create index settlements_connection_id_period_idx
  on public.settlements (connection_id, period_start);
create index settlement_lines_settlement_id_idx on public.settlement_lines (settlement_id);
create index settlement_lines_order_line_id_idx on public.settlement_lines (order_line_id);

-- Tenancy on every table -----------------------------------------------------
-- One loop over the tables this migration created, so the policy and the trigger
-- are written once and cannot differ per table. A name that is missing or a table
-- without tenant_id fails the migration here rather than leaving a table open.

do $$
declare
  target text;
begin
  foreach target in array array[
    'tenants', 'users', 'marketplaces', 'connections', 'products', 'listings',
    'orders', 'order_lines', 'shipments', 'returns', 'settlements',
    'settlement_lines', 'fee_expectations'
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

-- The Data API roles are granted nothing here, on purpose, and in particular not
-- the statement that grants on every table in the schema at once.
--
-- Nothing in this migration needs a table privilege: a migration runs as the owner
-- of the tables it creates, and the three request-bound roles reach these tables
-- only through a request, which part 4 of this set decides per table by name. A
-- grant on the whole schema written here would also reach the sixteen tables parts
-- 2 and 3 add later, and each of the three this set used to carry undid the revoke
-- the part before it had just written: `authenticated` was handed insert, update
-- and delete on settlement_lines, claims and invoices three times over that way,
-- and the tail of one migration is what the author of the next one copies. Grant
-- per table, by name, and say what the grant is for.
--
-- What is granted above is what a policy needs in order to be evaluated as
-- `authenticated` at all: usage on schema seen, and execute on
-- seen.current_tenant().
