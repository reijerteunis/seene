-- Trade record v1, part 5 of 8: the tenant travels along every foreign key.
-- SEEN-008, CODEX-01.
--
-- What parts 1 to 4 got right and what they missed. Every table carries
-- tenant_id, every table has row-level security, every policy reads the one
-- expression, and no client-bound role may write. All of that is per row and per
-- table, and none of it is a statement about the relationship between two rows.
-- A key written `references public.connections (id)` accepts any connection in
-- the database beside any tenant_id, and the tenant_id key beside it accepts any
-- tenant beside any connection. Each key is satisfied; the pair of them is an
-- edge from one tenant's row to another tenant's row, and `on delete cascade`
-- makes it a destructive edge.
--
-- Measured against the local stack before this file existed, as service_role:
-- tenants A and B, a Bol connection belonging to A, and an order carrying B's
-- tenant_id and A's connection_id. The insert was accepted. Deleting tenant A
-- then deleted that order, and tenant B was still standing to find it gone. A
-- mismatched parent id in an ingest run is all it takes, and deletion on request,
-- which the PRD promises and SEEN-083 performs, becomes the thing that destroys
-- another brand's trade record.
--
-- The fix is that the tenant travels along the key. Every foreign key between two
-- tables that carry tenant_id is rewritten as `(tenant_id, parent_id) references
-- parent (tenant_id, id)`, so the database refuses a child whose parent belongs
-- to somebody else and no code on the ingest side has to remember. The referenced
-- side needs a unique constraint on (tenant_id, id) for the key to point at, which
-- is sixteen indexes that duplicate what the primary key already guarantees: that
-- is the price, and it is paid once here rather than argued about per table later.
--
-- Three shapes are deliberately left alone. The twenty-eight keys to
-- public.tenants already carry the tenant, because the column they reference is
-- tenant_id itself. The key from connections to marketplaces was already written
-- as (tenant_id, marketplace) in part 3. And nothing here becomes `on delete
-- restrict`: a restrict refuses the parent's delete outright, the cascade from an
-- erased tenant reaches these children, and the whole erasure would roll back
-- mid-statement. The eight keys that set null keep doing so, naming the column to
-- null so that tenant_id, which is not null, is not one of them; Postgres 15 added
-- that form and the local stack is 17.
--
-- This migration grants nothing and revokes nothing. Part 4 decides the privileges
-- of every table per table and by name, and it is still the only place that does
-- for a table. Part 6 is the one that decides what a relation which is not a table
-- may be born holding, because `relkind = 'r'` is where every guard in parts 1 to 5
-- stops and a view is not one.
--
-- Forward only, like the four parts before it.

-- The referenced side. A foreign key can only point at a unique constraint, so
-- each parent of a tenant-scoped key needs (tenant_id, id) declared unique. It is
-- implied by the primary key on id alone and the database will not infer it.
do $$
declare
  parent text;
begin
  foreach parent in array array[
    'agent_actions', 'agent_runs', 'approvals', 'claims', 'connections', 'invoices',
    'listings', 'message_threads', 'order_lines', 'orders', 'price_changes', 'products',
    'returns', 'settlement_lines', 'settlements', 'shipments'
  ]
  loop
    execute format(
      'alter table public.%I add constraint %I unique (tenant_id, id)',
      parent, parent || '_tenant_id_id_key');
  end loop;
end;
$$;

-- And the keys themselves, each dropped and rewritten under its own name so that
-- a constraint violation still names the column a reader would look for.
--
-- The list is the whole of it: twenty foreign keys that cascade and eight that set
-- null, being every key in the schema that joins two tenant-owned tables and is
-- not already tenant-scoped. Written out rather than derived from the catalogue,
-- because a loop over pg_constraint would silently rewrite whatever a later
-- migration had added and this is a list somebody has to read and agree with.
do $$
declare
  key record;
  constraint_name text;
  action text;
