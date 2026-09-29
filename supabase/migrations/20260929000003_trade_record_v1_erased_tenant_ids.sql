-- Trade record v1, part 8 of 8: a tenant id an erasure has consumed is never
-- usable again. SEEN-008, F21.
--
-- What part 2 guaranteed, and the one thing it said nothing about.
-- public.audit_events is append-only in three layers: no role the application
-- uses holds update or delete, no policy on the table permits either command, and
-- seen.refuse_audit_mutation() refuses both even for the role that owns it. The
-- single exception is deliberate and is the delete the cascade from public.tenants
-- performs, because the PRD promises deletion on request within 30 days and an
-- audit table nothing could ever delete from would make that promise impossible to
-- keep. Every part of that is about removing a row. None of it is about putting
-- the tenant back.
--
-- Measured against this stack in a rolled-back transaction as `service_role`,
-- which is the role the API and the workers write as, before this file existed:
--
--   delete from public.tenants where tenant_id = X;
--   insert into public.tenants (tenant_id, name) values (X, 'whatever');
--
-- leaves zero audit events for X and a tenant row for X standing again. The id is
-- settable on insert because public.tenants.tenant_id is a plain uuid primary key
-- with a default, and everything else the cascade removed is re-ingestible:
-- orders, settlements and returns are read back from the marketplace APIs by
-- design, which is what this whole schema is for. So the audit trail is the only
-- thing permanently lost, while the id still resolves in every token, every Stripe
-- customer mapping and every invoice that names it. The erasure becomes
-- indistinguishable from nothing having happened, which is the opposite of what an
-- audit trail is for.
--
-- The fix is that the id is spent. An erasure leaves a tombstone in the registry
-- below, and an insert carrying a tombstoned id is refused outright. There is no
-- legitimate reason to reuse one, because a new tenant gets a new uuid, so there
-- is no escape hatch either: a flag or a setting that opened the refusal would be
-- the whole of the hole again, reachable by the role the defect was measured with.
--
-- And the id does not move. F27 found the first version of this file refusing the
-- insert and nothing else, so an update handed a living tenant the erased id and
-- the id was back a statement later. The rule below is the wider one it asks for:
-- public.tenants.tenant_id is never updatable at all, whatever it would be changed
-- to, because it is the identity twenty-eight foreign keys hang off and no
-- legitimate operation moves it. The reasoning for choosing that over the narrow
-- repair is beside the trigger. The tombstone write is idempotent for the same
-- defect's second half: a registry keyed by tenant_id made a second erasure of a
-- returned id fail on the primary key, which turned a reversible erasure into an
-- erasure that could not be performed at all.
--
-- The erasure itself is untouched and stays untouched. Deletion on request is a
-- promise this schema has to keep, and a fix that made a tenant undeletable, or
-- that held its audit events back from the cascade, would be a worse defect than
-- the one it closes. The tombstone is written by the delete rather than instead of
-- it, and packages/core/db/schema.test.ts asks every run that the erasure still
-- succeeds and still takes the audit events with it.
--
-- Why the registry lives in seen, and why it holds two columns. Only the public
-- schema is exposed through the Data API (supabase/config.toml), and a list of
-- which brands have left belongs to no tenant and must not be readable by one, so
-- it sits beside seen.marketplace_catalogue rather than in public, where it would
-- also fail the tenancy rule it could not satisfy. It records that an id is spent
-- and when it was spent, and nothing else: no name, no user, no buyer data. A
-- registry that kept a name would be a retained record of the customer the erasure
-- was performed for, which is the thing that was asked to go, and part 7's
-- classification of every column that can hold prose reads schema public and would
-- not reach here to catch it. The two columns are read back by the test suite, so a
-- later migration cannot widen the tombstone into a customer record quietly.
--
-- What this guarantee is not, on the same boundary as part 2's and for the same
-- reason. A superuser, or the role that owns these objects, can disable or drop
-- the triggers, set session_replication_role to replica, or drop the registry
-- outright, and none of that is preventable in SQL. It is a guarantee against the
-- application and against a mistake, not against whoever holds the database.
-- Nothing is claimed about the WAL, a backup or a restore either: an id that comes
-- back in a dump taken before the erasure is outside anything a trigger can see,
-- and a restore drill is SEEN-082's.
--
-- Forward only, as parts 1 to 7: the local stack is reset rather than rolled back.

