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
-- And the two sides cannot interleave. F28 found the refusal resting on a read,
-- and a read at read committed answers from a snapshot, which holds nothing an
-- uncommitted transaction has written. So one session could check the registry and
-- find it empty because the tombstone was still another session's, wait on the
-- primary key while that session finished erasing, and insert the id the moment the
-- key came free: live and tombstoned at once, from two ordinary statements in two
-- ordinary sessions. Both sides now take the same transaction-scoped advisory lock
-- on the id before they touch it, so the check cannot run inside the window the
-- erasure is open. What that costs and what it was chosen over is beside the lock.
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

-- The lock the erasure and the refusal share -------------------------------------
--
-- F28, and what it is for. The refusal below asks whether a tombstone exists, and
-- an existence test is a read of a snapshot. At read committed, which is Postgres's
-- default and what the API and the workers run at, that snapshot holds nothing an
-- uncommitted transaction has written. Measured against this stack on two
-- connections as `service_role`: session A deletes the tenant and does not commit,
-- session B inserts the same id, B's check finds no tombstone because A's is
-- invisible to it, B then waits on the primary key against the row A is deleting, A
-- commits, and B's insert succeeds. Neither session did anything unusual and
-- neither one was refused.
--
-- The mechanism. Both sides take a transaction-scoped advisory lock keyed on the id
-- before they do anything with it, through this one function so that the two can
-- never drift onto different keys, which would be a fix that reads correct and
-- locks nothing. The erasure takes it before the row goes and holds it to commit;
-- the refusal takes it before it reads the registry. A refusal that would have read
-- a stale snapshot therefore waits for the erasure to finish first, and the reason
-- waiting helps is that the check is a separate statement inside a volatile
-- function and so takes its own snapshot when it finally runs: it sees the tombstone
-- the wait was spent on rather than the absence it started with.
--
-- What it costs, because a lock that serialised every tenant write would be a real
-- price and should be a decision rather than an accident. The key is the id and not
-- the table, so two tenants being written at the same moment never wait on each
-- other. What serialises is an insert and an erasure of the same id, which is
-- exactly the pair that must not interleave, and a refusal that waits is one that
-- was going to refuse anyway. The second half of the key is a 32-bit digest, so two
-- unrelated ids can share it: the price of a collision is a wait between two writes
-- that had nothing to do with each other, never a wrong answer, because the registry
-- is still read by the id itself and not by the digest. The lock is transaction
-- scoped, so no path can leak one and a session that dies releases it by dying.
--
-- Why the erasure takes it before the delete rather than beside the tombstone. The
-- tombstone is written after the row has gone, and a lock taken there is taken after
-- the row is marked deleted: a second session that had already reached the primary
-- key would be waiting on the erasure's transaction while the erasure waited on that
-- session's advisory lock, and Postgres would break the cycle by refusing one of
-- them with 40P01. Taken before the row is touched, the two sides always queue in
-- the same order and only ever wait.
--
-- What was rejected. Asking the registry again in an `after insert` trigger costs no
-- lock at all and would close this interleaving, because by then the insert has
-- waited the erasure out; it was rejected because it is true only at read committed.
-- Under repeatable read the transaction has one snapshot for its whole life, the
-- second ask reads the same stale rows as the first, and the guarantee fails open
-- silently in an isolation level a later application might reasonably choose.
-- Making the registry authoritative through a constraint rather than a read was the
-- other candidate: a table of every id ever issued, referenced by public.tenants,
-- turns the check into a row lock the database takes without being asked. It was
-- rejected because that table holds the ids of living tenants rather than only spent
-- ones, which is a different table with a different meaning and a different privacy
-- story, and because marking a row erased is an update, so the registry would have
-- to stop being append-only to carry it. Raising the isolation level was not a
-- candidate at all: this schema cannot decide what its callers run at.
create or replace function seen.lock_tenant_id(id uuid)
returns void
language sql
set search_path = ''
as $$
  select pg_advisory_xact_lock(
    ('x' || substr(md5('seen.erased_tenants'), 1, 8))::bit(32)::int,
    ('x' || substr(md5(id::text), 1, 8))::bit(32)::int);
$$;

comment on function seen.lock_tenant_id(uuid) is
  'Takes the transaction-scoped advisory lock that an erasure and an insert of the same tenant id '
  'queue on, so that the registry is never read inside the window another session is erasing that '
  'id in. Keyed on the id, so writes of different tenants do not wait on each other.';

