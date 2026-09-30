-- Trade record v1, part 6 of 8: nothing relation-shaped is born reachable, a view
-- has to read its base tables as the caller, neither a materialised view nor a
-- foreign table belongs here at all, a table owes the tenancy whichever of the two
-- kinds of table it is, and neither a function nor a sequence here answers a
-- browser.
-- SEEN-008, F19, F29, F32, F33 and F35.
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
-- paragraph above answered one quarter of that sentence. A sequence is the quarter
-- after this one, F33, and it is closed below.
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

-- And the grant underneath that one, which five rounds of this ticket recorded as
-- unreachable and which is reachable ----------------------------------------
--
-- This paragraph corrects the file it is in. The rounds that wrote F32 concluded
-- that a function cannot be prevented from being born callable by `anon`, only
-- detected: PostgreSQL grants EXECUTE to PUBLIC on every routine as a baseline, a
-- `pg_default_acl` entry is merged into that baseline by adding to it, so a revoke
-- cannot subtract the grant that actually reaches a browser. That conclusion was
-- written into this file at length, into journal notes 154 and 159 and into the
-- ticket's Outcome, and the seventh Codex review of SEEN-008 (F39) demonstrated it
-- is false. It is wrong in one respect and everything else in it follows: the
-- impossibility belonged to the statement those rounds tried, not to PostgreSQL.
--
-- A default privilege is filed against a grantor and, optionally, a schema. The
-- revoke above names `in schema public`, so it is filed against schema public, and
-- the built-in EXECUTE to PUBLIC is filed against no schema at all. A per-schema
-- entry cannot subtract a grant that is not in its scope, which is the whole of
-- what those rounds measured and is true. A default privilege written with no `in
-- schema` clause is filed the same way the built-in grant is, and it can.
--
-- Measured on PostgreSQL 17.6 on this stack, both forms one after the other in a
-- rolled-back transaction, before this statement existed. With `alter default
-- privileges for role postgres in schema public revoke execute on functions from
-- public`, the entry for schema public read `{postgres=X/postgres,
-- service_role=X/postgres}` and the function created next was still born
-- `{=X/postgres,postgres=X/postgres,service_role=X/postgres}` with
-- `has_function_privilege('anon', ..., 'EXECUTE')` true. With the statement below,
-- `pg_default_acl` gains a row whose `defaclnamespace` is 0 reading
-- `{postgres=X/postgres}`, and the function created next is born
-- `{postgres=X/postgres,service_role=X/postgres}`: no PUBLIC entry at all, `anon`
-- and `authenticated` both false, `service_role` still true. So prevention here is
-- complete, on the same terms the sequence revoke below is, and the detection this
-- file describes as the bound is now the second line and not the first.
--
-- What it costs, because it is the widest statement in this migration set and the
-- only one that is not confined to a schema. It applies to every routine the
-- migration role creates anywhere, so what it takes away is exactly the built-in
-- grant and nothing that anybody wrote down: a per-schema entry naming a role is
-- untouched, which is why `service_role` keeps EXECUTE on the next function in
-- public and why the `storage` entry, which names `anon` and `authenticated` on
-- functions, is not narrowed by this either. The one place it changes an outcome in
-- this repository is schema `seen`, which carries no entry of its own: a helper
-- created there after this file is born `{postgres=X/postgres}` and no other role
-- can call it until its migration grants one. That is already the end state of
-- every helper parts 7 and 8 create, because each of them is followed by `revoke
-- all on function ... from public`, so nothing in this set changes shape; what
-- changes is that a helper somebody forgets to revoke is now safe by default rather
-- than callable by `anon`, and a helper a request must call needs the explicit
-- grant `seen.current_tenant()` already carries. Part 8's revokes are kept rather
-- than deleted, because they are what makes each file's guarantee readable in the
-- file that makes it and because they still close a routine created before this
-- statement runs.
--
-- What it does not cost, measured rather than reasoned, because a global statement
-- that broke the platform would be found by nobody until it did. An extension is
-- the one ordinary route by which a migration creates routines it did not write:
-- `create extension postgres_fdw` and `create extension citext with schema
-- extensions` were both run under this statement in a rolled-back transaction, and
-- every routine either produced is owned by `supabase_admin`, not by the migration
-- role, so this entry does not apply to them at all and `authenticated` can execute
-- them exactly as before. That is the same fact from the other side as the limit
-- below: Supabase escalates `create extension`, so the objects land under a grantor
-- this role cannot revoke for, and note 167's open item stands unchanged. A
-- migration that puts an extension in `public` without `with schema extensions`
-- still produces routines `anon` can execute, `revoke ... from anon` still answers
-- "no privileges could be revoked", and the self-check at the foot of this file is
-- still what refuses the migration. Prevention below covers what this role creates;
-- it does not cover what this role asks the platform to create.
alter default privileges for role postgres
  revoke execute on functions from public;

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
-- The second limit this file used to state here is withdrawn, and what stands in
-- its place is above rather than below. It read that `alter default privileges`
-- cannot take away the EXECUTE PostgreSQL grants to PUBLIC on every routine, so
-- prevention was impossible and detection with a bound was all there was. That is
-- false, F39 demonstrated it, and the statement that closes it is the global revoke
-- two sections up with the measurement beside it. It is corrected here as well as
-- there because this is where a reader looking for the limits of this file arrives,
-- and a paragraph that had been wrong for five rounds should not be found only by
-- somebody who read the whole file from the top.
--
-- So the three classes this file reaches are now alike: a relation, a routine and a
-- sequence created next by the migration role are each born unreachable by a
-- browser-bound role, and the guards in packages/core/db/schema.test.ts are the
-- second line rather than the only one. What the guards still carry alone is the
-- grantor limit above, an object `supabase_admin` creates, which no statement this
-- role can write reaches at all.
--
-- And one step deliberately not taken, on a reason that is now the only one it has.
-- An event trigger on `ddl_command_end` would refuse a non-invoker view in public
-- at the moment it is created, and this role can own one. When this file first
-- declined it, part of the reason given was that a relation added later is
-- unreachable until somebody grants it while a function added later is reachable at
-- once, which made the decline look like a choice taken in spite of a known hole.
-- The hole is closed, so the decline now rests on what it should have rested on:
-- an event trigger fires on every later ticket's DDL in a schema this ticket does
-- not own the future of, and with the defaults revoked nothing this role creates in
-- public is reachable by a browser-bound role until somebody writes a grant for it
-- by hand. The rule below and the guards in packages/core/db/schema.test.ts carry
-- the deliberate case, which is somebody writing that grant on purpose.

