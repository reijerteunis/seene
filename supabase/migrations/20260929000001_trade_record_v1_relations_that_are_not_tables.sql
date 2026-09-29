-- Trade record v1, part 6 of 8: nothing relation-shaped is born reachable, a view
-- has to read its base tables as the caller, a table owes the tenancy whichever of
-- the two kinds of table it is, and no function here answers a browser.
-- SEEN-008, F19, F29 and F32.
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
-- A fifth review came back to the same sentence from the other end. Of the four
-- kinds, one is a table: a partitioned table answers to `relkind = 'p'`, holds its
-- rows in its partitions, and can carry the whole of this schema's tenancy,
-- because `enable row level security` and `create policy` are both accepted on one
-- and the policy is applied to every row a query through the parent returns. F19
-- widened the privilege half to all four kinds and wrote the tenancy half down as
-- a limit it was not closing; F29 is that limit, and the rule for a partitioned
-- table below is where it is closed. So this file now carries two rules and not
-- one: what a relation this schema's policies cannot govern may hold, and what a
-- table owes whichever of the two kinds of table it is.
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

-- Born uncallable, which is one object class over and not the same statement --
--
-- `on tables` above is `defaclobjtype = 'r'` and that is the whole of what it
-- reaches. A function is `defaclobjtype = 'f'`, which nothing in parts 1 to 6 had
-- touched, so the sixth review of SEEN-008 (F32) is F19's defect one class over, in
-- the file that was written to close F19. `supabase/config.toml` names the class it
-- serves in its own comment, "tables, views, sequences and functions", and the
-- paragraph above answered one quarter of that sentence. A sequence is a quarter
-- still open and is F33.
--
-- Measured against this stack in a rolled-back transaction with two tenants
-- inserted, before this section existed. `pg_default_acl` for schema public, type
-- `f`, read `{postgres=X/postgres,anon=X/postgres,authenticated=X/postgres,
-- service_role=X/postgres}`, so
--
--   create function public.probe_tenant_directory() returns setof text
--     language sql security definer as $$ select name from public.tenants $$;
--
-- was born with `anon=X/postgres` in its own access control list, `anon` was
-- refused public.tenants with SQLSTATE 42501, and `anon` read both tenants' names
-- through it.
--
-- Why this is worse than the view above rather than the same. A view can be made to
-- read its base tables as the caller and then the tenancy applies to it; a
-- `security definer` function runs as its owner, no table in this schema carries
-- `relforcerowsecurity`, and the owner of every one of them is the migration role,
-- so there is no option that puts a policy back in the way of a request. And schema
-- public is served by the Data API, so such a function is a `POST /rpc/<name>`
-- endpoint reachable with the anon key. That is the ordinary Supabase remote
-- procedure pattern, which is how SEEN-024's ops console and SEEN-035's approval
-- inbox would write one without ever deciding to publish it.
--
-- One statement covers a function, a procedure and an aggregate alike, because all
-- three are `f` to the privilege system and all three are exposed by PostgREST the
-- same way; the grammar spells it `on routines` as well and means the same thing.
-- `service_role` keeps its default here for the reason it keeps its default above.
alter default privileges for role postgres in schema public
  revoke all on functions from anon, authenticated;

-- And the functions already in this schema, which are none of them -----------
--
-- A default privilege says nothing about an object that already exists, so the
-- revoke above leaves a function parts 1 to 5 created exactly as it was. There is
-- none: every helper this schema needs is in schema `seen`, which the Data API does
-- not serve. The loop is written anyway, on the same principle as the one below it,
-- because it is the statement and not the comment that stays true when these
-- migrations are re-applied against a schema somebody has added a function to, and
-- because "there are none" is worth confirming rather than assuming.
--
-- PUBLIC is in this revoke list and is not in the one below, and the difference is
-- the whole of what makes a function unlike a relation. PostgreSQL grants EXECUTE
-- to PUBLIC on every routine it creates, whatever any migration says, so for a
-- function that grant is the one that actually reaches `anon` and `revoke ... from
-- anon, authenticated` alone would leave it standing. Measured on the function
-- above: after `revoke all on function ... from public`, which part 8 writes five
-- times over its own helpers, the list still read `anon=X/postgres` and `anon` still
-- read both tenants' names; only revoking from the two named roles as well refused
-- it 42501. Neither statement is the other's shorthand and this loop writes both.
--
-- ROUTINE rather than FUNCTION in the grammar, because FUNCTION does not accept a
-- procedure and a loop over the catalogue cannot know which it is holding.
do $$
declare
  callable text;
