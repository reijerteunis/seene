-- Trade record v1, part 9 of 10: an identifier is constrained to be what its own
-- comment says it is, and a row with two parents cannot disagree with either.
-- SEEN-008, F55, F56, F57, F59, F60, F61, F62 and F65.
--
-- What parts 1 to 8 got right and what they left as prose. Every table carries
-- tenant_id, every table has a policy, the tenant travels along every key, no
-- relation is born reachable, every column that can hold a sentence says whether a
-- buyer is in it, and a tenant id an erasure has consumed is spent. All of that is
-- about who may read a row and whose row it is. None of it is about whether the
-- identifiers in the row mean anything.
--
-- Seven columns are named marketplace and all seven carry the identical comment,
-- "One of the six identifiers the marketplaces catalogue defines". Exactly one of
-- them enforced it: connections.marketplace, keyed to public.marketplaces in part
-- 3. The other six were bare `text not null`, with no key, no check and no domain.
--
-- Measured against this stack before this file existed, as the role the workers
-- ingest with, every insert accepted:
--
--   marketplace       | external_id     the same order, three times, on one
--   ------------------+-------------   Bol connection, all three rows standing
--   bol               | ORD-1
--   BOL               | ORD-1
--   not-a-marketplace | ORD-1
--
--   external_id | order_mkt | conn_mkt    an Amazon order on a Bol connection
--   ORD-1       | amazon    | bol
--
--   shipments_for_one_bol_order = 2       one external id, two marketplaces
--
-- So the unique index acceptance criterion 4 names, on (tenant_id, marketplace,
-- external_id), is an idempotency key only for as long as a connector spells the
-- marketplace the same way twice: a connector that changes its spelling does not
-- collide with what it already wrote, it doubles the trade record. And the column
-- the fee expectations, the detectors and the claims rail are all routed by was
-- free to contradict the seller account the row was read through.
--
-- The same defect one join further out. A return carries order_id and
-- order_line_id and nothing required the line to be a line of that order: a return
-- of ORD-1 whose line belongs to ORD-2 was accepted. A settlement line carries
-- settlement_id and order_line_id and nothing required either to agree with it: a
-- line saying amazon under a settlement saying bol was accepted, and a bol
-- settlement line matched to an amazon order line was accepted. SEEN-018 matches
-- settlement lines to order lines deterministically and SEEN-019 and SEEN-020
-- detect the shortfalls from those joins, so what the database would be storing is
-- a match the detectors then read as truth.
--
-- And order_lines, which is the row every downstream number hangs off, had no
-- unique key of any kind on the line id the marketplace gave it. Three reads of
-- one order left three rows, one fee expectation forking into three, and a margin
-- three times the truth; the upsert SEEN-014 is specified to write could not be
-- expressed at all, because `on conflict` needs a unique index to arbitrate and
-- answered "there is no unique or exclusion constraint matching the ON CONFLICT
-- specification". message_threads and messages are the same omission on the rail
-- where a redelivery of the same page is ordinary rather than exceptional.
--
-- Why a key and not a check constraint, argued rather than assumed --------------
--
-- Part 2 refuses value-set check constraints on principle, and says why: "an
-- eighth kind arriving from a marketplace must land in the record and be
-- reconciled, not rejected at ingest". That principle is right and it is not about
-- this column. It was written about a marketplace-supplied value, a status or a
-- line type or a mode, where the vocabulary belongs to somebody else and the
-- honest answer to a value nobody anticipated is to store it. `marketplace` is not
-- supplied by a marketplace. It is the identifier this schema invents for one, it
-- is created by part 1 and seeded by part 3 from the capability routing table of
-- docs/architecture.md, and there is no sense in which Bol can send us a seventh
-- value of it. A row whose marketplace is `not-a-marketplace` is not an
-- unanticipated fact about the world that reconciliation will settle; it is a row
-- no connector, no fee schedule and no claims rail can do anything with.
--
-- A check constraint was rejected for a second reason on top of that one: it would
-- write the six identifiers into six tables, so adding a marketplace would be a
-- migration over all of them, which is the cost part 1 rejected an enum to avoid
-- and the reason the catalogue is a table of rows in the first place. A domain
-- carries the same cost with the type system in the way as well. The key reads the
-- catalogue, so adding a marketplace stays what part 1 promised it would be: a row.
--
-- Where the key points, which is the part worth reading twice. Only claims gets a
-- key straight to public.marketplaces, because a claim hangs from nothing else
-- that names a marketplace. Every other one is keyed to the parent it already
-- hangs from, carrying marketplace in the key the way part 5 carried tenant_id:
--
--   order_lines ------,
--   shipments --------+--> orders ----,
--   returns ----------'               +--> connections --> marketplaces
--   settlement_lines ----> settlements'
--   claims ---------------------------------------------> marketplaces
--
-- which says something strictly stronger than six keys to the catalogue would. Six
-- keys would make every value a real identifier and leave every row free to name a
-- different one from its parent, which is half the measurement above. The chain
-- makes the value real and makes it agree, in one constraint per table, and the
-- last link is the catalogue key part 3 already wrote.
--
-- What the chain is not: it is not six independent guarantees. It is one, and it
-- holds only while every link stands, so a later migration that loosens the key
-- from orders to connections loosens four columns and not one. That is the price
-- of saying the stronger thing, it is stated here rather than discovered, and the
-- self-check at the end of this file walks the chain from the catalogue outwards
-- so that a broken link fails a migration rather than a review.
--
-- order_lines gets a marketplace column it did not have, because the key from a
-- settlement line to the order line it matched has nothing to compare otherwise.
-- It is the only new column here and it is not a new fact: every other child of an
-- order already carries one. It is filled from the order by a trigger and refuses
-- a supplied value that disagrees, so ingest cannot get it wrong and no connector
-- has to be told about it; the key to orders is what keeps it true if the trigger
-- is ever dropped, and is what settlement_lines actually points at.
--
-- What this migration does not do, said as plainly as what it does. It does not
-- constrain status, mode, line_type, direction, channel or any other vocabulary a
-- marketplace supplies: part 2's principle governs all of those and is untouched.
-- It does not make a marketplace identifier immutable; renaming one in the
-- catalogue still carries the connections with it, which is what part 3 wanted. It
-- says nothing about whether the right order line was matched, only that the one
-- that was matched is on the same marketplace: deterministic matching is SEEN-018's
-- and this removes a class of match it would otherwise have to defend against. And
-- the unique keys below make a second read of one page write one row; they do not
-- make ingest idempotent by themselves, because a statement that writes rather than
-- upserts still fails rather than corrects, which is SEEN-014's to write.
--
-- Forward only, like the parts before it.