-- Born out of reach, which is the last quarter and the one a revoke finishes ---
--
-- A sequence is `defaclobjtype = 'S'`, which is neither of the two classes above,
-- and the sixth review of SEEN-008 (F33) is that it was still standing after F32
-- closed the functions. `supabase/config.toml` names the class it serves as
-- "tables, views, sequences and functions": `'r'` was the first quarter, `'f'` the
-- second, and this statement is the fourth word of that sentence answered.
--
-- Measured against this stack in a rolled-back transaction before this section
-- existed. `pg_default_acl` for schema public, type `S`, read
-- `{postgres=rwU/postgres,anon=rwU/postgres,authenticated=rwU/postgres,
-- service_role=rwU/postgres}` from both grantors, so
--
--   create table public.ingest_batch (
--     id bigint generated by default as identity primary key, ...);
--
-- which names no sequence anywhere in it, created `public.ingest_batch_id_seq`
-- holding all three privileges for both browser-bound roles. As `anon`: `nextval`
-- was accepted and returned 1, `select last_value` returned a count of rows
-- aggregated over every tenant, and `setval(seq, 1)` was accepted, which makes the
-- next ingest insert collide on the primary key until the sequence catches up.
-- SEEN-014's ingest and SEEN-021's findings are the tickets that would write such a
-- column without ever deciding to create a sequence.
--
-- Two things about that exposure are unlike anything above it. Row-level security
-- is not a defence that merely happens to be missing: a sequence holds no row, so
-- there is nothing for a policy to be applied to, and no option, no
-- `security_invoker` and no rewriting would put one in the way. And the write half
-- is not a read at all: `nextval` and `setval` are outside transaction control, so
-- what `anon` does to the number survives the rollback of the statement it did it
-- in, which is why the guard in packages/core/db/schema.test.ts measures the value
-- left behind and not only the answer the call got.
--
-- And the one respect in which this revoke is simpler than the two statements above
-- it, which is worth saying because all three now buy the same thing by different
-- routes. PostgreSQL grants EXECUTE to PUBLIC on every routine it creates, so a
-- function needs two statements: the per-schema revoke takes the named grants away
-- and the global revoke takes the built-in one away underneath it. PostgreSQL
-- grants a new sequence nothing to PUBLIC, so there is no baseline underneath this
-- one and one statement is the whole of it. Measured on PostgreSQL 17.6 on this
-- stack with this statement applied:
-- a sequence created next is born `{postgres=rwU/postgres,service_role=rwU/postgres}`
-- with no PUBLIC entry at all, `has_sequence_privilege('anon', ...)` is false for
-- USAGE, SELECT and UPDATE alike, and `nextval`, `select last_value` and `setval`
-- are each refused 42501 - on the sequence an identity column creates exactly as on
-- one `create sequence` made.
--
-- The grantor limit stated above holds here too and was measured here rather than
-- assumed to carry over: `alter default privileges for role supabase_admin in
-- schema public revoke all on sequences from anon, authenticated` is refused with
-- SQLSTATE 42501, "permission denied to change default privileges", exactly as it
-- is for the `r` and `f` entries, so `supabase_admin`'s identical `S` entry still
-- stands and applies to a sequence `supabase_admin` itself creates, which nothing
-- in this repository does.
--
-- `service_role` keeps its default here for the reason it keeps its default above,
-- and it needs it more plainly than anywhere else: without USAGE on the sequence,
-- an insert into a table with an identity column is refused outright for the role
-- every worker and API call in this product connects as.
alter default privileges for role postgres in schema public
  revoke all on sequences from anon, authenticated;