begin
  for callable in
    select format('public.%I(%s)', p.proname,
                  pg_catalog.pg_get_function_identity_arguments(p.oid))
      from pg_catalog.pg_proc p
      join pg_catalog.pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public'
     order by 1
  loop
    execute format('revoke all privileges on routine %s from public, anon, authenticated',
                   callable);
  end loop;
end;
$$;

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
-- `postgres` is not a member of `supabase_admin`. That is true of the `f` entry
-- exactly as F19's round found it of the `r` entry, and it was measured again this
-- round rather than assumed to carry over. What remains open is an object created
-- in public by `supabase_admin` itself, which nothing in this repository does and
-- which would be a platform action rather than a migration. It is named here so
-- that a later reader measuring the default access control list and finding two
-- entries per class knows that one of them was left deliberately.
--
-- The second limit, and this one has no grantor behind it. `alter default
-- privileges` can take the two named grants off the functions created next and it
-- cannot take away the EXECUTE PostgreSQL grants to PUBLIC on every routine,
-- because that grant is part of the default access control list a new object starts
-- from and a `pg_default_acl` entry is merged into that default by adding to it.
-- Measured on PostgreSQL 17.6 on this stack, with `alter default privileges for
-- role postgres in schema public revoke all on functions from public` applied on
-- top of the revoke above: `pg_default_acl` reads
-- `{postgres=X/postgres,service_role=X/postgres}` and the function created next is
-- still born `{=X/postgres,postgres=X/postgres,service_role=X/postgres}`, which
-- `has_function_privilege('anon', ..., 'EXECUTE')` answers true.
--
-- So for a function, unlike a relation, the revoke above is not the whole of
-- prevention and this file does not claim it is. What it buys is that the next
-- function in public is not born with `anon` and `authenticated` written into its
-- own list, so one `revoke ... from public` beside its `create function` closes it
-- rather than half-closing it. What carries the rest is the guard in
-- packages/core/db/schema.test.ts, which asks `has_function_privilege` of every
-- routine in this schema for both browser-bound roles: the pull request that adds
-- the first function to public fails the suite inside itself. The one mechanism
-- that would make prevention complete is the event trigger the next paragraph
-- declines, and the reason it gives holds for a relation and does not hold here,
-- because a relation added later is unreachable until somebody grants it and a
-- function added later is reachable at once. Reversing a decision this file records
-- is a gate's call and not a rework round's, so it is written down as the choice it
-- is rather than taken quietly.
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
  -- Anything relation-shaped whose rows no policy of this database governs is
  -- stripped of every privilege the two browser-bound roles could hold on it,
  -- whatever granted it. A no-op today, and the statement rather than the comment
  -- is what stays true when this migration is re-applied against a schema that has
  -- one.
  --
  -- A partitioned table is not in this set and was until F29. Stripping one would
  -- undo the select part 4 grants it as a table and leave the product unable to
  -- read its own record through it; what a partitioned table owes is the rule
  -- below, which is the rule every other table is held to.
  for offenders in
    select c.relname
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind in ('f', 'm', 'v')
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