-- Security definer for the reason the two functions below are: the lock function is
-- revoked from public, and a call by name from inside a trigger running as
-- `service_role` would be refused where a call from the owner is not.
create or replace function seen.lock_tenant_id_for_erasure()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform seen.lock_tenant_id(old.tenant_id);
  return old;
end;
$$;

comment on function seen.lock_tenant_id_for_erasure() is
  'Takes the tenant id''s advisory lock before the tenant row is deleted, so that an insert of the '
  'same id cannot read the erasure registry while this erasure is uncommitted.';

create trigger lock_before_erasure before delete on public.tenants
  for each row execute function seen.lock_tenant_id_for_erasure();

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
--
-- And F28 is the same failure mode in time rather than in privilege: an existence
-- test is also a test of what has committed. The lock comes first for that reason
-- and is a statement of its own, because the check that follows it is what takes the
-- fresh snapshot the waiting was for.
create or replace function seen.refuse_erased_tenant_id()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform seen.lock_tenant_id(new.tenant_id);

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
--
-- Why `from public` is the whole of the revoke here, and would not be one line from
-- here in schema public. Measured this round against this stack: schema `seen`
-- carries no `pg_default_acl` entry at all, so a function created here is born with
-- the single grant PostgreSQL writes itself, EXECUTE to PUBLIC, and taking that
-- away leaves `{postgres=X/postgres}` and refuses `anon` with SQLSTATE 42501.
-- Schema public is not like that: its default access control list names `anon` and
-- `authenticated` on functions as well as on relations, so these five statements
-- written there would leave both roles holding EXECUTE, with the access control
-- list still reading `anon=X/postgres` and `anon` reading every tenant's rows
-- through a security definer body. That is the sixth review of SEEN-008 (F32), and
-- part 6 is where the default is taken away. So the sentence above is about the
-- functions this file creates in `seen` and is not the rule for writing one in a
-- schema the Data API serves.
revoke all on function seen.lock_tenant_id(uuid) from public;
revoke all on function seen.lock_tenant_id_for_erasure() from public;
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
  -- Asked as part 4 asks it, and for the same reason: what a role can do is not
  -- what the relation's own access control list says, and reading the list missed
  -- a grant to PUBLIC, a grant on one column and a privilege held through
  -- membership of another role (F30). A tombstone that one of these three roles
  -- can delete or rewrite is not a tombstone.
  --
  -- MAINTAIN is the one privilege the list used to report that this does not:
  -- it exists only from Postgres 17, so naming it would tie this migration to a
  -- server version, and it vacuums and analyses a table rather than removing a row
  -- from it.
  select string_agg(
           format('%s holds %s%s', held.role, held.privilege,
                  case when held.columns is null then ''
                       else format(' on column %s', held.columns) end),
           ', ' order by held.role, held.privilege)
    into offenders
    from (
      select h.role as role, a.privilege as privilege,
             has_table_privilege(h.role, 'seen.erased_tenants'::regclass, a.privilege)
               as on_the_relation,
             case when has_table_privilege(h.role, 'seen.erased_tenants'::regclass, a.privilege)
                  then null else (
               select string_agg(att.attname, ', ' order by att.attnum)
                 from pg_catalog.pg_attribute att
                where att.attrelid = 'seen.erased_tenants'::regclass
                  and att.attnum > 0 and not att.attisdropped
                  and a.privilege in ('SELECT', 'INSERT', 'UPDATE', 'REFERENCES')
                  and has_column_privilege(h.role, 'seen.erased_tenants'::regclass,
                                           att.attnum, a.privilege)
             ) end as columns
        from (values ('anon'), ('authenticated'), ('service_role')) as h(role)
        cross join (values ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE'),
                           ('REFERENCES'), ('TRIGGER')) as a(privilege)
    ) held
   where held.on_the_relation or held.columns is not null;

  if offenders is not null then
    raise exception 'a role the application uses holds a privilege on seen.erased_tenants, so '
      'the tombstone can be removed and the tenant id used again: %', offenders;
  end if;

  if not exists (
    select 1 from pg_catalog.pg_trigger
     where tgrelid = 'public.tenants'::regclass and not tgisinternal
       and tgname in ('lock_before_erasure', 'record_erasure', 'refuse_erased_tenant_id',
                      'refuse_tenant_id_change')
     group by tgrelid having count(*) = 4
  ) then
    raise exception 'public.tenants does not carry all four of the trigger that locks the id '
      'before an erasure, the trigger that writes a tombstone, the trigger that refuses a '
      'tombstoned id on insert and the trigger that refuses any change of tenant_id, so an '
      'erasure is still reversible by one route or another, or is still raceable by two '
      'sessions';
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