-- The marketplace column order_lines did not have ------------------------------
--
-- Added nullable, filled, then made not null, which is the order that works on a
-- database with rows in it as well as on the empty one `pnpm db:reset` leaves. Not
-- null is load bearing rather than tidy: a foreign key is MATCH SIMPLE by default,
-- so a null in any column of the key satisfies it without a check, and a nullable
-- marketplace here would be a key that guards every row but the ones written
-- without it.
alter table public.order_lines add column marketplace text;

update public.order_lines l
   set marketplace = o.marketplace
  from public.orders o
 where o.id = l.order_id and o.tenant_id = l.tenant_id;

comment on column public.order_lines.marketplace is
  'Not buyer PII. One of the six identifiers the marketplaces catalogue defines. Derived from '
  'the order this line belongs to rather than read from the marketplace, and kept equal to it '
  'by seen.order_line_marketplace() and by the key to orders: it exists so that a settlement '
  'line matched to this line can be refused when the two are on different marketplaces.';

-- Filled from the order rather than supplied, and a supplied value that disagrees
-- is refused rather than corrected.
--
-- Why fill at all instead of requiring the column of every writer. The value is not
-- an independent fact: an order line is a line of exactly one order and the order
-- names the marketplace, so a writer that supplies it is restating something the
-- row already knows, and every place that restates a fact is a place the two copies
-- drift. Filling it means no connector, no fixture and no later ticket has to be
-- told about a column whose value was never theirs to choose.
--
-- Why refuse a disagreeing value instead of overwriting it silently. An overwrite
-- would make a writer that believes it is inserting an Amazon line get a Bol one
-- with no error, which is the same class of quiet wrongness this whole file is
-- about. A raise names the disagreement to whoever wrote it.
--
-- Not security definer, which is a decision and not an omission. It runs as the
-- caller and so reads public.orders under whatever the caller may read, and the
-- two roles that can write an order line at all are the two that bypass row-level
-- security: `postgres`, which owns the schema, and `service_role`, which the API
-- and the workers run as and which part 4 leaves as the only Data API role holding
-- insert on this table. A browser-bound role holds nothing here, so there is no
-- caller for whom the lookup could come back empty and no owner rights to lend one.
-- If a later ticket grants `authenticated` a write on order_lines, this function
-- has to be revisited in the same change, because the read it makes would then be
-- filtered by the tenancy policy and every insert would be refused as an orphan.
create or replace function seen.order_line_marketplace()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  owner text;
begin
  select o.marketplace into owner
    from public.orders o
   where o.tenant_id = new.tenant_id and o.id = new.order_id;

  if owner is null then
    raise exception
      'an order line hangs from no order of its own tenant: order_id % is not an order of '
      'tenant %. The marketplace of a line is the marketplace of its order, so there is nothing '
      'to derive it from.', new.order_id, new.tenant_id
      using errcode = 'foreign_key_violation';
  end if;

  if new.marketplace is not null and new.marketplace is distinct from owner then
    raise exception
      'an order line cannot name a marketplace its own order does not: the line says % and '
      'order % says %. The column is derived from the order and is not a second place to record '
      'which marketplace a line was read from.', new.marketplace, new.order_id, owner
      using errcode = 'foreign_key_violation';
  end if;

  new.marketplace := owner;
  return new;