-- The registry -----------------------------------------------------------------

create table seen.erased_tenants (
  tenant_id uuid primary key,
  erased_at timestamptz not null default now()
);

comment on table seen.erased_tenants is
  'Tombstones for the tenant ids a deletion on request has consumed. One row per erasure, '
  'holding the id and the moment it was spent and nothing else, so it records that an erasure '
  'happened rather than retaining a record of the customer it was performed for. Outside public '
  'so it is outside the Data API and outside the tenancy rule it could not satisfy, because a '
  'list of erasures belongs to no tenant. Append-only itself: a tombstone that could be removed '
  'is a tenant id that could be created again a statement later.';

comment on column seen.erased_tenants.tenant_id is
  'The tenant id the erasure consumed, and which public.tenants will never accept again. No '
  'foreign key to public.tenants, because the row such a key would reference is exactly the row '
  'that is gone.';

comment on column seen.erased_tenants.erased_at is
  'When the erasure was performed. It is what makes an erasure legible as an event rather than '
  'as an absence, and it is the only other thing a tombstone is allowed to say.';

-- Row-level security with no policy at all, as on seen.marketplace_catalogue: the
-- table is reachable by nothing but its owner and the security definer functions
-- below, and a policy here would be a way in rather than a boundary.
alter table seen.erased_tenants enable row level security;

-- Nothing is granted to the three request-bound roles, and the revoke is written
-- out rather than left to the absence of a grant. Schema seen carries no entry in
-- pg_default_acl, so a table created here starts owner-only and this statement
-- takes nothing away today; what it does is put that state in the table's own
-- access control list, where the self-check below and schema.test.ts read it, so
-- `service_role holds nothing on the registry` is a measured fact rather than an
-- inference from a default that a later `alter default privileges` could change.
revoke all on seen.erased_tenants from anon, authenticated, service_role;

-- The tombstone is written by the erasure ---------------------------------------
--
-- Security definer, and that is the point rather than a convenience: the role that
-- performs the erasure is `service_role`, which holds nothing on the registry and
-- must go on holding nothing, because a role that could write a tombstone could
-- equally rewrite one. So the write is the owner's and the caller only causes it.
--
-- After delete rather than before, so what is recorded is an erasure that
-- happened.
--
-- The insert does nothing on conflict, and F27 is why it no longer raises. The
-- registry is keyed by tenant_id, so a plain insert makes a second erasure of an
-- id already tombstoned fail on the primary key, and the delete fails with it.
-- That turns the wrong thing loud: the assumption that has broken is that the id
-- came back, and the price of announcing it is paid by the tenant asking to be
-- deleted, who is refused. Deletion on request is owed within 30 days, and a
-- tenant it refuses for is worse off than one whose id was reusable.
--
-- With the refusals below in place no id should come back to be erased twice, so
-- this is defence in depth rather than a case anything is expected to reach. The
-- first tombstone is kept rather than overwritten: erased_at records when the id
-- was spent, and it was spent the first time.
create or replace function seen.record_tenant_erasure()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into seen.erased_tenants (tenant_id) values (old.tenant_id)
    on conflict (tenant_id) do nothing;
  return null;
end;
$$;

comment on function seen.record_tenant_erasure() is
  'Writes the tombstone for a tenant id as the tenant row is deleted, so that the erasure can '
  'later be told from no erasure having happened.';

create trigger record_erasure after delete on public.tenants
  for each row execute function seen.record_tenant_erasure();

