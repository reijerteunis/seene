-- Trade record v1, part 2 of 8: findings, claims, evidence, correspondence and
-- the agent's own record. SEEN-008.
--
-- Part 1 created the tenancy, the policy helper seen.current_tenant() and the
-- order and settlement tables. These eleven are what the reconciliation engine
-- writes and what the agent is accountable for: a finding is what a detector saw,
-- a claim is what was asked of a marketplace, and an audit event is the record
-- that the asking happened, written before the side effect and never rewritten.
--
-- The same rules as part 1. Every table carries tenant_id, row-level security and
-- the one policy expression, created by the loop at the foot of this file rather
-- than written out eleven times. Amounts are integer cents in bigint with a
-- three-letter currency code beside them. Vocabularies arriving from a
-- marketplace, or owned by a later ticket, are text with their values in a column
-- comment rather than a constrained type: a value nobody anticipated must land in
-- the record and be reconciled, not rejected at ingest.
--
-- What is deliberately not here: the gate's behaviour. agent_actions and
-- approvals are the columns the policy gate (SEEN-033) and the approval inbox
-- (SEEN-035) will read and write, and nothing else. No trigger decides an
-- outcome, no default grants an autonomy, and no constraint encodes a cap.
--
-- Forward only, as part 1: the local stack is reset rather than rolled back.

-- Recover: findings, claims, evidence ---------------------------------------
-- claims is created before findings because a finding carries the claim it was
-- grouped into, which is the direction the ER diagram draws the relation.

