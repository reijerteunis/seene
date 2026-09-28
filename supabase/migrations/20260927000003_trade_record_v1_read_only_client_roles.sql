-- Trade record v1, part 4 of 5: the Data API roles read, and nothing more.
--
-- The set is these four files, the migrations whose names carry `trade_record_v1`,
-- and not everything in supabase/migrations: the evidence bucket migration of
-- 24 September creates a bucket for the environment and takes no part in the
-- privilege boundary these four hand to each other. Every part's first line states
-- the size of the set and schema.test.ts checks that number against the files on
-- disk, so a fifth part is added by numbering it and correcting the four in front
-- of it. The count is the route to this file: part 3 ends by saying it grants no
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
  for target in
    select c.relname
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind = 'r'
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
     and c.relkind = 'r'
     and a.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
     -- The three roles a request can be bound to. The owner of the table holds
     -- update, delete and truncate on audit_events and has to: the trigger is what
     -- refuses those to the owner as well, and a table nobody owns is not a table.
     and a.grantee in ('anon'::regrole, 'authenticated'::regrole, 'service_role'::regrole)
     and (
       a.grantee = 'anon'::regrole
       or (a.grantee = 'authenticated'::regrole and a.privilege_type <> 'SELECT')
       or (c.relname = 'audit_events' and a.privilege_type in ('UPDATE', 'DELETE', 'TRUNCATE'))
     );

  if offenders is not null then
    raise exception 'the Data API roles still hold privileges this migration meant to remove: %',
      offenders;
  end if;

  if not has_table_privilege('service_role', 'public.audit_events', 'insert')
     or not has_table_privilege('service_role', 'public.tenants', 'delete') then
    raise exception 'the revoke was over-broad: service_role can no longer write an audit event '
      'or erase a tenant, and both are server jobs this schema owes SEEN-032 and SEEN-083';
  end if;
end;
$$;
