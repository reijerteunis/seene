-- Trade record v1, part 4: the Data API roles read, and nothing more.
--
-- Parts 1 to 3 ended with `grant select, insert, update, delete on all tables in
-- schema public to authenticated`, and Supabase's default privileges for schema
-- public had already granted the same four to `anon` and `authenticated` when each
-- table was created. Two things followed from that, both of them reproduced
-- against this stack before this migration was written.
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
-- This migration does not end in `grant ... on all tables in schema public`, and
-- no later one may either. That is what re-granted update and delete on
-- audit_events three times over in parts 1 to 3, each time silently undoing the
-- revoke the part before it had just written. Grant per table, or re-revoke
-- immediately afterwards and say why.

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
    -- Everything, from both sources at once: the blanket grants in parts 1 to 3
    -- and the default privileges Supabase holds on schema public, which granted
    -- insert, update, delete and truncate to anon and authenticated at the moment
    -- each table was created. Narrowing the grants alone would have left the
    -- default access control list standing.
    execute format('revoke all privileges on public.%I from anon, authenticated', target);
    execute format('grant select on public.%I to authenticated', target);

    if target = 'audit_events' then
      -- The gate writes an event and no role rewrites one. Named per table rather
      -- than granted broadly and revoked after, because the revoke is the part
      -- that keeps getting undone.
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