create table public.claims (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  marketplace text not null,
  -- The claim rule that was applied: which entitlement is being asserted, from
  -- the templates in packages/core. The claims rail (SEEN-027) owns the list.
  rule text,
  -- api, assisted or track: whether the claim is filed through the marketplace's
  -- own API, handed to a person as a prepared case pack, or only followed. The ER
  -- prose names api and assisted; track is the third mode SEEN-027 adds.
  mode text,
  amount_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- The text that was submitted, as submitted. Drafted by the agent, possibly
  -- edited in the approval inbox, and kept verbatim because it is what a
  -- marketplace was actually told.
  claim_text text,
  -- The agent run or the person who submitted it. Text rather than a foreign key
  -- to two different tables; the audit event carries the full account.
  submitted_by text,
  submitted_at timestamptz,
  -- The marketplace's own case, dispute or ticket id, which is what the tracking
  -- and the deadline watch (SEEN-066) follow.
  external_case_id text,
  -- draft, submitted, accepted, refused, credited or expired. SEEN-027 owns the
  -- vocabulary; a claim's status is never set by anything but the rail.
  status text not null default 'draft',
  -- The settlement line that paid this claim, matched by SEEN-031. This column is
  -- the only thing that makes a claim billable: a credit is billable only as an
  -- ingested settlement line linked to a claim, so nothing here or in the console
  -- may write a billable event directly.
  credited_by_settlement_line_id uuid references public.settlement_lines (id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.claims is
  'What was asked of a marketplace, in the mode the capability routing allows. '
  'A claim becomes billable only through credited_by_settlement_line_id.';

create table public.findings (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- The three things a detector reads, one of which raised this finding. All
  -- nullable: a fee finding has a settlement line and no shipment, a lost
  -- shipment has a shipment and no settlement line.
  settlement_line_id uuid references public.settlement_lines (id) on delete cascade,
  shipment_id uuid references public.shipments (id) on delete cascade,
  return_id uuid references public.returns (id) on delete cascade,
  -- The claim this finding was grouped into, null until it is claimed. The ER
  -- diagram draws the relation as mandatory; it cannot be, because a finding
  -- exists from the moment a detector runs and most findings are never claimed.
  claim_id uuid references public.claims (id) on delete set null,
  -- What was found: the detector's own rule name, for example a commission
  -- charged above the schedule or a return never compensated. The detectors
  -- (SEEN-019, SEEN-020) own the vocabulary, so a new detector is a row here and
  -- not a migration.
  finding_type text not null,
  amount_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- Between 0 and 1. The detectors are deterministic, so this is the confidence
  -- of the match behind the finding, not of a model's opinion.
  confidence numeric(4, 3) check (confidence >= 0 and confidence <= 1),
  -- The rows and documents that evidence this finding, before a claim exists to
  -- hang evidence rows from.
  evidence_refs jsonb not null default '[]'::jsonb,
  -- The date by which the marketplace stops accepting a claim for this. Watched
  -- by SEEN-066; a finding past it is expired, not open.
  deadline_at timestamptz,
  -- open, claimed, credited, refused or expired, the five the architecture names.
  status text not null default 'open',
  detected_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.findings is
  'What a detector saw: one recoverable amount with its evidence and its deadline. '
  'Findings are produced by pure functions in packages/core and are never written by hand.';

create table public.claim_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  claim_id uuid not null references public.claims (id) on delete cascade,
  -- drafted, submitted, reminded, accepted, refused, credited: the history of one
  -- claim, so a refusal that was later credited can still be read in order.
  event_type text not null,
  detail jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.evidence (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  claim_id uuid not null references public.claims (id) on delete cascade,
  -- Where the storage provider holds the document: local Supabase Storage now,
  -- the EU project after the SEEN-007 go decision. The bytes are never in this
  -- database.
  storage_path text not null,
  -- Hashed on write, so a document produced months later is provably the one the
  -- claim was filed with.
  sha256 text,
  -- Which rail produced it: the marketplace API, a carrier, the tenant, or a
  -- report the agent assembled.
  source text,
  -- Buyer PII. A proof of delivery names the person it was delivered to, and a
  -- claim about a lost parcel cannot be made without it. Named here rather than
  -- buried in the document so SEEN-083 has a list to expire.
  buyer_name text,
  buyer_address text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on column public.evidence.buyer_name is
  'Buyer PII. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump.';
comment on column public.evidence.buyer_address is
  'Buyer PII. Written only as far as a claim needs it and expired after 30 days by SEEN-083. '
  'Encryption at rest is the storage layer only: the volume this database sits on, and the '
  'Supabase EU project once the SEEN-007 go decision is taken. The value itself is cleartext, '
  'so a pg_dump taken for a restore drill and any query as service_role read every tenant''s '
  'buyer data as typed. Nothing here encrypts the value itself, and no ticket owns doing so: '
  'column-level encryption is owed and unowned, a decision beyond SEEN-008 and one owed '
  'before SEEN-082 takes the first restore-drill dump.';

-- Serve: correspondence ------------------------------------------------------

create table public.message_threads (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- The connection the thread belongs to, null for a thread that arrived through
  -- the forwarded mailbox (SEEN-062) and cannot be attributed to one marketplace
  -- account. The ER diagram hangs threads off a connection, which is true of
  -- every thread read from a marketplace messaging API.
  connection_id uuid references public.connections (id) on delete cascade,
  -- marketplace or mail: which rail this thread is carried on, and therefore
  -- which one a reply goes back out through.
  channel text not null,
  -- The marketplace's own thread id, or the mail thread's Message-ID root. The
  -- upsert key for message ingest belongs to SEEN-061, so there is no unique
  -- index on it here.
  external_thread_id text,
  subject text,
  status text,
  last_message_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  thread_id uuid not null references public.message_threads (id) on delete cascade,
  external_message_id text,
  -- inbound or outbound.
  direction text not null,
  body text,
  -- agent or the person who wrote or edited it. Null on an inbound message,
  -- because nobody here drafted it.
  drafted_by text,
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- The policy gate and the agent's record -------------------------------------

create table public.policies (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- The action type the tools declare, which is the key the gate reads a policy
  -- by: one row per tenant and action type.
  action_type text not null,
  -- autonomous, approval or refuse. No default: a policy row that does not say
  -- what it permits should not exist, and the gate's own default for a missing
  -- row is SEEN-033's decision and not this migration's.
  mode text not null,
  -- The caps, in integer cents. The MVP's values (EUR 1,000 per claim, EUR 5,000
  -- filed per day) are a tenant's configuration and are seeded by the gate's
  -- ticket, not here.
  cap_per_action_cents bigint,
  cap_per_day_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- The price bands and the per-marketplace ceiling relative to the brand's own
  -- trailing price, keyed by marketplace. The governor (SEEN-072) owns the shape.
  price_bands jsonb not null default '{}'::jsonb,
  -- How long the governor waits before moving the same price again. Minutes
  -- because the architecture names a cooldown without a unit, and a column that
  -- states its unit is better than one that carries it in a comment elsewhere.
  cooldown_minutes integer,
  -- What the trust ramp (SEEN-065) has earned for this action type. Moved only by
  -- the ramp: autonomy is granted at a 95% approval rate over at least 50
  -- decisions and revoked on any refused execution.
  autonomy_score numeric(5, 4),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, action_type)
);

comment on table public.policies is
  'What the agent may do per action type, per tenant. Read by the policy gate before '
  'every action; refunds, purchase orders, account settings and delistings are never '
  'agent actions at all and so are never rows here.';

create table public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- What started the run: the queue and job that produced the task.
  trigger text,
  model text,
  input_tokens integer,
  output_tokens integer,
  -- The run's cost in integer cents, which is what the gross-margin check and the
  -- per-tenant cost in the ops console read.
  cost_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  duration_ms integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.approvals (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- Who decided, and when.
  decided_by text,
  decided_at timestamptz,
  -- approve, edit or reject, the three the approval inbox offers. What an edit
  -- changed is the action's own input and the audit event that records it, so
  -- there is no edited payload column here.
  decision text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.agent_actions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  agent_run_id uuid not null references public.agent_runs (id) on delete cascade,
  -- The approval that gated this action, null when the gate allowed it
  -- autonomously or refused it outright. The key is on this side because the ER
  -- diagram lets one approval gate more than one action.
  approval_id uuid references public.approvals (id) on delete set null,
  -- The tool that was called, from the fixed tool set. A name that is not in that
  -- set is not an action the runtime can take.
  tool text not null,
  -- The hash of the tool's input, so the same proposal is recognisable across a
  -- retry without storing the input twice.
  input_hash text,
  -- Whether this action can be undone: a dispute is reversible, a delisting is
  -- not. Declared by the tool, recorded here because the gate decided on it.
  reversible boolean,
  -- The action type the tool declared, which is the policies row the gate read.
  action_type text,
  -- The euro impact the tool's estimator returned, in integer cents.
  impact_cents bigint,
  currency text not null default 'EUR' check (char_length(currency) = 3),
  -- What the gate decided: autonomous, approval or refuse.
  decision text,
  -- What came back: accepted, refused, pending or credited.
  outcome text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.agent_actions is
  'One proposed or executed action of the agent. The gate writes the decision here and '
  'the audit event before the side effect; this table holds no behaviour of its own.';

create table public.audit_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants (tenant_id) on delete cascade,
  -- The action this event is about, null for an event that is not an agent action
  -- at all (an ingest run, a connection change). The ER diagram pairs one event
  -- with one action; the runtime writes at least two, the proposal and the
  -- outcome, so the relation is one action to many events.
  agent_action_id uuid references public.agent_actions (id) on delete cascade,
  event_type text not null,
  -- agent, the person who acted, or system.
  actor text,
  payload jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now(),
  -- No updated_at and no touch trigger: a row that is never updated has nothing
  -- to touch.
  created_at timestamptz not null default now()
);

-- The paths every module reads on: a tenant's open work, and a parent's children.
create index findings_tenant_status_idx on public.findings (tenant_id, status);
create index findings_deadline_at_idx on public.findings (deadline_at);
create index findings_settlement_line_id_idx on public.findings (settlement_line_id);
create index findings_claim_id_idx on public.findings (claim_id);
create index claims_tenant_status_idx on public.claims (tenant_id, status);
create index claims_credited_by_settlement_line_id_idx
  on public.claims (credited_by_settlement_line_id);
create index claim_events_claim_id_occurred_at_idx on public.claim_events (claim_id, occurred_at);
create index evidence_claim_id_idx on public.evidence (claim_id);
create index message_threads_tenant_last_message_at_idx
  on public.message_threads (tenant_id, last_message_at);
create index message_threads_external_thread_id_idx
  on public.message_threads (tenant_id, external_thread_id);
create index messages_thread_id_sent_at_idx on public.messages (thread_id, sent_at);
create index agent_runs_tenant_created_at_idx on public.agent_runs (tenant_id, created_at);
create index agent_actions_agent_run_id_idx on public.agent_actions (agent_run_id);
create index agent_actions_approval_id_idx on public.agent_actions (approval_id);
create index audit_events_tenant_occurred_at_idx on public.audit_events (tenant_id, occurred_at);
create index audit_events_agent_action_id_idx on public.audit_events (agent_action_id);

-- audit_events is append-only ------------------------------------------------
--
-- What the guarantee is. No role the application uses (anon, authenticated,
-- service_role) holds the update or delete privilege; no policy on the table
-- permits either command, so row-level security would refuse them even if a
-- privilege were granted by mistake later; and a trigger refuses both for every
-- role including the one that owns the table, which is the only way to say no to
-- the connection the workers and the migrations themselves run as.
--
-- The one delete that is allowed, deliberately. A tenant's erasure removes its
-- audit events with it: the PRD promises deletion on request within 30 days, and
-- an audit table that could never be deleted from would make that promise
-- impossible to keep. The trigger allows a delete exactly when the owning tenant
-- row is already gone, which inside Postgres is only true while the cascade from
-- public.tenants is running.
--
-- Why the function runs as its owner, which is the whole of the exception's
-- safety (SEEN-008, F23). `not exists (select ...)` under the invoker's rights is
-- not a question about what is there: it is a question about what the caller can
-- see, and public.tenants carries row-level security with one policy bound to
-- `authenticated`. A caller that policy does not name reads no tenant at all,
-- whatever claim it holds, so an invoker-rights branch would be open for every
-- tenant including the caller's own. That was true and harmless only by
-- coincidence, because the two roles holding delete on this table, service_role
-- and the owner, both bypass row-level security and an absent row and an
-- invisible one are the same answer to them; the next migration to grant delete
-- to a role a request is bound to would have turned the exception into permission
-- to erase the audit trail one event at a time. Security definer makes the branch
-- mean what this comment says it means. It is the failure mode part 8 names on
-- its own registry, and it is worth naming twice: an existence test that is really
-- a visibility test fails open and fails silently.
--
-- What that exception did not cover, and what part 8 of this set does. Removing
-- the rows is only half of an erasure: nothing here stops the tenant being created
-- again under the same id, and an id that resolves with no audit events behind it
-- makes an erasure and an absence of one the same observation. Part 8 records the
-- id an erasure consumed and refuses it on every later insert, so this branch stays
-- the one delete it says it is.
--
-- What the guarantee is not. A superuser can disable the trigger, set
-- session_replication_role to replica, drop the table or alter it, and none of
-- that is preventable in SQL. Nor does this say anything about the WAL, a backup
-- or a restore. It is a guarantee against the application and against a mistake,
-- not against whoever holds the database. Tamper evidence beyond this needs
-- something outside Postgres, and no ticket has asked for it.

create or replace function seen.refuse_audit_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'DELETE'
     and not exists (
       select 1 from public.tenants t where t.tenant_id = old.tenant_id
     ) then
    -- The tenant row is gone rather than merely out of the caller's sight, so this
    -- is the erasure cascade and not an attempt to remove one event. Let it
    -- through. The owner's rights buy this one read and nothing else: the function
    -- writes nothing, takes no argument, builds no statement from a value, and
    -- names every object it touches with its schema under an empty search_path.
    return old;
  end if;

  raise exception
    'public.audit_events is append-only: % is refused. An audit event is written before the '
    'side effect it records and is never rewritten; the only delete permitted is the erasure '
    'of its tenant.', tg_op
    using errcode = 'restrict_violation';
end;
$$;

comment on function seen.refuse_audit_mutation() is
  'Refuses every update and delete on public.audit_events except the delete that the '
  'cascade from public.tenants performs when a tenant is erased. Security definer, so that '
  'the test for the tenant row asks whether it exists rather than whether the caller may '
  'see it.';

-- Not callable by name, as part 8's two security definer functions are not: a
-- function that runs as the owner and can be reached by whoever can name it is a
-- privilege handed out. A trigger function cannot be called directly anyway, and
-- the privilege a trigger needs is checked when the trigger is created rather than
-- each time it fires, so this takes nothing away from the two below.
revoke all on function seen.refuse_audit_mutation() from public;

create trigger audit_events_append_only
  before update or delete on public.audit_events
  for each row execute function seen.refuse_audit_mutation();

-- A row trigger never sees a truncate, and truncate would empty the table in one
-- statement, so it is refused by a statement trigger as well.
create trigger audit_events_no_truncate
  before truncate on public.audit_events
  for each statement execute function seen.refuse_audit_mutation();

-- Tenancy on every table -----------------------------------------------------
-- The same loop as part 1, over this migration's eleven tables: one policy
-- expression and one updated_at trigger, written once. A table without tenant_id
-- fails the migration here rather than being left open.
--
-- audit_events is the one branch: it takes a select policy and an insert policy
-- instead of one policy for all commands, so that no policy on it permits an
-- update or a delete, and it takes no updated_at trigger because it has no
-- updated_at.

do $$
declare
  target text;
begin
  foreach target in array array[
    'claims', 'findings', 'claim_events', 'evidence', 'message_threads', 'messages',
    'policies', 'agent_runs', 'approvals', 'agent_actions', 'audit_events'
  ]
  loop
    if not exists (
      select 1 from pg_catalog.pg_attribute a
       where a.attrelid = format('public.%I', target)::regclass
         and a.attname = 'tenant_id' and a.attnum > 0 and not a.attisdropped
    ) then
      raise exception 'public.% has no tenant_id column, so it cannot carry the tenancy policy',
        target;
    end if;

    execute format('alter table public.%I enable row level security', target);

    if target = 'audit_events' then
      execute $a$
        create policy tenant_isolation on public.audit_events
          for select to authenticated
          using (tenant_id = seen.current_tenant())
      $a$;
      execute $a$
        create policy tenant_append on public.audit_events
          for insert to authenticated
          with check (tenant_id = seen.current_tenant())
      $a$;
    else
      execute format($p$
        create policy tenant_isolation on public.%I
          for all to authenticated
          using (tenant_id = seen.current_tenant())
          with check (tenant_id = seen.current_tenant())
      $p$, target);
      execute format($t$
        create trigger touch_updated_at before update on public.%I
          for each row execute function seen.touch_updated_at()
      $t$, target);
    end if;
  end loop;
end;
$$;

-- As part 1: no table privilege is granted here, because part 4 grants per table by
-- name and a grant on the whole schema would reach every table parts 1 and 3 own
-- as well.
--
-- audit_events gives back what no migration granted it in the first place.
-- Supabase's default privileges for schema public hand insert, update, delete and
-- truncate to anon, authenticated and service_role at the moment a table is
-- created, so this table was rewritable before this line and no statement in this
-- file is what made it so. Truncate goes with the other two: a truncated audit
-- trail is an erased one. Part 4 revokes the same three per table again, so the
-- guarantee does not rest on the tail of an earlier migration that a later author
-- can delete without seeing what it was for.
revoke update, delete, truncate on public.audit_events from anon, authenticated, service_role;
