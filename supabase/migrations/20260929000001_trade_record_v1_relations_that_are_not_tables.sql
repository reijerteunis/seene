-- Trade record v1, part 6 of 8: nothing relation-shaped is born reachable, and a
-- view has to read its base tables as the caller. SEEN-008, F19.
--
-- What parts 1 to 5 secured and what they all stopped short of. Every tenancy,
-- privilege and append-only guarantee this ticket writes is expressed over
-- `relkind = 'r'`: the do-loops that enable row-level security and create the one
-- policy, the per-table revoke in part 4, part 4's own self-check, and every
-- assertion in packages/core/db/schema.test.ts. That is an ordinary table and
-- nothing else. Four other relation kinds hold rows and are served through the
-- Data API exactly as a table is, and none of them was looked at.
--
-- Measured against this stack in a rolled-back transaction with two tenants
-- seeded, before this file existed. `anon` is refused public.shipments with
-- SQLSTATE 42501, which is part 4 working. Three lines later:
--
--   create view public.buyer_book as
--     select tenant_id, buyer_name, buyer_address from public.shipments;
--
-- and `anon` reads both tenants' buyer name and buyer address through it. The
-- guard counted twenty-nine relations of kind `r` and saw no view at all, so
-- nothing in this ticket would have failed. SEEN-046 and SEEN-024 are the tickets
-- that will want exactly such a view over the trade record.
--
-- Two things made that true at once and this migration answers both, because
-- either alone is half a fix. The default access control list of schema public
-- granted `anon` and `authenticated` everything on the view the moment it was
-- created, so it was reachable; and a view is not subject to the row-level
-- security of the tables underneath it unless it is created `with
-- (security_invoker = true)`, so once reached it answered with every tenant's
-- rows. A materialised view cannot be fixed by the second at all: it is a stored
-- copy of the rows its owner could see when it was refreshed, so there is no
-- request for a policy to be applied to, and the rule for one is therefore not how
-- to create it but that it does not belong in a schema the Data API serves.
--
-- Forward only, as parts 1 to 5: the local stack is reset rather than rolled back.

-- Born unreachable ----------------------------------------------------------
--
-- `alter default privileges` is what grants on objects that do not exist yet, and
-- it is the statement parts 1 to 4 were written to keep out of the migrations. It
-- is also the only statement that can take such a grant away, so this is the one
-- place it appears, in its revoking direction, and the test that forbids it is
-- narrowed to its granting form rather than carrying an exception for this file.
-- A revoke can only narrow.
--
-- `on tables` in this grammar does not mean tables. It is `defaclobjtype = 'r'`,
-- which is every relation kind a `create table`, `create view`, `create
-- materialized view` or `create foreign table` produces, and that is precisely
-- why one statement closes the whole class rather than only the one view that was
-- measured.
--
-- The first review of SEEN-008 left this standing and said so: "pg_default_acl
-- still grants the four write privileges to anon and authenticated on tables that
-- do not exist yet, so the next migration's table is born writable by the role a
-- browser is bound to", named as detection rather than prevention. It was worse
-- than that paragraph knew, because the detection did not cover a view either.
--
-- `service_role` keeps its defaults on purpose. It bypasses row-level security by
-- design, no browser request is ever bound to it, and part 4 grants it per table
-- by name in any case; taking its default away would make a later ticket's table
-- unreachable by the API for reasons that have nothing to do with this defect.
alter default privileges for role postgres in schema public
  revoke all on tables from anon, authenticated;

-- The limit this migration could not close, stated rather than left to be found.
--
-- There are two grantors of default privileges on schema public in a Supabase
-- database, `postgres` and `supabase_admin`, and a default privilege applies only
-- to the objects the grantor itself creates. Measured: the view in the
-- reproduction above carried `anon=arwdDxtm/postgres`, so `postgres` is the
-- grantor that applied, because the Supabase CLI runs every migration as
-- `postgres` and every relation in this schema is owned by it. The statement above
-- therefore closes the route this repository's own migrations take.
--
-- `supabase_admin`'s identical entry is still standing and this role cannot remove
-- it: `alter default privileges for role supabase_admin ...` is refused with
-- SQLSTATE 42501, "permission denied to change default privileges", because
-- `postgres` is not a member of `supabase_admin`. What remains open is a relation
-- created in public by `supabase_admin` itself, which nothing in this repository
-- does and which would be a platform action rather than a migration. It is named
-- here so that a later reader measuring the default access control list and
-- finding two entries knows that one of them was left deliberately.
--
-- And one step deliberately not taken. An event trigger on `ddl_command_end` would
-- refuse a non-invoker view in public at the moment it is created, and this role
-- can own one. It is not written, because it would fire on every later ticket's
-- DDL in a schema this ticket does not own the future of, and because with the
-- defaults revoked a view added later is unreachable by a browser-bound role until
-- somebody writes a grant for it by hand. The rule below and the guards in
-- packages/core/db/schema.test.ts carry the deliberate case.