end;
$$;

comment on function seen.order_line_marketplace() is
  'Fills public.order_lines.marketplace from the order the line belongs to, and refuses a '
  'supplied value that disagrees with it.';

create trigger order_line_marketplace before insert or update on public.order_lines
  for each row execute function seen.order_line_marketplace();

revoke all on function seen.order_line_marketplace() from public;

alter table public.order_lines alter column marketplace set not null;

-- The referenced side ----------------------------------------------------------
--
-- A foreign key can only point at a unique constraint, so a parent that has to
-- lend its marketplace to a child needs (tenant_id, id, marketplace) declared
-- unique, and order_lines needs (tenant_id, order_id, id) so that a return's order
-- can travel in the key the way its tenant already does. Both are implied by the
-- primary key on id alone and the database will not infer either. It is five more
-- indexes duplicating what the primary key guarantees, which is the same price
-- part 5 paid sixteen times for the tenant, and it is paid here rather than argued
-- about per table later.
do $$
declare
  parent text;
begin
  foreach parent in array array['connections', 'order_lines', 'orders', 'settlements']
  loop
    execute format(
      'alter table public.%I add constraint %I unique (tenant_id, id, marketplace)',
      parent, parent || '_tenant_id_id_marketplace_key');
  end loop;
end;
$$;

alter table public.order_lines
  add constraint order_lines_tenant_id_order_id_id_key unique (tenant_id, order_id, id);

-- The chain, one link at a time ------------------------------------------------
--
-- Each key is dropped and rewritten under the name part 5 gave it, so a violation
-- still names the column a reader would look for, and each keeps the delete rule
-- part 5 decided: cascade where the child cannot outlive the parent, set null
-- naming the column to null where it can. Nothing here restricts, for part 5's
-- reason: a restricting key refuses the parent's delete outright, and a settlement
-- line or a connection has to stay removable and re-ingestible while something
-- points at it, which ingest does on every correction a marketplace sends.
--
-- Written out rather than looped, unlike part 5's twenty-eight, because these nine
-- differ from each other in the third column of the key and a loop over them would
-- be a loop with a case in it. A list somebody has to read and agree with is the
-- point.

-- An order is a row of the connection it was read through, and a settlement is a
-- statement from it, so neither may name a marketplace that account does not sell
-- on.
alter table public.orders drop constraint orders_connection_id_fkey;
alter table public.orders
  add constraint orders_connection_id_fkey
  foreign key (tenant_id, connection_id, marketplace)
  references public.connections (tenant_id, id, marketplace)
  on delete cascade;