-- And the id is refused ever after ----------------------------------------------
--
-- Security definer for the same reason and for a second one. The reason: the
-- registry is unreadable by every role the application uses, so an invoker-rights
-- function would be refused the table outright and the refusal would never fire.
-- The second: row-level security is enabled on the registry with no policy, so
-- under the invoker's rights this `exists` would answer what the caller can see
-- rather than what is there, and a caller who can see nothing would be told the id
-- is free. An existence test that is really a visibility test is the failure mode
-- worth naming here, because it fails open and it fails silently.
create or replace function seen.refuse_erased_tenant_id()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if exists (
    select 1 from seen.erased_tenants e where e.tenant_id = new.tenant_id
  ) then
    raise exception
      'tenant id % was erased on request and cannot be created again. A new tenant gets a new '
      'uuid; reusing an erased id would leave it resolving in every token, Stripe customer and '
      'invoice that names it with no audit events behind it, and the erasure would stop being '
      'distinguishable from no erasure at all.', new.tenant_id
      using errcode = 'restrict_violation';
  end if;

  return new;
end;
$$;

comment on function seen.refuse_erased_tenant_id() is
  'Refuses an insert into public.tenants carrying a tenant id a previous erasure consumed.';

create trigger refuse_erased_tenant_id before insert on public.tenants
  for each row execute function seen.refuse_erased_tenant_id();

-- And a tenant id is never changed at all ---------------------------------------
--
-- F27: the refusal above was a `before insert` trigger and nothing else, so an
-- update reached the state an insert could not. Measured as `service_role` in a
-- rolled-back transaction: erase a tenant, create a fresh one, clear the six
-- catalogue rows its insert seeds, and set the fresh tenant's id to the erased
-- one. Accepted. The id was back with no audit events behind it, which is the
-- whole of what the refusal above exists to prevent, reached one statement
-- further on. The child rows matter to the measurement and not to the defect:
-- while they stand their foreign keys refuse the update with 23503, which is
-- protection by accident rather than by design and vanishes the moment a tenant
-- has none.
--
-- The narrow repair is to fire the refusal above on update as well, so that an
-- update landing on a tombstoned id is refused like an insert. The rule here is
-- the stronger and simpler one: a tenant's id is its identity and is never
-- updatable, whatever it would be changed to. Twenty-eight tables carry a foreign
-- key to public.tenants, so an update of this column rewrites or orphans the
-- tenant scoping of every row beneath it, and nothing legitimate does that: the
-- schema, the migrations and the test suite update a tenant's name, status and
-- updated_at and never its id. The narrow repair was not enough because it leaves
-- the column writable and defends one destination: it has nothing to say about an
-- id handed to a tenant that was never erased, which is the same rewriting of
-- twenty-eight tables' tenancy with no tombstone involved, and it keeps the
-- erased-id case as a special case that a later reader has to keep in mind.
-- Under this rule the tombstone stops being a special case at all, because the
-- column the tombstone protects cannot move.
--
-- The condition is the trigger's rather than the function's body, so an ordinary
-- update of a tenant's name does not enter a function to be told it may proceed:
-- public.tenants already carries touch_updated_at on every update, and the rest of
-- the row stays ordinarily updatable, which is the point of naming the column here
-- rather than freezing the row. A fix that froze the whole tenant row would break
-- what the schema expects and would be a worse defect than the one it closes.
create or replace function seen.refuse_tenant_id_change()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception
    'a tenant id is not updatable: % cannot become %. It is the identity twenty-eight tables '
    'reference, so changing it would rewrite or orphan the tenant scoping of every row beneath '
    'it, and an id a previous erasure consumed would be back with no audit events behind it. A '
    'new tenant gets a new uuid.', old.tenant_id, new.tenant_id
    using errcode = 'restrict_violation';
end;
$$;

comment on function seen.refuse_tenant_id_change() is
  'Refuses any update of public.tenants.tenant_id, whatever the new value is, so that the id a '
  'tenant is known by cannot move and an erased id cannot be handed back to a living tenant.';