begin
  for key in
    select *
      from (values
        -- child table, its column, the parent, what a delete of the parent does
        ('agent_actions',        'agent_run_id',                   'agent_runs',       'cascade'),
        ('agent_actions',        'approval_id',                    'approvals',        'set null'),
        ('audit_events',         'agent_action_id',                'agent_actions',    'cascade'),
        ('claim_events',         'claim_id',                       'claims',           'cascade'),
        ('claims',               'credited_by_settlement_line_id', 'settlement_lines', 'set null'),
        ('competitor_snapshots', 'listing_id',                     'listings',         'cascade'),
        ('evidence',             'claim_id',                       'claims',           'cascade'),
        ('fee_expectations',     'order_line_id',                  'order_lines',      'cascade'),
        ('findings',             'claim_id',                       'claims',           'set null'),
        ('findings',             'return_id',                      'returns',          'cascade'),
        ('findings',             'settlement_line_id',             'settlement_lines', 'cascade'),
        ('findings',             'shipment_id',                    'shipments',        'cascade'),
        ('headroom_entries',     'price_change_id',                'price_changes',    'cascade'),
        ('listings',             'connection_id',                  'connections',      'cascade'),
        ('listings',             'product_id',                     'products',         'set null'),
        ('message_threads',      'connection_id',                  'connections',      'cascade'),
        ('messages',             'thread_id',                      'message_threads',  'cascade'),
        ('order_lines',          'order_id',                       'orders',           'cascade'),
        ('order_lines',          'product_id',                     'products',         'set null'),
        ('orders',               'connection_id',                  'connections',      'cascade'),
        ('price_changes',        'listing_id',                     'listings',         'cascade'),
        ('returns',              'order_id',                       'orders',           'cascade'),
        ('returns',              'order_line_id',                  'order_lines',      'set null'),
        ('settlement_lines',     'order_line_id',                  'order_lines',      'set null'),
        ('settlement_lines',     'settlement_id',                  'settlements',      'cascade'),
        ('settlements',          'connection_id',                  'connections',      'cascade'),
        ('shipments',            'order_id',                       'orders',           'cascade'),
        ('statements',           'invoice_id',                     'invoices',         'set null')
      ) as k(child, child_column, parent, on_delete)
  loop
    constraint_name := key.child || '_' || key.child_column || '_fkey';

    -- Set null has to name the column, or the database nulls every column of the
    -- key, tenant_id among them, and tenant_id is not null. What that costs is the
    -- ordinary delete of the parent row: measured with a bare set-null in this
    -- key's place, deleting the settlement line a claim was credited by, or the
    -- settlement or the connection it hangs from, is refused with 23502, so a line
    -- cannot be removed or re-ingested while a claim points at it. A tenant's own
    -- erasure is not the case that proves it, though this comment used to say it
    -- was: with a bare key in place the erasure is accepted, because the cascade
    -- removes the child before the set-null can reach it, and the order two sibling
    -- cascade actions run in is not something a reason may rest on.
    if key.on_delete = 'set null' then
      action := format('set null (%I)', key.child_column);
    else
      action := 'cascade';
    end if;

    execute format(
      'alter table public.%I drop constraint %I', key.child, constraint_name);
    execute format(
      'alter table public.%I add constraint %I foreign key (tenant_id, %I) '
      'references public.%I (tenant_id, id) on delete %s',
      key.child, constraint_name, key.child_column, key.parent, action);
  end loop;
end;
$$;

-- And the migration checks its own outcome. The loop above is a list a person
-- wrote, and the thing that makes it right is that nothing is left over: this asks
-- the catalogue the same question the review asked, rather than trusting the list.
do $$
declare
  offenders text;
begin
  select string_agg(
           format('%s.%s -> %s', src.relname, con.conname, tgt.relname),
           ', ' order by src.relname, con.conname)
    into offenders
    from pg_catalog.pg_constraint con
    join pg_catalog.pg_class src on src.oid = con.conrelid
    join pg_catalog.pg_class tgt on tgt.oid = con.confrelid
    join pg_catalog.pg_namespace n on n.oid = src.relnamespace
   where con.contype = 'f'
     and n.nspname = 'public'
     -- Both sides owned by a tenant. A key to a table with no tenant_id at all is
     -- a different question and this migration does not answer it.
     and exists (select 1 from pg_catalog.pg_attribute a
                  where a.attrelid = src.oid and a.attname = 'tenant_id'
                    and a.attnum > 0 and not a.attisdropped)
     and exists (select 1 from pg_catalog.pg_attribute a
                  where a.attrelid = tgt.oid and a.attname = 'tenant_id'
                    and a.attnum > 0 and not a.attisdropped)
     and not exists (
       select 1
         from unnest(con.conkey, con.confkey) as pair(child_attnum, parent_attnum)
         join pg_catalog.pg_attribute ca
           on ca.attrelid = src.oid and ca.attnum = pair.child_attnum
         join pg_catalog.pg_attribute pa
           on pa.attrelid = tgt.oid and pa.attnum = pair.parent_attnum
        where ca.attname = 'tenant_id' and pa.attname = 'tenant_id');

  if offenders is not null then
    raise exception 'foreign keys still reference their parent by id alone, so a child row may '
      'name a parent belonging to another tenant: %', offenders;
  end if;

  -- The other half: a key that refuses the parent's delete makes a tenant
  -- undeletable, and deletion on request is a promise this schema has to keep.
  select string_agg(format('%s.%s', src.relname, con.conname), ', ' order by con.conname)
    into offenders
    from pg_catalog.pg_constraint con
    join pg_catalog.pg_class src on src.oid = con.conrelid
    join pg_catalog.pg_namespace n on n.oid = src.relnamespace
   where con.contype = 'f' and n.nspname = 'public' and con.confdeltype = 'r';

  if offenders is not null then
    raise exception 'foreign keys refuse a delete of the parent outright, which is what a '
      'tenant''s erasure is: %', offenders;
  end if;
end;
$$;
