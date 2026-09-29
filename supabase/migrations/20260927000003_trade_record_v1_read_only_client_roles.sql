-- Trade record v1, part 4 of 8: the Data API roles read, and nothing more.
--
-- The set is these eight files, the migrations whose names carry
-- `trade_record_v1`, and not everything in supabase/migrations: the evidence
-- bucket migration of 24 September creates a bucket for the environment and takes
-- no part in the privilege boundary these eight hand to each other. Every part's
-- first line states the size of the set and schema.test.ts checks that number
-- against the files on disk, so a ninth part is added by numbering it and
-- correcting the eight in front of it. The count is the route to this file: part 3 ends by saying it grants no
-- table privilege because part 4 decides them per table and by name, and a header
-- that stopped the set at three sent the next author away before they read that
-- boundary or the self-check below, with Supabase's default ACL left standing on
-- the table they had just created.
--
-- Parts 1 to 3 each used to end with `grant select, insert, update, delete on all
-- tables in schema public to authenticated`, and Supabase's default privileges for
-- schema public had already granted the same four to `anon` and `authenticated`
-- when each table was created. Two things followed from that, both of them
-- reproduced against this stack before this migration was written.
--
-- Those three tails are gone: the second review of SEEN-008 found that they were
-- the template the next migration author would read, and one copy of part 3's tail
-- hands `authenticated` insert, update and delete on settlement_lines, claims and
-- invoices back again with nothing re-running to notice. The default privileges are
-- the half that remains, and are what the revoke below is for. Nothing is deployed,
-- so the applied files could be corrected rather than patched over: the regression
-- starts from `pnpm db:reset` on an empty database and measures the whole schema
-- again.
--
-- A signed-in user of a tenant could delete that tenant's own row in
-- public.tenants. The delete privilege was there, and the tenancy policy's USING
-- clause governs DELETE, so the row matched and went; the cascade then took the
-- whole trade record and every audit event for that tenant with it, through the
-- one branch the append-only trigger permits. The audit trail exists to hold the
-- agent, and the tenant, accountable for what was filed on the tenant's behalf,
-- and the party it holds accountable could empty it in one statement.
--
-- And the same privileges let the party that gets invoiced write the record it is
-- invoiced from: a settlement nobody ingested, a compensation line of
-- EUR 9,999.00 nobody was paid, a claim that says that line credited it, an
-- invoice updated to zero and void, a statement deleted, a headroom figure the
-- Price module is supposed to be the only source of.
--
-- So: `anon` and `authenticated` get select and nothing else, on all 29 tables,
-- and `anon` loses select as well. The web application reads Postgres through
-- row-level security as `authenticated`, which is all a server component does;
-- every write in this product goes through the API or a worker as `service_role`.
-- `anon` carries no tenant claim, so the policy already yields it no rows, and
-- taking its select too means a table that later loses its policy is not readable
-- by a caller who never signed in on top of that.
--
-- Two consequences this migration owns rather than leaves to be discovered.
--
-- Erasing a tenant is now a service-role action. That is the one delete the
-- append-only trigger on public.audit_events lets through, and it is still
-- reachable, because `service_role` still holds delete on public.tenants: what
-- changed is that only the server can open it. Deletion on request is SEEN-083's,
-- and it is a server job in any case.
--
-- The tenancy policies stay as `for all` with both clauses reading
-- seen.current_tenant(), rather than being narrowed to `for select`. A policy is
-- what decides which rows a role reaches and a privilege is what decides whether
-- it reaches the table at all: the two answers should agree, and if a later
-- migration re-grants a write privilege by accident, a WITH CHECK clause that
-- still names the tenant is the difference between one tenant's mistake and every
-- tenant's.
--
-- This migration does not end in `grant ... on all tables in schema public`, and no
-- later one may either. That is what re-granted update and delete on audit_events
-- three times over in parts 1 to 3, each time silently undoing the revoke the part
-- before it had just written. Grant per table, by name.
--
-- That sentence was already here as a comment and a comment was not enough, so it
-- is a test now: `packages/core/db/schema.test.ts` reads every file under
-- supabase/migrations and fails on a grant that names a whole schema, and on an
-- `alter default privileges`, which is the same hazard one level up. The next author
-- meets a failing test rather than this paragraph.

do $$
declare
  target text;
