-- Trade record v1, part 10 of 10: the bytes an erasure could not reach, the path
-- a row could name that was not its own, the last hop of the billable chain, and
-- one seeded capability that said the opposite of the routing table. SEEN-008,
-- F63, F64, F66 and F58.
--
-- What the parts before this one settled, and the place all of it stopped.
-- Every table in public carries tenant_id, row-level security and one policy
-- expression; part 5 rewrote every foreign key as (tenant_id, child) references
-- parent (tenant_id, id) so a row cannot reach another tenant's row through a key;
-- part 8 made an erased tenant id unusable ever after. None of that reaches the
-- storage bucket, and two of the findings below are the same sentence read twice:
-- public.evidence.storage_path was free text with no relation to
-- public.evidence.tenant_id, and it was also the only thing in this database that
-- said which stored object belonged to which tenant.
--
-- So a row inside tenant A's boundary could address tenant B's buyer invoice
-- (F64, measured: the insert was accepted, while the same crossing attempted
-- through claim_id was refused with 23503 by part 5's key), and a deletion on
-- request deleted that column along with everything else and left the objects
-- standing with nothing able to say whose they were (F63, measured: evidence 2
-- rows and 2 objects before, 0 rows and the same 2 objects after, with the id
-- tombstoned in seen.erased_tenants and no row anywhere associating the two).
--
-- The order the two are fixed in is the argument. Constraining the path to begin
-- with the row's own tenant id closes F64 with the technique this schema already
-- uses for keys, and it is also what makes F63 closable at all: an erasure can
-- then find a tenant's objects by their names, which is the one thing about them
-- that survives the rows being deleted.
--
-- Forward only, as every part before it: the local stack is reset rather than
-- rolled back.

-- F64: a path is its own tenant's ------------------------------------------------
--
-- The check compares two columns of the same row, which is what a check
-- constraint can do and a policy cannot: a policy decides which rows a request
-- sees and says nothing about whether the value in one of them addresses another
-- tenant's object. Written as a prefix test rather than as a trigger, so it is
-- enforced on every insert and update by the database with nothing on the writing
-- side having to remember, and so a constraint violation names the column a
-- reader would look for.
--
-- Why LIKE and not a function. The pattern is built from the row's own
-- tenant_id::text, and the text of a uuid is hexadecimal digits and hyphens, so
-- it carries neither of LIKE's wildcards and cannot be read as a pattern by
-- accident. starts_with() would say the same thing and would tie the constraint
-- to a Postgres version this repository has no reason to require.
--
-- What it does not claim. It binds what a row may name, not where the storage
-- provider was told to put the bytes. Those are the same thing in practice
-- because the row is how anything in this system addresses an object, and the
-- erasure below sweeps by the same prefix, so an object written outside its
-- tenant's prefix is one no row may point at and no erasure will find. That is
-- SEEN-022's to respect when it assembles the audit PDF and the evidence store,
-- and it is not owed a criterion, because a path it cannot store is not a promise
-- it has to remember to keep.

alter table public.evidence
  add constraint evidence_storage_path_is_its_own_tenants
  check (storage_path like tenant_id::text || '/%');

comment on constraint evidence_storage_path_is_its_own_tenants on public.evidence is
  'An evidence row may only address a stored object under its own tenant''s prefix. The tenancy '
  'policy protects the row; without this the row could name another tenant''s buyer document and '
  'the application would resolve it to a signed URL. F64.';

-- statements.storage_path is the same column in a different table and was not in
-- the finding, which named only the evidence one. It is included because the
-- convention the erasure rests on has to be true of every column that addresses an
-- object, not of the one that was measured: a rendered statement left outside its
-- tenant's prefix is a document the sweep below walks past. Nullable, because a
-- period that was reported and not rendered has no document at all, and a
-- constraint that refused that would break a row this schema means to allow.
alter table public.statements
  add constraint statements_storage_path_is_its_own_tenants
  check (storage_path is null or storage_path like tenant_id::text || '/%');

comment on constraint statements_storage_path_is_its_own_tenants on public.statements is
  'A statement may only address a rendered document under its own tenant''s prefix, and a period '
  'that was reported and not rendered carries no path at all. F64, widened from the evidence '
  'column the finding measured to every column that addresses a stored object.';

-- F63: what an erasure leaves for the bytes --------------------------------------
--
-- The thing this fix cannot be. A database cannot delete an object: storage.objects
-- is a row about a file and removing the row orphans the file rather than deleting
-- it, so a trigger that tidied up storage.objects would turn a recoverable defect
-- into an unrecoverable one and would read, from inside this schema, exactly like a
-- fix. Only the storage provider deletes bytes, and nothing in Postgres can call it.
--
-- So the whole of what this schema can carry is the mapping, kept where the cascade
-- cannot reach it. The erasure writes one row per stored object the tenant left
-- behind, the objects themselves are untouched, and SEEN-083, which owns deletion on
-- request, empties the worklist by deleting each object through the storage API and
-- removing the row. That obligation is on the table's own comment and in SEEN-083's
-- acceptance criteria, which is where F34 established such a promise has to live: a
-- promise its promiser never hears is not one.
--
-- Why the sweep reads storage.objects and not public.evidence. The evidence rows are
-- being deleted by the same statement, and a worklist built from them would hold
-- only the objects this database happens to know about: an upload whose row was never
-- written, or was written and then rolled back, is bytes in a bucket with no row at
-- all, and it is precisely the case an erasure must not walk past. Reading the bucket
-- reaches both, and it reaches every bucket a later ticket adds without this trigger
-- being edited, because what it matches on is the prefix the constraints above make
-- true rather than a list of bucket names.
--
-- Why the registry lives in seen, and what it is allowed to say. The same two reasons
-- as seen.erased_tenants beside it. Only public is served by the Data API
-- (supabase/config.toml), and a list of what a departed brand left in a bucket
-- belongs to no tenant and must not be readable by one; and a table in public without
-- tenant_id would fail criterion 2's test, rightly. It holds the bucket, the object's
-- name, the id the erasure consumed and when it was recorded, and nothing else: no
-- name, no user, no buyer data. The tenant id is not a new retention, because
-- seen.erased_tenants already holds exactly that id and the object's own name begins
-- with it; without it an entry could not be attributed to the erasure that owes it.
--
-- What is deliberately not here: a way for anything to read the worklist. Nothing is
-- granted to anon, authenticated or service_role, exactly as on the tombstone
-- registry, so the table is reachable by its owner and the security definer function
-- below and by nothing else. SEEN-083 will need a reader, and whether that is a grant
-- to the role its worker runs as or a security definer function of its own depends on
-- where the sweep runs, which this ticket does not know and should not guess.

create table seen.pending_object_erasures (
  bucket_id text not null,
  object_name text not null,
  tenant_id uuid not null,
  recorded_at timestamptz not null default now(),
  primary key (bucket_id, object_name)
);

comment on table seen.pending_object_erasures is
  'The stored objects a deletion on request left behind, one row per object, written by the '
  'erasure as the tenant row is deleted. It exists because a database cannot delete bytes: '
  'removing a row of storage.objects orphans the file rather than deleting it, and only the '
  'storage provider can carry out the deletion the PRD promises within 30 days. So this is the '
  'mapping surviving the cascade that destroys every other trace of it, and it is worth nothing '
  'on its own: it falls to SEEN-083, which owns deletion on request, to keep it so, by deleting '
  'each object from its bucket through the storage API and removing the row it was named in. A '
  'worklist that is never emptied is a list of what was not deleted. F63.';

comment on column seen.pending_object_erasures.bucket_id is
  'The bucket the object is in, so the sweep needs no convention about which bucket an erased '
  'tenant wrote to and a bucket a later ticket adds is covered without this table changing.';

comment on column seen.pending_object_erasures.object_name is
  'The object''s own name in that bucket, which is the only thing about it that survives the '
  'rows being deleted, and the only thing the storage API needs to delete it.';

comment on column seen.pending_object_erasures.tenant_id is
  'The tenant id the erasure consumed. Not a new retention: seen.erased_tenants holds the same '
  'id beside this table and the object''s own name begins with it, and without it an entry '
  'cannot be attributed to the erasure that owes it.';

comment on column seen.pending_object_erasures.recorded_at is
  'When the erasure recorded the object, so the 30 days SEEN-083 has to act within are counted '
  'from a moment in this database rather than from a job''s memory of one.';

-- Row-level security with no policy at all, as on seen.erased_tenants and
-- seen.marketplace_catalogue: the table is reachable by nothing but its owner and
-- the security definer function below, and a policy here would be a way in rather
-- than a boundary.
alter table seen.pending_object_erasures enable row level security;

-- Written out rather than left to the absence of a grant, for the reason part 8
-- writes it out: it puts the state in the table's own access control list, where
-- schema.test.ts reads it, so `no request-bound role holds anything on the
-- worklist` is a measured fact rather than an inference from a default.
revoke all on seen.pending_object_erasures from anon, authenticated, service_role;

-- Security definer, and that is the point rather than a convenience, exactly as it
-- is for seen.record_tenant_erasure() beside it: the role that performs the erasure
-- is service_role, which holds nothing on this table and must go on holding nothing,
-- because a role that could write an entry could equally remove one. So the write is
-- the owner's and the caller only causes it. It also needs the owner's rights to read
-- storage.objects at all, which service_role is not guaranteed to hold.
--
-- After delete, so what is recorded is an erasure that happened, and so the entries
-- are written by the same statement that removes the rows they replace.
--
-- Nothing on conflict, for part 8's reason one table along: a primary key collision
-- here would fail the delete, and the price of announcing a surprise would be paid by
-- the tenant asking to be deleted, who would be refused. An object can only collide
-- with itself, so the first entry is the right one either way.
create or replace function seen.record_tenant_object_erasures()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into seen.pending_object_erasures (bucket_id, object_name, tenant_id)
  select o.bucket_id, o.name, old.tenant_id
    from storage.objects o
   where o.bucket_id is not null
     and o.name is not null
     and o.name like old.tenant_id::text || '/%'
  on conflict (bucket_id, object_name) do nothing;
  return null;
end;
$$;

comment on function seen.record_tenant_object_erasures() is
  'Records every stored object under the erased tenant''s prefix as the tenant row is deleted, '
  'so the bytes can still be reached after the rows that named them are gone.';

create trigger record_object_erasures after delete on public.tenants
  for each row execute function seen.record_tenant_object_erasures();

-- Part 6 revokes execute from public by default on a routine created here, and part
-- 8 writes the revoke out beside its own functions regardless, because what is being
-- relied on otherwise is a default privilege entry a later ticket could change.
revoke all on function seen.record_tenant_object_erasures() from public;

-- F66: the last hop of the billable chain ----------------------------------------
--
-- The rule, in CLAUDE.md's words: a credit is billable only as an ingested settlement
-- line linked to a claim, and never let a person or the agent create a billable event
-- directly. The architecture's seventh principle says the meter and the ledger are
-- the same table. This schema builds the chain carefully up to the second-last link,
-- and claims.credited_by_settlement_line_id is a real tenant-scoped key to an
-- ingested line. Then it stopped at a jsonb array defaulting to '[]', with no key, no
-- check and no counterpart on the claim, whose own comment stated the contract the
-- database did not enforce. Measured: two inserts accepted, EUR 124,000 of recovery
-- share billed at status 'open' against one claim still at status 'draft' with a null
-- credit link, one line of which cited a claim id present in no table at all.
--
-- What is not done here, and why. The typed relation is SEEN-040's, by that ticket's
-- own text rather than by this one's preference: its description names an
-- invoice_claims link table and its second acceptance criterion already requires a
-- unique constraint on invoice_claims.claim_id. Building that table one sprint early
-- would be this schema guessing the shape of a thing its owner has already described,
-- and part 3 declined it for a version of the same reason.
--
-- What is done here is the half that is this ticket's. Part 3's reasoning for the
-- jsonb column was that the relation stays readable either way and SEEN-040 may
-- normalise it; the defect is that both remain available afterwards, and of two
-- representations of one relation the unenforced one is the one somebody writes.
-- A column that cannot carry the rule, shipped with a default that makes writing to
-- it the path of least resistance, is this schema handing a later ticket a way around
-- its own ground rule. So it is removed rather than left beside what replaces it, and
-- the obligation moves to the table's comment and into SEEN-040's criteria.
--
-- module_lines stays. A module subscription is a price for a period, no rule makes it
-- a metered event, and SEEN-045 owns the switches it is billed from.

alter table public.invoices drop column recovery_share_lines;

comment on table public.invoices is
  'What the tenant was charged, mirrored from Stripe. Nothing here holds the recovery share '
  'lines: they are the typed relation SEEN-040 builds, one row per credited claim, and it falls '
  'to SEEN-040 to keep it so. Each such row names a claim whose credited_by_settlement_line_id '
  'is set, which is the whole of what makes a credit billable, and a claim may appear on one '
  'invoice only. The untyped column this table used to carry was dropped rather than left beside '
  'the typed relation, because of two representations of one relation the unenforced one is the '
  'one that gets written, and it accepted a recovery share against a claim that was never '
  'credited and against a claim id present in no table. F66.';

-- F58: Bol correspondence is assisted, not out of scope ---------------------------
--
-- The seeded cell read {"mode": "none", "detail": "by API (assisted via inbox)"}, and
-- the detail is the tell: the routing table's cell is `none by API (assisted via
-- inbox)`, and the parser's longest-prefix rule took `none` off the front of it and
-- kept the second half of a negation as though it were a detail. A module reading
-- capabilities->'buyer_messages'->>'mode' for bol was told the capability is out of
-- scope for the MVP, which is what the routing table's legend defines `none` to mean
-- and what packages/core/db/marketplaces.ts repeats in its own words.
--
-- Which of the two is wrong was established before either was touched, because the
-- criterion compares them and a fix applied to the wrong side would pass. The
-- document is right: its own consequence sentence says Bol is the only marketplace
-- with no messaging API, so its correspondence runs through the tenant's forwarded
-- mailbox; the PRD ships it as Serve, at FR-28 for the Postmark inbound mailbox with
-- thread matching by order id and FR-29 for the drafted replies; and SEEN-062 and
-- SEEN-063 build it in Sprint 5. The cell says assisted in English and the seed says
-- the opposite, so the seed is what moves.
--
-- The repository's own comparison could not catch this, and that is the part worth
-- keeping. marketplaces.test.ts parses the document at test time and compares it
-- cell by cell with these rows, with the parser that produced them, so both sides
-- shared the reading and agreed. The parser now refuses a cell whose text after the
-- mode continues into another mode, rather than reading the first and keeping the
-- rest, and this cell is named in the map it already keeps for the cells no rule
-- reaches. The mode stored is the answer a module routes on; the detail stays the
-- cell's own words, as it does for the other cell in that map.

update seen.marketplace_catalogue
   set capabilities = jsonb_set(
         capabilities, '{buyer_messages}',
         '{"mode": "assisted", "detail": "none by API (assisted via inbox)"}'::jsonb)
 where marketplace = 'bol';

-- And the tenants that already hold a copy, because the catalogue is copied into
-- public.marketplaces per tenant and a source corrected without its copies is a
-- correction no module reads. On a fresh `pnpm db:reset` this loop finds none, which
-- is why the source above is corrected rather than the copies.
do $$
declare
  existing uuid;
begin
  for existing in select tenant_id from public.tenants loop
    perform seen.seed_marketplaces(existing);
  end loop;
end;
$$;

-- And the migration checks its own outcome, as part 5 does: the statements above are
-- what a person wrote, and what makes them right is that the database now answers
-- differently. Raised rather than asserted elsewhere, so a reset that silently did
-- not apply one of them fails here rather than one test run later.
do $$
declare
  stored text;
begin
  select capabilities->'buyer_messages'->>'mode'
    into stored
    from seen.marketplace_catalogue
   where marketplace = 'bol';
  if stored is distinct from 'assisted' then
    raise exception
      'Bol correspondence is seeded as %, where the routing table routes it as assisted through '
      'the forwarded inbox and the PRD ships it as Serve. The claims and correspondence rails '
      'route on this value.', coalesce(stored, 'nothing at all');
  end if;
end;
$$;