-- And the sequences already in this schema, which are none of them -----------
--
-- The same principle as the loop over the routines, and the same confirming rather
-- than assuming: there is no sequence in public today, because every key in this
-- schema is a uuid with a default, and the statement rather than the comment is
-- what stays true when these migrations are re-applied against a schema somebody
-- has added an identity column to.
--
-- PUBLIC is in this revoke list, as it is for a routine and unlike the relation
-- loop below, and the reason is not the one it is for a routine. PostgreSQL grants
-- a sequence nothing to PUBLIC; what makes the wider list necessary is that the
-- check at the foot of this file asks `has_sequence_privilege`, which answers true
-- through a grant to PUBLIC somebody wrote by hand, so a strip that could not reach
-- what the check can see would make this migration fail on its own output.
do $$
declare
  counter text;
begin
  for counter in
    select format('public.%I', c.relname)
      from pg_catalog.pg_class c
      join pg_catalog.pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind = 'S'
     order by 1
  loop
    execute format('revoke all privileges on sequence %s from public, anon, authenticated',
                   counter);
  end loop;
end;
$$;

-- The rule for a view, a materialised view and a foreign table --------------
--
-- Stated as a check that runs rather than as a paragraph, on the same principle as
-- part 4's self-check: a rule the database asserts is a rule, and a rule in a
-- comment is a hope. There is none of the three in the public schema today, so
-- this passes over nothing at the moment it is written, and that is exactly what
-- packages/core/db/schema.test.ts is for: it makes the same assertions and shows
-- itself each of the three kinds in a rolled-back transaction, so a checker that
-- measured nothing could not pass.
--
-- The third kind is the seventh review of SEEN-008 (F35), and what it found was an
-- asymmetry rather than a route out. The privilege strip below covers a foreign
-- table, because `defaclobjtype = 'r'` and `relkind in ('f', 'm', 'v')` both do, so
-- one created here is born holding nothing for `anon` or `authenticated` and the
-- suite catches a `grant select` a later migration writes by hand. What no
-- statement in this set did was forbid the relation, while packages/core/db/
-- tables.ts told the next reader that its rule was the materialised view's. So the
-- exposure was closed and the rule was not, and this file said one thing where it
-- did another.
--
-- It is closed by refusing the kind rather than by writing the weaker rule down,
-- because every reason a materialised view does not belong here holds for a foreign
-- table and one more does. Measured on this stack in a rolled-back transaction, on
-- a foreign table over a `postgres_fdw` server: `enable row level security` is
-- refused 42809 and `create policy` is refused 42809, "is not a table", so this
-- schema's tenancy cannot be written on one at all - which is also what makes
-- excluding the kind from the tenancy checks sound rather than convenient; part 5's
-- reference to `public.tenants` is refused 0A000, "foreign key constraints are not
-- supported on foreign tables", so an erased tenant's rows in one are outside part
-- 8's cascade altogether; and `information_schema.tables` reports it in this schema
-- regardless, as FOREIGN beside the twenty-nine BASE TABLEs, which is the sentence
-- criterion 2 of this ticket is written in. A materialised view is at least a copy
-- of rows this database produced and could be made to be refreshed; a foreign
-- table's rows were never here, and no statement of this database decides which of
-- them a caller sees. `service_role`, the role every worker and API call in this
-- product connects as, would read it unfiltered with nothing narrowing what it
-- sees.
--
-- What that costs, and the way out, because a rule nobody can satisfy is deleted by
-- whoever hits it first. A later ticket that wants to read a reporting warehouse, a
-- second Postgres or one of the Supabase wrappers through this database creates the
-- foreign table in a schema the Data API does not serve: `supabase/config.toml`
-- exposes `public` and `graphql_public` and nothing else, and `seen` is already
-- such a schema. That is the same answer this file gives a materialised view, and
-- it costs one qualified name. If those rows have to reach the trade record itself,
-- the answer this architecture already gives is the one every connector takes: they
-- are ingested into a table in `public` that carries `tenant_id`, a policy and a
-- reference to `public.tenants`, so they are governed here rather than read from
-- somewhere this database can promise nothing about.
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

  -- And a foreign table, which is the same rule and not a weaker one. The two
  -- statements this schema's tenancy is made of are both refused on one, and so is
  -- the reference to public.tenants that part 5 requires and part 8 erases through.
  select string_agg(format('%s is a foreign table', c.relname), ', ' order by c.relname)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relkind = 'f';

  if offenders is not null then
    raise exception 'a foreign table is in schema public, and its rows are on another server '
      'that no statement of this database governs: row-level security cannot be enabled on one, '
      'no policy can be created on one, and it cannot reference public.tenants, so it carries '
      'neither this schema''s tenancy nor the erasure that follows from it while '
      'information_schema reports it here as a table. Put it in a schema the Data API does not '
      'serve, or ingest its rows into a table of this schema that carries tenant_id: %', offenders;
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
-- The revokes above are three statements and a silent partial result is a boundary
-- nobody would notice was open, which is the whole shape of the defect they close.
-- Every class `pg_default_acl` files is read and not the ones the round in hand was
-- looking at, because a subset being right is how F32 and F33 sat under six
-- reviews: this check asked for `r` and passed while `anon` held EXECUTE on every
-- function and USAGE on every sequence schema public was about to gain.
--
-- `T`, a type or a domain, is in the list and has no revoke beside it, which is
-- deliberate and is stated rather than left for a seventh round to find. Measured:
-- `pg_default_acl` holds no `T` row for this schema from either grantor, so there
-- is nothing to revoke, and `alter default privileges ... revoke all on types`
-- records no row when it is run. `anon` does hold USAGE on every type here through
-- the grant PostgreSQL makes to PUBLIC on a type it creates, which no default
-- privilege can reach, exactly as for a function - and that one is harmless,
-- because USAGE on a type is not a route to a row: it permits naming the type in a
-- cast, a column or a declaration, no type in this schema holds data, the composite
-- types here are the row types of the tables, and reading a table's rows goes
-- through the table privilege part 4 governs. `config.toml` names four classes and
-- not five for the same reason. So what `T` is asked for below is only that no
-- later migration files a default privilege on one.
do $$
declare
  offenders text;