begin
  -- The relation kinds this schema's tenancy is written on: an ordinary table is
  -- `'r'` and a partitioned table is `'p'`. A partitioned table is read through
  -- the Data API exactly as a table is and can carry an enabled policy, so it is
  -- granted what a table is granted rather than stripped like the kinds below;
  -- the fifth Codex review of SEEN-008 (F29) is that it was on the wrong side of
  -- that line here and invisible to the tenancy guards altogether. Reading through
  -- the parent is checked against the parent's privileges alone, measured on the
  -- local stack, and reading a partition directly is checked against the
  -- partition's own, so both are granted here: a partition answers to `'r'`.
  for target in
    select c.relname
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind in ('p', 'r')
     order by c.relname
  loop
    -- Everything, whatever granted it: the default privileges Supabase holds on
    -- schema public granted insert, update, delete and truncate to anon and
    -- authenticated at the moment each table was created, and parts 1 to 3 granted
    -- the same four again until those tails were removed. Narrowing a grant is not
    -- enough on its own, because the default access control list would still be
    -- standing behind it.
    execute format('revoke all privileges on public.%I from anon, authenticated', target);
    execute format('grant select on public.%I to authenticated', target);

    if target = 'audit_events' then
      -- The gate writes an event and no role rewrites one. Named per table rather
      -- than granted broadly and revoked after, because the revoke is the part that
      -- keeps getting undone. The revoke is written here as well as in part 2, so
      -- that this migration is true on its own when read: part 2 is what strips the
      -- privileges the table was created with, and this is what a later reader can
      -- check without having to find part 2 to know whether it still holds.
      execute format(
        'revoke update, delete, truncate on public.%I from service_role', target);
      execute format('grant select, insert on public.%I to service_role', target);
    else
      execute format(
        'grant select, insert, update, delete, truncate on public.%I to service_role', target);
    end if;
  end loop;

  -- And the relations in this schema that no policy of this database governs,
  -- which the loop above deliberately does not reach. A view answers to `'v'`, a
  -- materialised view to `'m'` and a foreign table to `'f'`, all three hold rows,
  -- all three are served through the Data API exactly as a table is, and none of
  -- them is subject to row-level security the way the twenty-nine above are: a
  -- view only if it was created `with (security_invoker = true)`, a materialised
  -- view never, and a foreign table's rows are on another server. So they are
  -- stripped rather than granted, and a later migration that wants to publish one
  -- writes its own grant and says why.
  --
  -- There is no such relation in this schema today, so this loop turns over
  -- nothing. It is here because the self-check below asks about all five kinds,
  -- and a check that asks more than the statements above it did would be a check
  -- somebody has to satisfy by hand. Part 6 is what stops the next one being born
  -- holding the default access control list in the first place.
  for target in
    select c.relname
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind in ('f', 'm', 'v')
     order by c.relname
  loop
    execute format('revoke all privileges on public.%I from anon, authenticated', target);
  end loop;
end;
$$;

-- And the migration checks its own outcome, because the privileges of a table
-- come from more places than the statements above and a silent partial result
-- here is a boundary nobody would notice was open.
do $$
declare
  offenders text;
begin
  select string_agg(
           format('%s: %s holds %s', c.relname, a.grantee::regrole::text, a.privilege_type),
           ', ' order by c.relname)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    cross join lateral aclexplode(c.relacl) a
   where n.nspname = 'public'
     -- Every relation kind that holds rows, not the ordinary table alone. The
     -- third Codex review of SEEN-008 (F19) found that this self-check, like every
     -- guard in the set, read `relkind = 'r'` and so measured nothing whatever
     -- about a view: `anon` was refused public.shipments and read both tenants'
     -- buyer name and buyer address through a view over it, and this raised
     -- nothing.
     and c.relkind in ('f', 'm', 'p', 'r', 'v')
     and a.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
     -- The three roles a request can be bound to. The owner of the table holds
     -- update, delete and truncate on audit_events and has to: the trigger is what
     -- refuses those to the owner as well, and a table nobody owns is not a table.
     and a.grantee in ('anon'::regrole, 'authenticated'::regrole, 'service_role'::regrole)
     and (
       a.grantee = 'anon'::regrole
       -- `authenticated` reads a table and holds nothing else anywhere. On a
       -- relation that is not a table it does not even read: a select there is a
       -- read that row-level security may never have been applied to. A
       -- partitioned table is a table for this purpose and an ordinary one is, and
       -- the two lists have to agree: the loop above grants select on both, so a
       -- check that exempted only `'r'` would raise on the grant it had just
       -- written (F29).
       or (a.grantee = 'authenticated'::regrole
           and (a.privilege_type <> 'SELECT' or c.relkind not in ('p', 'r')))
       or (c.relname = 'audit_events' and a.privilege_type in ('UPDATE', 'DELETE', 'TRUNCATE'))
     );

  if offenders is not null then
    raise exception 'the Data API roles still hold privileges this migration meant to remove, on '
      'a table or on a relation that is not one: %', offenders;
  end if;

  if not has_table_privilege('service_role', 'public.audit_events', 'insert')
     or not has_table_privilege('service_role', 'public.tenants', 'delete') then
    raise exception 'the revoke was over-broad: service_role can no longer write an audit event '
      'or erase a tenant, and both are server jobs this schema owes SEEN-032 and SEEN-083';
  end if;
end;
$$;
