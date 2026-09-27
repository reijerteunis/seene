/**
 * Criterion 2: every table in the public schema carries `tenant_id` and an
 * enabled row-level security policy.
 *
 * Asserted from `pg_catalog` and not from a hand-written list of table names, so
 * a table added by a later migration without tenancy fails here without anyone
 * remembering to extend this test. The list in `tables.ts` is read the other way
 * round, to prove the migration created what it said it would.
 *
 * Two properties of the schema that are not criterion 2 but are decided by the
 * same migrations live here too, because they are facts about the schema and
 * nothing else would assert them: the buyer PII columns SEEN-083 has to expire
 * say so in their own comments, and `audit_events` is append-only.
 */
import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import {
  APPEND_ONLY_TABLES, BUYER_PII_COLUMNS, TENANT_CLAIM, TRADE_RECORD_TABLES,
} from './tables';

// The local Supabase stack's Postgres, the address `pnpm dev:up` prints when it
// starts. Overridden by SEEN_DATABASE_URL so CI or a second stack needs no code
// change; the default is the local development credential the CLI fixes for
// every project and is the only connection string this repository ever spells.
const LOCAL_DEFAULT = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres';
const DATABASE_URL = process.env.SEEN_DATABASE_URL ?? LOCAL_DEFAULT;

/** Host, port and database only: a connection string carries a password, and a
 * test's own failure text is read again in a journal record and in a CI log. */
function where(url: string): string {
  try {
    const parsed = new URL(url);
    return `${parsed.hostname}:${parsed.port || '5432'}${parsed.pathname}`;
  } catch {
    return 'the database SEEN_DATABASE_URL names';
  }
}

/** A connection, or a refusal that says the database is unreachable and that
 * this test therefore proves nothing about the schema. The two failures have to
 * read differently: a red that fails because Docker is down is not a red. */
async function connect(): Promise<Client> {
  const client = new Client({ connectionString: DATABASE_URL });
  try {
    await client.connect();
  } catch (cause) {
    await client.end().catch(() => undefined);
    throw new Error(
      `No Postgres answering at ${where(DATABASE_URL)}, so this test proves nothing about the `
      + 'schema. Start the local stack with `pnpm dev:up`, apply the migrations with '
      + '`pnpm db:reset`, or point SEEN_DATABASE_URL at another stack. The driver said: '
      + `${(cause as Error).message}`,
      { cause },
    );
  }
  return client;
}