begin
  select string_agg(format('%s holds %s by default on every %s from %s',
                           case when a.grantee = 0 then 'PUBLIC'
                                else a.grantee::regrole::text end,
                           a.privilege_type,
                           case d.defaclobjtype when 'S' then 'sequence'
                                                when 'T' then 'type'
                                                when 'f' then 'function'
                                                else 'relation' end,
                           d.defaclrole::regrole::text),
                    ', ' order by d.defaclobjtype, a.grantee, a.privilege_type)
    into offenders
    from pg_catalog.pg_default_acl d
    cross join lateral aclexplode(d.defaclacl) a
   where d.defaclnamespace = 'public'::regnamespace
     and d.defaclobjtype in ('S', 'T', 'f', 'r')
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
      'so the next table, view or materialised view created here is born readable by it, the '
      'next function is born callable by it, and the next sequence, which an identity column '
      'creates without naming one, is born readable and settable by it: %', offenders;
  end if;

  -- And not over-broad in the other direction: the revokes must not have reached
  -- the role every worker and API call connects as, which would leave the whole
  -- product unable to read its own record after the next migration, unable to call
  -- the next function this schema gains, and unable to insert a row at all into the
  -- next table an identity column numbers, because that insert needs USAGE on the
  -- sequence behind the column. `T` is not asked for here and cannot be: there is no
  -- `T` entry for `service_role` either, and an assertion that can never pass is not
  -- a check.
  select string_agg(format('%s on every %s', missing.privilege_type, missing.class), ', ')
    into offenders
    from (values ('r', 'relation', 'SELECT'), ('f', 'function', 'EXECUTE'),
                 ('S', 'sequence', 'USAGE'))
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

  -- And the one guarantee in this file that is filed against no schema, asked for
  -- by the shape of its own row rather than by what it grants. The global revoke is
  -- the statement that takes PostgreSQL's built-in EXECUTE to PUBLIC off every
  -- routine this role creates next, and a grant back to PUBLIC does not leave a
  -- weaker row behind: it deletes the row, because the entry then matches the
  -- built-in default and PostgreSQL stops filing it. So the check is that the row
  -- exists and that PUBLIC is not in it, and absence is the failure this catches on
  -- a re-apply. `defaclnamespace = 0` is how a default privilege with no `in schema`
  -- clause is stored, and it is asked for by number because there is no schema to
  -- name and a join to `pg_namespace` drops the row.
  if not exists (
    select 1
      from pg_catalog.pg_default_acl d
     where d.defaclnamespace = 0
       and d.defaclobjtype = 'f'
       and d.defaclrole = 'postgres'::regrole
       and not exists (
         select 1 from aclexplode(d.defaclacl) a where a.grantee = 0
       )
  ) then
    raise exception 'the global default privilege on functions is not in place, so the next '
      'routine this role creates is born with PostgreSQL''s own EXECUTE to PUBLIC and every '
      'role there is can call it, `anon` included. A per-schema revoke cannot subtract that '
      'grant, which is what the sixth review of this ticket concluded was the end of the '
      'matter and the seventh disproved';
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

  -- And the sequences that already exist, asked the same way and for the same
  -- reason: `has_sequence_privilege` answers what a role can do, where the
  -- sequence's own list is null on one nobody has granted or revoked anything on
  -- and names no role for a grant made to PUBLIC. This passes over nothing today,
  -- because every key in this schema is a uuid with a default and no identity or
  -- `bigserial` column exists yet; the loop above is what keeps the sentence true
  -- when these migrations are re-applied against a schema that has one.
  select string_agg(format('%s can be %s by %s', reachable.name, reachable.privilege,
                           reachable.role),
                    ', ' order by reachable.name, reachable.role, reachable.privilege)
    into offenders
    from (
      select format('public.%I', c.relname) as name, r.rolname as role, p.privilege
        from pg_catalog.pg_class c
        join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        cross join pg_catalog.pg_roles r
        cross join unnest(array['SELECT', 'UPDATE', 'USAGE']) as p(privilege)
       where n.nspname = 'public' and c.relkind = 'S'
         and r.rolname in ('anon', 'authenticated')
         and has_sequence_privilege(r.oid, c.oid, p.privilege)
    ) as reachable;

  if offenders is not null then
    raise exception 'a sequence in schema public can be reached by a browser-bound role. A '
      'sequence holds no row, so no policy of this database is ever applied to one: what SELECT '
      'lends is a count of rows across every tenant, and what UPDATE lends is a setval whose '
      'effect on the next insert no rollback undoes: %', offenders;
  end if;
end;
$$;