create trigger refuse_tenant_id_change before update on public.tenants
  for each row when (new.tenant_id is distinct from old.tenant_id)
  execute function seen.refuse_tenant_id_change();

-- No function here is callable except through its trigger and this migration, as
-- seen.seed_marketplaces is not: a security definer function reachable by name is
-- a privilege handed to whoever can name it.
revoke all on function seen.record_tenant_erasure() from public;
revoke all on function seen.refuse_erased_tenant_id() from public;
revoke all on function seen.refuse_tenant_id_change() from public;

-- The registry is append-only too -----------------------------------------------
--
-- Without this the refusal above is defeated in one statement: delete the
-- tombstone, then insert the tenant again. The three layers are the ones part 2
-- gave public.audit_events, with one difference that is worth stating. There is no
-- permitted delete here and no exception branch at all. audit_events has one
-- because a tenant's rows go when the tenant goes; a tombstone is the record that
-- the tenant went, so nothing cascades to it, nothing outlives it, and there is no
-- condition under which removing one is the right thing to do.
create or replace function seen.refuse_erasure_registry_mutation()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception
    'seen.erased_tenants is append-only: % is refused. A tombstone that can be removed is a '
    'tenant id that can be created again a statement later, and the erasure it records would '
    'stop being distinguishable from no erasure at all.', tg_op
    using errcode = 'restrict_violation';
end;
$$;

comment on function seen.refuse_erasure_registry_mutation() is
  'Refuses every update, delete and truncate on seen.erased_tenants, for every role including '
  'the one that owns the table.';

create trigger erased_tenants_append_only
  before update or delete on seen.erased_tenants
  for each row execute function seen.refuse_erasure_registry_mutation();

-- A row trigger never sees a truncate, and truncate would empty the registry in
-- one statement, so it is refused by a statement trigger as well.
create trigger erased_tenants_no_truncate
  before truncate on seen.erased_tenants
  for each statement execute function seen.refuse_erasure_registry_mutation();

-- What this migration claims, measured rather than asserted ---------------------
--
-- The same shape as the self-checks parts 4, 5 and 6 end with: the migration fails
-- rather than leaving a guarantee that reads true and is not. Both halves are
-- asked, because a fix that closed the reuse and broke the erasure would be worse
-- than the defect.
do $$
declare
  offenders text;
begin
  select string_agg(format('%s holds %s', a.grantee::regrole::text, a.privilege_type),
                    ', ' order by a.grantee::regrole::text, a.privilege_type)
    into offenders
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    cross join lateral aclexplode(c.relacl) a
   where n.nspname = 'seen' and c.relname = 'erased_tenants'
     and a.grantee in ('anon'::regrole, 'authenticated'::regrole, 'service_role'::regrole);

  if offenders is not null then
    raise exception 'a role the application uses holds a privilege on seen.erased_tenants, so '
      'the tombstone can be removed and the tenant id used again: %', offenders;
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
     where tgrelid = 'public.tenants'::regclass and not tgisinternal
       and tgname in ('record_erasure', 'refuse_erased_tenant_id', 'refuse_tenant_id_change')
     group by tgrelid having count(*) = 3
  ) then
    raise exception 'public.tenants does not carry all three of the trigger that writes a '
      'tombstone, the trigger that refuses a tombstoned id on insert and the trigger that '
      'refuses any change of tenant_id, so an erasure is still reversible by one route or the '
      'other';
  end if;

  if not has_table_privilege('service_role', 'public.tenants', 'delete') then
    raise exception 'the fix was over-broad: service_role can no longer erase a tenant, and '
      'deletion on request within 30 days is a promise this schema owes SEEN-083';
  end if;

  if not has_table_privilege('service_role', 'public.tenants', 'update') then
    raise exception 'the fix was over-broad in the other direction: service_role can no longer '
      'update a tenant at all, where what is refused is a change of tenant_id and not a rename';
  end if;
end;
$$;