alter table public.settlements drop constraint settlements_connection_id_fkey;
alter table public.settlements
  add constraint settlements_connection_id_fkey
  foreign key (tenant_id, connection_id, marketplace)
  references public.connections (tenant_id, id, marketplace)
  on delete cascade;

-- A line, a shipment and a return are all rows of one order and inherit its
-- marketplace. On order_lines the column is derived, so this key is not what fills
-- it; it is what keeps the derivation true when the trigger is not there, and it is
-- what settlement_lines below is able to point at.
alter table public.order_lines drop constraint order_lines_order_id_fkey;
alter table public.order_lines
  add constraint order_lines_order_id_fkey
  foreign key (tenant_id, order_id, marketplace)
  references public.orders (tenant_id, id, marketplace)
  on delete cascade;

alter table public.shipments drop constraint shipments_order_id_fkey;
alter table public.shipments
  add constraint shipments_order_id_fkey
  foreign key (tenant_id, order_id, marketplace)
  references public.orders (tenant_id, id, marketplace)
  on delete cascade;

alter table public.returns drop constraint returns_order_id_fkey;
alter table public.returns
  add constraint returns_order_id_fkey
  foreign key (tenant_id, order_id, marketplace)
  references public.orders (tenant_id, id, marketplace)
  on delete cascade;

-- A settlement line is a line of one settlement and takes its marketplace from it.
alter table public.settlement_lines drop constraint settlement_lines_settlement_id_fkey;
alter table public.settlement_lines
  add constraint settlement_lines_settlement_id_fkey
  foreign key (tenant_id, settlement_id, marketplace)
  references public.settlements (tenant_id, id, marketplace)
  on delete cascade;

-- The two keys where a row has a second parent it had been free to disagree with.
--
-- A return's line must be a line of the return's own order, so order_id travels in
-- the key. A settlement line's matched line must be on the settlement line's own
-- marketplace, so marketplace does. Both stay nullable and both stay `set null`
-- naming the column: a return may be a return of a whole order and a settlement
-- line is unmatched until SEEN-018 matches it, and MATCH SIMPLE means a null
-- reference satisfies the key without a check, which is exactly the reading wanted
-- here and exactly the reading a nullable marketplace would have wrecked above.
alter table public.returns drop constraint returns_order_line_id_fkey;
alter table public.returns
  add constraint returns_order_line_id_fkey
  foreign key (tenant_id, order_id, order_line_id)
  references public.order_lines (tenant_id, order_id, id)
  on delete set null (order_line_id);

alter table public.settlement_lines drop constraint settlement_lines_order_line_id_fkey;
alter table public.settlement_lines
  add constraint settlement_lines_order_line_id_fkey
  foreign key (tenant_id, order_line_id, marketplace)
  references public.order_lines (tenant_id, id, marketplace)
  on delete set null (order_line_id);

-- A claim hangs from no connection and no order, so the catalogue is the only
-- parent that can say what its marketplace is. Written the way part 3 wrote the
-- connections key and for the same reasons: composite on (tenant_id, marketplace)
-- because the catalogue is held per tenant, so a claim cannot point at another
-- tenant's catalogue row; no `on delete` clause, so the check falls at the end of
-- the statement and the cascade from tenants can remove a tenant's catalogue and
-- its claims in one statement without the two racing, where RESTRICT would refuse
-- mid-statement and make erasure on request impossible; `on update cascade` so a
-- rename in the catalogue carries the claims with it rather than orphaning them.
alter table public.claims
  add constraint claims_marketplace_fkey
  foreign key (tenant_id, marketplace)
  references public.marketplaces (tenant_id, marketplace)
  on update cascade;