-- The rule for a view, and for a materialised view -------------------------
--
-- Stated as a check that runs rather than as a paragraph, on the same principle as
-- part 4's self-check: a rule the database asserts is a rule, and a rule in a
-- comment is a hope. There is no view in the public schema today, so this passes
-- over nothing at the moment it is written, and that is exactly what
-- packages/core/db/schema.test.ts is for: it makes the same three assertions and
-- shows itself a view and a materialised view in a rolled-back transaction, so a
-- checker that measured nothing could not pass.
do $$
declare
  offenders text;
begin
  -- Anything relation-shaped that is not an ordinary table is stripped of every
  -- privilege the two browser-bound roles could hold on it, whatever granted it.
  -- A no-op today, and the statement rather than the comment is what stays true
  -- when this migration is re-applied against a schema that has one.
  for offenders in
    select c.relname
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind in ('f', 'm', 'p', 'v')
     order by c.relname
  loop
    execute format('revoke all privileges on public.%I from anon, authenticated', offenders);
  end loop;

  -- A view that runs with its owner's rights reads its base tables as the
  -- migration role, which every policy in this schema is written on the
  -- assumption never happens for a request.
  select string_agg(format('%s is a view without security_invoker', c.relname),
                    ', ' order by c.relname)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relkind = 'v'
     and coalesce(
           (select o.option_value
              from pg_catalog.pg_options_to_table(c.reloptions) o
             where o.option_name = 'security_invoker'),
           'false') not in ('1', 'on', 'true', 'yes');

  if offenders is not null then
    raise exception 'a view in schema public runs with its owner rights, so row-level security '
      'is not applied to a request that reads it: %', offenders;
  end if;

  -- And a materialised view, which no option can put a policy back on.
  select string_agg(format('%s is a materialised view', c.relname), ', ' order by c.relname)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relkind = 'm';

  if offenders is not null then
    raise exception 'a materialised view is in schema public, and row-level security can never '
      'apply to one: it is a stored copy of the rows its owner could see. Put it in a schema the '
      'Data API does not serve, or make it a view with security_invoker: %', offenders;
  end if;
end;
$$;

-- And this migration checks its own outcome, as part 4 does -----------------
--
-- The revoke above is one statement and a silent partial result is a boundary
-- nobody would notice was open, which is the whole shape of the defect it closes.
do $$
declare
  offenders text;
begin
  select string_agg(format('%s holds %s by default from %s',
                           a.grantee::regrole::text, a.privilege_type,
                           d.defaclrole::regrole::text),
                    ', ' order by a.grantee::regrole::text, a.privilege_type)
    into offenders
    from pg_catalog.pg_default_acl d
    cross join lateral aclexplode(d.defaclacl) a
   where d.defaclnamespace = 'public'::regnamespace
     and d.defaclobjtype = 'r'
     -- The grantor this role can act for. The `supabase_admin` entry beside it is
     -- the limit stated above and is not asserted here, because an assertion that
     -- can never pass is not a check.
     and d.defaclrole = 'postgres'::regrole
     and a.grantee in ('anon'::regrole, 'authenticated'::regrole);

  if offenders is not null then
    raise exception 'the default privileges on schema public still reach a browser-bound role, '
      'so the next table, view or materialised view created here is born readable by it: %',
      offenders;
  end if;

  -- And not over-broad in the other direction: the revoke must not have reached
  -- the role every worker and API call connects as, which would leave the whole
  -- product unable to read its own record after the next migration.
  if not exists (
    select 1
      from pg_catalog.pg_default_acl d
      cross join lateral aclexplode(d.defaclacl) a
     where d.defaclnamespace = 'public'::regnamespace
       and d.defaclobjtype = 'r'
       and d.defaclrole = 'postgres'::regrole
       and a.grantee = 'service_role'::regrole
       and a.privilege_type = 'SELECT'
  ) then
    raise exception 'the revoke was over-broad: service_role no longer holds select by default '
      'on a relation created in schema public, and every worker and API call in this product '
      'connects as it';
  end if;
end;
$$;