async function tableNames(client: Client): Promise<string[]> {
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relkind = 'r'
      order by c.relname`,
  );
  return rows.map((row) => row.name);
}

describe('the trade record schema', () => {
  let client: Client;
  let present: string[];

  beforeAll(async () => {
    client = await connect();
    present = await tableNames(client);
  });

  afterAll(async () => {
    await client?.end();
  });

  it('created every table the trade record names', () => {
    const missing = TRADE_RECORD_TABLES.filter((table) => !present.includes(table));
    expect(
      missing,
      `The public schema is missing ${missing.length} of the ${TRADE_RECORD_TABLES.length} `
      + `tables the trade record names: ${missing.join(', ')}`,
    ).toEqual([]);
  });

  it('carries tenant_id on every table in the public schema', async () => {
    const { rows } = await client.query<{ name: string }>(
      `select c.relname as name
         from pg_catalog.pg_class c
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = 'r'
          and not exists (
            select 1 from pg_catalog.pg_attribute a
             where a.attrelid = c.oid and a.attname = 'tenant_id'
               and a.attnum > 0 and not a.attisdropped)
        order by c.relname`,
    );
    const without = rows.map((row) => row.name);
    expect(present.length, 'The public schema has no tables at all').toBeGreaterThan(0);
    expect(without, `Tables in the public schema without a tenant_id column: ${without.join(', ')}`)
      .toEqual([]);
  });

  it('has row-level security enabled on every table in the public schema', async () => {
    const { rows } = await client.query<{ name: string }>(
      `select c.relname as name
         from pg_catalog.pg_class c
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity
        order by c.relname`,
    );
    const without = rows.map((row) => row.name);
    expect(without, `Tables in the public schema without RLS enabled: ${without.join(', ')}`)
      .toEqual([]);
  });

  it('binds every table to the one tenancy expression', async () => {
    // One helper, `seen.current_tenant()`, rather than the expression copied per
    // table: a policy that spells its own comparison is a policy that can be
    // subtly different from the other twenty-eight.
    const { rows } = await client.query<{ tablename: string; qual: string | null }>(
      `select tablename, qual from pg_catalog.pg_policies where schemaname = 'public'`,
    );
    const bound = new Set(
      rows.filter((row) => (row.qual ?? '').includes('current_tenant')).map((row) => row.tablename),
    );
    const unbound = present.filter((table) => !bound.has(table));
    expect(
      unbound,
      'Tables in the public schema with no policy reading seen.current_tenant(): '
      + unbound.join(', '),
    ).toEqual([]);
  });

  it('reads the tenant from the claim the helper documents', async () => {
    // The claim name is this ticket's decision and nothing else in the repository
    // records it, so the helper's own definition is asserted against the constant
    // the web application will read when it mints the token.
    const { rows } = await client.query<{ definition: string }>(
      `select pg_catalog.pg_get_functiondef(p.oid) as definition
         from pg_catalog.pg_proc p
         join pg_catalog.pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'seen' and p.proname = 'current_tenant'`,
    );
    expect(rows, 'seen.current_tenant() does not exist').toHaveLength(1);
    expect(rows[0].definition).toContain(`'${TENANT_CLAIM}'`);
    expect(rows[0].definition).toContain('request.jwt.claims');
  });

  it('names every buyer PII column as PII with the 30-day expiry it owes', async () => {
    // Read from the catalogue in both directions: the columns `tables.ts` lists
    // exist and say what they are, and no column named for the buyer exists that
    // the list does not carry. SEEN-083 has to expire this data after 30 days and
    // should find a list, not do a search.
    const { rows } = await client.query<{ column: string; comment: string | null }>(
      `select c.relname || '.' || a.attname as column,
              pg_catalog.col_description(c.oid, a.attnum) as comment
         from pg_catalog.pg_class c
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
         join pg_catalog.pg_attribute a on a.attrelid = c.oid
        where n.nspname = 'public' and c.relkind = 'r'
          and a.attnum > 0 and not a.attisdropped and a.attname like 'buyer%'
        order by 1`,
    );
    const found = rows.map((row) => row.column);
    const missing = BUYER_PII_COLUMNS.filter((column) => !found.includes(column));
    const unlisted = found.filter(
      (column) => !(BUYER_PII_COLUMNS as readonly string[]).includes(column),
    );
    expect(missing, `Buyer PII columns the schema does not have: ${missing.join(', ')}`).toEqual([]);
    expect(
      unlisted,
      'Columns named for the buyer that BUYER_PII_COLUMNS does not list, so SEEN-083 would not '
      + `expire them: ${unlisted.join(', ')}`,
    ).toEqual([]);

    const silent = rows
      .filter((row) => !(row.comment ?? '').includes('PII') || !(row.comment ?? '').includes('30 days'))
      .map((row) => row.column);
    expect(
      silent,
      'Buyer PII columns whose own comment does not say they are PII expiring after 30 days: '
      + silent.join(', '),
    ).toEqual([]);
  });
});

describe('the append-only guarantee on audit_events', () => {
  // What append-only means here, and what it does not. No application role holds
  // the update or delete privilege, no policy permits either command, and a
  // trigger refuses both for every role including the one that owns the table.
  // The single delete the guarantee allows is a tenant's erasure: the audit rows
  // go when the tenant goes, because the PRD promises deletion on request.
  let client: Client;
  let tenant: string | undefined;
  let event: string | undefined;

  beforeAll(async () => {
    client = await connect();
    const present = await tableNames(client);
    const missing = APPEND_ONLY_TABLES.filter((table) => !present.includes(table));
    if (missing.length > 0) {
      throw new Error(
        `This test cannot say anything about the append-only guarantee: ${missing.join(', ')} `
        + `${missing.length === 1 ? 'does' : 'do'} not exist in the public schema. The findings, `
        + 'claims and agent migration has not been applied, so there is nothing to refuse an '
        + 'update to. Apply it with `pnpm db:reset`.',
      );
    }
    const seeded = await client.query<{ tenant_id: string }>(
      "insert into public.tenants (name) values ('Tenant append-only') returning tenant_id",
    );
    tenant = seeded.rows[0].tenant_id;
    const written = await client.query<{ id: string }>(
      `insert into public.audit_events (tenant_id, event_type, actor)
       values ($1, 'test.written_first', 'test') returning id`,
      [tenant],
    );
    event = written.rows[0].id;
  });

  afterAll(async () => {
    if (tenant) {
      await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
    }
    await client?.end();
  });

  it('refuses an update of an audit event, to the owner of the table as well', async () => {
    // The connection is the owner role, which bypasses row-level security and
    // holds every privilege the table grants: if the update is refused here it is
    // refused for everyone SQL can bind.
    await expect(
      client.query("update public.audit_events set actor = 'rewritten' where id = $1", [event]),
    ).rejects.toThrow(/append-only/);
  });

  it('refuses a delete of an audit event, to the owner of the table as well', async () => {
    await expect(
      client.query('delete from public.audit_events where id = $1', [event]),
    ).rejects.toThrow(/append-only/);
  });

  it('grants no update or delete privilege to any role the application uses', async () => {
    const { rows } = await client.query<{
      role: string; may_update: boolean; may_delete: boolean;
      may_select: boolean; may_insert: boolean;
    }>(
      `select role,
              has_table_privilege(role, 'public.audit_events', 'update') as may_update,
              has_table_privilege(role, 'public.audit_events', 'delete') as may_delete,
              has_table_privilege(role, 'public.audit_events', 'select') as may_select,
              has_table_privilege(role, 'public.audit_events', 'insert') as may_insert
         from unnest(array['anon', 'authenticated', 'service_role']) as role`,
    );
    const writable = rows.filter((row) => row.may_update || row.may_delete).map((row) => row.role);
    expect(
      writable,
      `Roles holding update or delete on audit_events: ${writable.join(', ')}`,
    ).toEqual([]);
    // And the privileges it does hold, so the revoke cannot be over-broad and
    // leave the gate unable to write its event at all.
    const writer = rows.find((row) => row.role === 'service_role');
    expect(writer?.may_insert, 'service_role cannot write an audit event').toBe(true);
    expect(writer?.may_select, 'service_role cannot read an audit event').toBe(true);
  });

  it('carries no policy permitting an update or a delete', async () => {
    const { rows } = await client.query<{ policyname: string; cmd: string }>(
      `select policyname, cmd from pg_catalog.pg_policies
        where schemaname = 'public' and tablename = 'audit_events'
          and cmd in ('ALL', 'UPDATE', 'DELETE')`,
    );
    const permissive = rows.map((row) => `${row.policyname} (${row.cmd})`);
    expect(
      permissive,
      `Policies on audit_events permitting more than select and insert: ${permissive.join(', ')}`,
    ).toEqual([]);
  });

  it('lets a tenant be erased, which is the one delete the guarantee allows', async () => {
    // Deletion on request has to keep working: SEEN-083 removes a tenant's rows
    // within 30 days, and an audit table that could never be deleted from would
    // make that impossible. The trigger allows the delete exactly when the owning
    // tenant is already gone, which is only ever true inside that cascade.
    await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
    const { rows } = await client.query(
      'select id from public.audit_events where tenant_id = $1',
      [tenant],
    );
    expect(rows, "the erased tenant's audit events survived the erasure").toEqual([]);
    tenant = undefined;
  });
});