-- One row per page a marketplace was read ---------------------------------------
--
-- Part 1 states the reason beside the five indexes it creates: "one row per
-- (tenant, marketplace, external id), so reading the same page of a marketplace's
-- API twice writes the row once". Three externally sourced tables were left
-- without one.
--
-- None of the three takes the (tenant_id, marketplace, external_id) shape, and
-- that is a choice rather than an inconsistency. A marketplace's line id is unique
-- within the order it was read from, not across a marketplace, so keying it wider
-- would refuse an ordinary second order that happens to number its lines the same
-- way; listings is already keyed the same narrower way, on (tenant_id,
-- connection_id, external_offer_id), which is part 1's own precedent for an
-- external id scoped by its parent. The key is as narrow as the identifier it
-- keys, which is what makes it safe to enforce.
--
-- Where the external id is null the row is not keyed at all, on all three. That is
-- not an oversight either: a row the marketplace gave no id for cannot be found
-- again by that id, so there is nothing for a second read to collide with, and a
-- key that folded those rows together would refuse a legitimate second line.
create unique index order_lines_tenant_id_order_id_external_line_id_key
  on public.order_lines (tenant_id, order_id, external_line_id);

-- The one that needs `nulls not distinct`, and the one place in this file where
-- the default reading of a null would have left the guarantee where it is least
-- affordable. A thread read from a marketplace messaging API hangs from a
-- connection; a thread that arrived through the forwarded mailbox (SEEN-062) has
-- no connection_id at all. Under the default, two nulls are different values, so a
-- key on (tenant_id, connection_id, external_thread_id) would guard every thread
-- but the mail ones, which are precisely the ones where the same message arriving
-- again is ordinary. `nulls not distinct` makes the two mail threads collide as a
-- reader expects. The partial predicate is what keeps that from folding every
-- thread with no external id into one row.
create unique index message_threads_tenant_id_connection_id_external_thread_id_key
  on public.message_threads (tenant_id, connection_id, external_thread_id)
  nulls not distinct
  where external_thread_id is not null;

create unique index messages_tenant_id_thread_id_external_message_id_key
  on public.messages (tenant_id, thread_id, external_message_id);

-- The catalogue's tenant id does not move --------------------------------------
--
-- connections_marketplace_fkey is `(tenant_id, marketplace) references
-- public.marketplaces (tenant_id, marketplace) on update cascade`, and part 3
-- states the intent beside it: renaming an identifier in the catalogue should carry
-- the connections with it rather than orphan them. That reasoning covers one column
-- of the key. Postgres has no per-column referential action, so the cascade fires
-- on a change to either, and a change to marketplaces.tenant_id rewrites
-- connections.tenant_id.
--
-- Measured before this file existed, as the role apps/api and apps/worker run as:
--
--   before  aaaaaaaa-...-0001 | bol | projects/seen/secrets/tenantA-bol-oauth
--   after   bbbbbbbb-...-0002 | bol | projects/seen/secrets/tenantA-bol-oauth
--
-- one UPDATE, no error, and one tenant holding another tenant's Secret Manager
-- pointer, its scopes and its external seller id. A referential action is not a
-- statement: it passes through no policy, and connections has no trigger that would
-- have objected. Part 8 settled that a tenant id is an identity and not a value and
-- put a trigger on public.tenants to say so; the catalogue is the one other place
-- in this schema where an update of a tenant_id rewrites another table's rows, and
-- it was the place with nothing in the way.
--
-- What was chosen, and what was chosen over it. The cascade is kept, because the
-- reason part 3 gave for it is still true of the column it was written about, and
-- dropping it would make a rename refuse itself while connections stand rather than
-- carry them. What is taken away is the column it was never meant to reach: this
-- tenant_id is not updatable at all, whatever it would be changed to, so the only
-- change the cascade can now carry is the rename it was written for. A narrower
-- rule that refused only a move to a different tenant was rejected for part 8's
-- reason: there is no legitimate operation that moves one, a new tenant gets a new
-- uuid, and a rule with a permitted case in it is a rule with a way through it.
--
-- What this is not. It is not client-reachable and was not before: no role a
-- browser is bound to may write public.marketplaces at all, so this closes a
-- defence-in-depth gap rather than an open door. And it is one table's tenant_id
-- and not every table's: elsewhere in this schema a tenant_id is held in place by
-- part 5's keys, which name no update action and so refuse the move while a child
-- stands, and a childless row's tenant_id can still be moved by a role that can
-- write it. That is a wider question than F65 and it is not settled here.
create or replace function seen.refuse_marketplace_tenant_change()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception
    'the tenant of a catalogue row is not updatable: % cannot become %. connections, claims and '
    'every table keyed to them through it hang off this pair by a foreign key that cascades on '
    'update, so moving it would carry one tenant''s connection, its credential reference and its '
    'scopes into another tenant, through a referential action that passes no policy and writes '
    'no audit event. A tenant id is an identity and not a value.', old.tenant_id, new.tenant_id
    using errcode = 'restrict_violation';