-- The rule for a partitioned table -----------------------------------------
--
-- The three kinds above are told where they may be and what they may not hold,
-- because this schema's tenancy cannot be expressed over any of them. A
-- partitioned table is the one kind in F19's list of four that it can: `enable row
-- level security` and `create policy` are both accepted on one and the policy is
-- applied to every row a query through the parent returns. So the rule for one is
-- not that it stays out of this schema but that it owes exactly what every other
-- table owes, and the fifth Codex review of SEEN-008 (F29) is that nothing asked
-- it for any of it. The do-loops in parts 1 to 3 enable row-level security on the
-- tables they name, part 4's loop read `relkind = 'r'`, and so did every guard in
-- packages/core/db/schema.test.ts, so a partitioned table added by a later
-- migration would have carried no tenant_id, no enabled policy and no failing
-- test, with criterion 2's "100% of them" still reading as a pass.
--
-- A partition is a relation of kind `'r'` and is therefore a row of this check in
-- its own right rather than something its parent covers, and it has to be.
-- Measured on this stack in a rolled-back transaction: enabling row-level security
-- on the parent leaves `relrowsecurity` false on the partition, the policy created
-- on the parent is the parent's alone in `pg_policies`, and `authenticated`
-- granted select on the partition reads both tenants' rows through it where the
-- same role reading through the parent reads one tenant's. The privilege half is
-- closed by default in that case and the policy half is not, which is why the
-- check below asks each relation for its own tenant_id, its own enabled
-- row-level security and its own permissive policy.
--
-- What this check cannot do, stated rather than left to be assumed. It sees the
-- schema as it stands when this migration runs, so a partitioned table added by a
-- later ticket's migration is caught by packages/core/db/schema.test.ts on the
-- next run of the suite and not by this file at the moment it is created. Only an
-- event trigger would refuse it there, and this migration declines one above for
-- the reason it gives: it would fire on every later ticket's DDL in a schema this
-- ticket does not own the future of.
do $$
declare
  offenders text;
begin
  select string_agg(format('%s, %s, %s', name, kind, problems), '; ' order by name)
    into offenders
    from (
      select c.relname as name,
             case c.relkind when 'p' then 'a partitioned table' else 'an ordinary table' end
               as kind,
             concat_ws(' and ',
               case when not exists (
                 select 1 from pg_catalog.pg_attribute a
                  where a.attrelid = c.oid and a.attname = 'tenant_id'
                    and a.attnum > 0 and not a.attisdropped
               ) then 'carries no tenant_id column' end,
               case when not c.relrowsecurity
                 then 'does not have row-level security enabled' end,
               -- The permissive policies are the ones that decide what a role may
               -- see: row-level security ORs them together, and a table with none
               -- of them shows an ordinary role nothing at all, which is a denial
               -- rather than a tenancy. A restrictive policy can only narrow, so
               -- it is not what this asks for.
               case when not exists (
                 select 1 from pg_catalog.pg_policy p
                  where p.polrelid = c.oid and p.polpermissive
               ) then 'carries no permissive policy' end) as problems
        from pg_catalog.pg_class c
        join pg_catalog.pg_namespace n on n.oid = c.relnamespace
       where n.nspname = 'public' and c.relkind in ('p', 'r')
    ) as checked
   where problems <> '';

  if offenders is not null then
    raise exception 'a table in schema public does not carry the tenancy every table in this '
      'schema owes, so a row in it belongs to no tenant or is shown to every tenant: %', offenders;
  end if;

  -- And not vacuously: a check of the shape "the tables failing this are none"
  -- passes against a schema with no tables, which is how record 8 of this ticket
  -- read an empty database as a pass.
  if not exists (
    select 1
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind in ('p', 'r')
  ) then
    raise exception 'there is not one table in schema public, so the tenancy check above proves '
      'nothing about this schema and parts 1 to 3 of this set cannot have run';
  end if;
end;
$$;

-- And this migration checks its own outcome, as part 4 does -----------------
--
-- The revokes above are two statements and a silent partial result is a boundary
-- nobody would notice was open, which is the whole shape of the defect they close.
-- Both classes are read, because one of them being right is how F32 sat under six
-- reviews: this check asked for `r` and passed while `anon` held EXECUTE on every
-- function schema public was about to gain.
do $$
declare
  offenders text;
begin
  select string_agg(format('%s holds %s by default on every %s from %s',
                           case when a.grantee = 0 then 'PUBLIC'
                                else a.grantee::regrole::text end,
                           a.privilege_type,
                           case d.defaclobjtype when 'f' then 'function'
                                                else 'relation' end,
                           d.defaclrole::regrole::text),
                    ', ' order by d.defaclobjtype, a.grantee, a.privilege_type)
    into offenders
    from pg_catalog.pg_default_acl d
    cross join lateral aclexplode(d.defaclacl) a
   where d.defaclnamespace = 'public'::regnamespace
     and d.defaclobjtype in ('f', 'r')
     -- The grantor this role can act for. The `supabase_admin` entry beside it is
     -- the limit stated above and is not asserted here, because an assertion that
     -- can never pass is not a check.
     and d.defaclrole = 'postgres'::regrole
     -- Grantee 0 is PUBLIC, and it is asked for by number because `regrole` renders
     -- it as a hyphen and a check matching a grantee by name walks past it. A
     -- default privilege granted to PUBLIC reaches `anon` and `authenticated` along
     -- with every other role, so it is the same defect as the two the fifth Codex
     -- review of SEEN-008 (F30) found on the relation ACLs, on the one inventory
     -- `has_table_privilege` cannot answer: there is no relation to ask it about
     -- until the next migration creates one.
     and a.grantee in (0, 'anon'::regrole, 'authenticated'::regrole);

  if offenders is not null then
    raise exception 'the default privileges on schema public still reach a browser-bound role, '
      'so the next table, view or materialised view created here is born readable by it and the '
      'next function is born callable by it: %', offenders;
  end if;

  -- And not over-broad in the other direction: the revokes must not have reached
  -- the role every worker and API call connects as, which would leave the whole
  -- product unable to read its own record after the next migration, and unable to
  -- call the next function this schema gains.
  select string_agg(format('%s on every %s', missing.privilege_type, missing.class), ', ')
    into offenders
    from (values ('r', 'relation', 'SELECT'), ('f', 'function', 'EXECUTE'))
           as missing(objtype, class, privilege_type)
   where not exists (
     select 1
       from pg_catalog.pg_default_acl d
       cross join lateral aclexplode(d.defaclacl) a
      where d.defaclnamespace = 'public'::regnamespace
        and d.defaclobjtype = missing.objtype
        and d.defaclrole = 'postgres'::regrole
        and a.grantee = 'service_role'::regrole
        and a.privilege_type = missing.privilege_type
   );

  if offenders is not null then
    raise exception 'a revoke was over-broad: service_role no longer holds % by default in '
      'schema public, and every worker and API call in this product connects as it', offenders;
  end if;

  -- And the objects that already exist, which the revokes above say nothing about.
  -- A function is asked what a role can do with it rather than what its own list
  -- says, because PostgreSQL writes no role name into the list it grants PUBLIC,
  -- and PUBLIC reaches `anon` along with everything else.
  --
  -- This passes over nothing today, as the view rule above does: schema public
  -- holds no function and schema `seen` is where the helpers are. The suite in
  -- packages/core/db/schema.test.ts is what shows it measures something, by
  -- creating exactly the function F32 was reported on and requiring the same
  -- question to name it.
  select string_agg(format('%s can be executed by %s', callable.signature, callable.role),
                    ', ' order by callable.signature, callable.role)
    into offenders
    from (
      select p.oid::regprocedure::text as signature, r.rolname as role
        from pg_catalog.pg_proc p
        join pg_catalog.pg_namespace n on n.oid = p.pronamespace
        cross join pg_catalog.pg_roles r
       where n.nspname = 'public'
         and r.rolname in ('anon', 'authenticated')
         and has_function_privilege(r.oid, p.oid, 'EXECUTE')
    ) as callable;

  if offenders is not null then
    raise exception 'a routine in schema public can be executed by a browser-bound role, and '
      'schema public is served by the Data API, so it answers a POST /rpc call made with the '
      'anon key. A security definer one runs as its owner, which no policy in this schema '
      'governs: %', offenders;
  end if;
end;
$$;