end;
$$;

comment on function seen.refuse_marketplace_tenant_change() is
  'Refuses any update of public.marketplaces.tenant_id, so the one foreign key in this schema '
  'that cascades on update can carry nothing but the marketplace identifier it was written for.';

create trigger refuse_marketplace_tenant_change before update on public.marketplaces
  for each row when (new.tenant_id is distinct from old.tenant_id)
  execute function seen.refuse_marketplace_tenant_change();

revoke all on function seen.refuse_marketplace_tenant_change() from public;

-- What this migration claims, measured rather than asserted ---------------------
--
-- The shape parts 4, 5, 6 and 8 end with: the migration fails as it applies rather
-- than leaving a guarantee that reads true and is not. The claims above are a list
-- somebody wrote, and what makes a list right is that nothing is left over, so each
-- check below asks the catalogue the question rather than trusting the list.
do $$
declare
  offenders text;
begin
  -- The chain, walked from the catalogue outwards rather than named.
  --
  -- This is the one check that has to be recursive, because the guarantee is
  -- transitive: orders is constrained by connections, which is constrained by the
  -- catalogue, and a check that only asked "is this column in some foreign key"
  -- would pass a schema in which four tables held each other up and none of them
  -- reached a real identifier. The walk starts at the keys that point straight at
  -- public.marketplaces and follows a key only where it carries marketplace from a
  -- column already reached to the column being asked about.
  --
  -- public.marketplaces itself is excluded, because it is where the walk starts:
  -- its own marketplace column is the definition and has nothing above it to agree
  -- with.
  with recursive constrained as (
    select con.conrelid as relid
      from pg_catalog.pg_constraint con
      join pg_catalog.pg_attribute a
        on a.attrelid = con.conrelid and a.attname = 'marketplace'
       and a.attnum > 0 and not a.attisdropped
     where con.contype = 'f'
       and con.confrelid = 'public.marketplaces'::regclass
       and a.attnum = any(con.conkey)
    union
    select con.conrelid
      from pg_catalog.pg_constraint con
      join constrained reached on reached.relid = con.confrelid
      join pg_catalog.pg_attribute ca
        on ca.attrelid = con.conrelid and ca.attname = 'marketplace'
       and ca.attnum > 0 and not ca.attisdropped
      join pg_catalog.pg_attribute pa
        on pa.attrelid = con.confrelid and pa.attname = 'marketplace'
       and pa.attnum > 0 and not pa.attisdropped
     where con.contype = 'f'
       and exists (
         select 1 from unnest(con.conkey, con.confkey) as pair(child, parent)
          where pair.child = ca.attnum and pair.parent = pa.attnum)
  )
  select string_agg(format('%s.marketplace', c.relname), ', ' order by c.relname)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    join pg_catalog.pg_attribute a
      on a.attrelid = c.oid and a.attname = 'marketplace'
     and a.attnum > 0 and not a.attisdropped
   where n.nspname = 'public'
     and c.relkind in ('r', 'p')
     and c.oid <> 'public.marketplaces'::regclass
     and c.oid not in (select relid from constrained);

  if offenders is not null then
    raise exception 'a marketplace column reaches no catalogue row by any chain of keys, so its '
      'own comment saying it is one of the six identifiers the catalogue defines is a sentence '
      'and not a guarantee, and the unique index on (tenant_id, marketplace, external_id) is an '
      'idempotency key only while a connector spells the value the same way twice: %. Either key '
      'it to the parent that already names a marketplace, or key it straight to '
      'public.marketplaces the way claims is', offenders;
  end if;

  -- And the column is not nullable anywhere, which the walk above cannot see. A
  -- foreign key is MATCH SIMPLE by default, so one null in the key satisfies it
  -- with no check performed, and a nullable marketplace would be a link in the
  -- chain that every row written without it walks straight through.
  select string_agg(format('%s.marketplace', c.relname), ', ' order by c.relname)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    join pg_catalog.pg_attribute a
      on a.attrelid = c.oid and a.attname = 'marketplace'
     and a.attnum > 0 and not a.attisdropped
   where n.nspname = 'public' and c.relkind in ('r', 'p') and not a.attnotnull;

  if offenders is not null then
    raise exception 'a marketplace column is nullable, and a key carrying it is MATCH SIMPLE, so '
      'a row written without the value satisfies the key with no check at all: %', offenders;
  end if;

  -- The second parent each of the two matched rows has to agree with. Asked by the
  -- columns of the key rather than by its name, because a key renamed still keeps
  -- the guarantee and a key rewritten under the same name may not.
  select string_agg(
           format('%s.%s does not carry %s', named.child, named.keyname, named.travels),
           ', ' order by named.child)
    into offenders
    from (values
      ('returns',          'returns_order_line_id_fkey',          'order_id'),
      ('settlement_lines', 'settlement_lines_order_line_id_fkey', 'marketplace')
    ) as named(child, keyname, travels)
   where not exists (
     select 1
       from pg_catalog.pg_constraint con
       join pg_catalog.pg_attribute a
         on a.attrelid = con.conrelid and a.attname = named.travels
        and a.attnum > 0 and not a.attisdropped
      where con.contype = 'f'
        and con.conrelid = format('public.%I', named.child)::regclass
        and con.conname = named.keyname
        and a.attnum = any(con.conkey));

  if offenders is not null then
    raise exception 'a row with two parents that have to agree can still disagree with one of '
      'them: %. A return''s order_line_id must be a line of the return''s own order, and a '
      'settlement line''s matched order line must be on the settlement line''s own marketplace, '
      'or the database stores a match SEEN-018 and the detectors read as truth', offenders;
  end if;

  -- One row per page read, on the three externally sourced tables part 1 left
  -- without a key. Asked as "a unique index whose columns include this one",
  -- because the shape differs per table and what each buys is the same thing: a
  -- second read of one page cannot write a second row.
  select string_agg(format('%s.%s', named.child, named.identifier), ', ' order by named.child)
    into offenders
    from (values
      ('message_threads', 'external_thread_id'),
      ('messages',        'external_message_id'),
      ('order_lines',     'external_line_id')
    ) as named(child, identifier)
   where not exists (
     select 1
       from pg_catalog.pg_index i
       join pg_catalog.pg_attribute a
         on a.attrelid = i.indrelid and a.attname = named.identifier
        and a.attnum > 0 and not a.attisdropped
      where i.indrelid = format('public.%I', named.child)::regclass
        and i.indisunique
        and a.attnum = any(i.indkey::smallint[]));

  if offenders is not null then
    raise exception 'an externally sourced table carries a marketplace''s own identifier with no '
      'unique index on it, so a second read of the same page writes the row again and no upsert '
      'can be written at all, because `on conflict` needs a unique index to arbitrate: %',
      offenders;
  end if;

  -- And the one tenant_id in this schema that a referential action could move.
  if not exists (
    select 1 from pg_catalog.pg_trigger
     where tgrelid = 'public.marketplaces'::regclass
       and not tgisinternal
       and tgname = 'refuse_marketplace_tenant_change'
  ) then
    raise exception 'nothing refuses an update of public.marketplaces.tenant_id, and the key '
      'from connections to it cascades on update, so one statement moves another tenant''s '
      'connection and the credential reference on it into a tenant that never asked for it';
  end if;

  -- Both halves, because a fix that closed the identifier and broke the catalogue
  -- would be worse than the defect. The seed has to still be able to write a
  -- tenant's six rows, and it writes them through an upsert that updates name and
  -- capabilities, which the trigger above must not be in the way of.
  if not exists (select 1 from seen.marketplace_catalogue) then
    raise exception 'the catalogue this file keys six columns to is empty, so every key added '
      'here refuses every row and criterion 5 has nothing to compare against the routing table';
  end if;
end;
$$;
