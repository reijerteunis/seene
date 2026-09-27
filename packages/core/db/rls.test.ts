/**
 * Criterion 3: a query with tenant A's claim returns zero rows from tenant B's
 * orders, findings and claims, and a query with no claim at all returns zero rows
 * from any of them.
 *
 * The second half is the point of the test rather than a nicety: a policy that is
 * permissive when the claim is missing passes the two-tenant comparison and still
 * leaks the whole table to an unauthenticated caller.
 *
 * The rows are written through the connection's owner role, which bypasses row
 * level security the way `service_role` does, and read back the way PostgREST
 * reads for a request: `set local role authenticated` with the verified token's
 * claims in `request.jwt.claims`. That setting, and not the token, is what the
 * policy reads; minting a signed token belongs to the ticket that wires Supabase
 * Auth, and this test records that limit rather than claiming equivalence.
 */
import { randomUUID } from 'node:crypto';

import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { BILLING_CRITICAL_TABLES, TENANT_CLAIM } from './tables';

// The local Supabase stack's Postgres, the address `pnpm dev:up` prints when it
// starts. Overridden by SEEN_DATABASE_URL so CI or a second stack needs no code
// change; the default is the local development credential the CLI fixes for
// every project and is the only connection string this repository ever spells.
const LOCAL_DEFAULT = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres';
const DATABASE_URL = process.env.SEEN_DATABASE_URL ?? LOCAL_DEFAULT;

/** The tables the orders block needs before it can say anything about a policy. */
const NEEDED = ['tenants', 'connections', 'orders'] as const;

/** And the tables the findings and claims block needs. */
const NEEDED_FOR_CLAIMS = ['tenants', 'claims', 'findings'] as const;

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
 * this test therefore proves nothing about tenancy. The two failures have to read
 * differently: a red that fails because Docker is down is not a red. */
async function connect(): Promise<Client> {
  const client = new Client({ connectionString: DATABASE_URL });
  try {
    await client.connect();
  } catch (cause) {
    await client.end().catch(() => undefined);
    throw new Error(
      `No Postgres answering at ${where(DATABASE_URL)}, so this test proves nothing about tenant `
      + 'isolation. Start the local stack with `pnpm dev:up`, apply the migrations with '
      + '`pnpm db:reset`, or point SEEN_DATABASE_URL at another stack. The driver said: '
      + `${(cause as Error).message}`,
      { cause },
    );
  }
  return client;
}

/** Which of the tables this test reads do not exist yet, named rather than left
 * to a driver error halfway through a fixture. */
async function absent(client: Client, needed: readonly string[]): Promise<string[]> {
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relkind = 'r' and c.relname = any($1)`,
    [[...needed]],
  );
  const present = rows.map((row) => row.name);
  return needed.filter((table) => !present.includes(table));
}

interface Fixture {
  tenant: string;
  order: string;
}

interface ClaimFixture {
  tenant: string;
  claim: string;
  finding: string;
}

describe('tenant isolation on orders', () => {
  let client: Client;
  let a: Fixture;
  let b: Fixture;

  /** One tenant, one connection and one order, written as the owner role. */
  async function seed(name: string, marketplace: string, externalId: string): Promise<Fixture> {
    const tenant = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    const tenantId = tenant.rows[0].tenant_id;
    const connection = await client.query<{ id: string }>(
      `insert into public.connections (tenant_id, marketplace, country, status)
       values ($1, $2, 'NL', 'active') returning id`,
      [tenantId, marketplace],
    );
    const order = await client.query<{ id: string }>(
      `insert into public.orders (tenant_id, connection_id, marketplace, external_id, placed_at)
       values ($1, $2, $3, $4, now()) returning id`,
      [tenantId, connection.rows[0].id, marketplace, externalId],
    );
    return { tenant: tenantId, order: order.rows[0].id };
  }

  /** What `select * from orders` returns for a request carrying these claims, or
   * carrying none at all, read as `authenticated` the way PostgREST reads. */
  async function ordersFor(claims: Record<string, string> | null): Promise<string[]> {
    await client.query('begin');
    try {
      if (claims !== null) {
        await client.query('select set_config($1, $2, true)', [
          'request.jwt.claims',
          JSON.stringify(claims),
        ]);
      }
      await client.query('set local role authenticated');
      const { rows } = await client.query<{ id: string }>('select id from public.orders');
      return rows.map((row) => row.id);
    } finally {
      await client.query('rollback');
    }
  }

  beforeAll(async () => {
    client = await connect();
    const missing = await absent(client, NEEDED);
    if (missing.length > 0) {
      throw new Error(
        'This test cannot query public.orders at all: '
        + `${missing.join(', ')} ${missing.length === 1 ? 'does' : 'do'} not exist in the public `
        + 'schema. The trade record migration has not been applied, so there is no policy to '
        + 'prove anything about. Apply it with `pnpm db:reset`.',
      );
    }
    a = await seed('Tenant A', 'bol', 'rls-test-a');
    b = await seed('Tenant B', 'ebay', 'rls-test-b');
  });

  afterAll(async () => {
    if (a) {
      await client.query('delete from public.tenants where tenant_id = any($1)', [
        [a.tenant, b?.tenant].filter(Boolean),
      ]);
    }
    await client?.end();
  });

  it("returns zero rows from tenant B's orders for a request carrying tenant A's claim", async () => {
    const seen = await ordersFor({ [TENANT_CLAIM]: a.tenant });
    expect(seen).toEqual([a.order]);
    expect(seen, "tenant A's request can see tenant B's order").not.toContain(b.order);
  });

  it("returns zero rows from tenant A's orders for a request carrying tenant B's claim", async () => {
    const seen = await ordersFor({ [TENANT_CLAIM]: b.tenant });
    expect(seen).toEqual([b.order]);
    expect(seen, "tenant B's request can see tenant A's order").not.toContain(a.order);
  });

  it('returns zero rows for a request carrying no claim at all', async () => {
    // The assertion this test exists for: a policy that is permissive when the
    // claim is missing passes both comparisons above and leaks every tenant's
    // orders to a caller who never authenticated.
    const seen = await ordersFor(null);
    expect(seen, 'a request with no tenant claim can read orders').toEqual([]);
  });

  it('returns zero rows for a request carrying a claim for no tenant at all', async () => {
    const seen = await ordersFor({ [TENANT_CLAIM]: '00000000-0000-0000-0000-000000000000' });
    expect(seen).toEqual([]);
  });
});

/**
 * The same three assertions on the two tables the Recover module is built out of.
 *
 * A finding and a claim carry the amount a marketplace owes and, through the
 * evidence, as much of a buyer's name and address as a claim needs: they are the
 * rows a tenant would least like another tenant to read. The block is separate
 * from the orders one so that its failure names the tables it could not query
 * rather than being hidden inside a fixture for a table that exists.
 */
describe('tenant isolation on findings and claims', () => {
  let client: Client;
  let a: ClaimFixture;
  let b: ClaimFixture;

  /** One tenant with one claim and one finding grouped into it, as the owner. */
  async function seed(name: string, marketplace: string): Promise<ClaimFixture> {
    const tenant = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    const tenantId = tenant.rows[0].tenant_id;
    const claim = await client.query<{ id: string }>(
      `insert into public.claims (tenant_id, marketplace, rule, mode, amount_cents, status)
       values ($1, $2, 'commission_overcharged', 'assisted', 1250, 'draft') returning id`,
      [tenantId, marketplace],
    );
    const finding = await client.query<{ id: string }>(
      `insert into public.findings
         (tenant_id, claim_id, finding_type, amount_cents, confidence, status)
       values ($1, $2, 'commission_overcharged', 1250, 0.9, 'claimed') returning id`,
      [tenantId, claim.rows[0].id],
    );
    return { tenant: tenantId, claim: claim.rows[0].id, finding: finding.rows[0].id };
  }

  /** The ids one table yields for a request carrying these claims, or none. */
  async function idsFor(table: string, claims: Record<string, string> | null): Promise<string[]> {
    await client.query('begin');
    try {
      if (claims !== null) {
        await client.query('select set_config($1, $2, true)', [
          'request.jwt.claims',
          JSON.stringify(claims),
        ]);
      }
      await client.query('set local role authenticated');
      const { rows } = await client.query<{ id: string }>(`select id from public.${table}`);
      return rows.map((row) => row.id);
    } finally {
      await client.query('rollback');
    }
  }

  beforeAll(async () => {
    client = await connect();
    const missing = await absent(client, NEEDED_FOR_CLAIMS);
    if (missing.length > 0) {
      throw new Error(
        'This test cannot query public.findings or public.claims at all: '
        + `${missing.join(', ')} ${missing.length === 1 ? 'does' : 'do'} not exist in the public `
        + 'schema. The findings, claims and agent migration has not been applied, so there is no '
        + 'policy to prove anything about. Apply it with `pnpm db:reset`.',
      );
    }
    a = await seed('Tenant A findings', 'bol');
    b = await seed('Tenant B findings', 'ebay');
  });

  afterAll(async () => {
    if (a) {
      await client.query('delete from public.tenants where tenant_id = any($1)', [
        [a.tenant, b?.tenant].filter(Boolean),
      ]);
    }
    await client?.end();
  });

  it("returns zero of tenant B's findings and claims for a request carrying tenant A's claim", async () => {
    expect(await idsFor('findings', { [TENANT_CLAIM]: a.tenant })).toEqual([a.finding]);
    expect(await idsFor('claims', { [TENANT_CLAIM]: a.tenant })).toEqual([a.claim]);
  });

  it("returns zero of tenant A's findings and claims for a request carrying tenant B's claim", async () => {
    expect(await idsFor('findings', { [TENANT_CLAIM]: b.tenant })).toEqual([b.finding]);
    expect(await idsFor('claims', { [TENANT_CLAIM]: b.tenant })).toEqual([b.claim]);
  });

  it('returns zero findings and claims for a request carrying no claim at all', async () => {
    expect(await idsFor('findings', null), 'a request with no tenant claim can read findings')
      .toEqual([]);
    expect(await idsFor('claims', null), 'a request with no tenant claim can read claims')
      .toEqual([]);
  });
});

/**
 * The other half of the boundary: what a request bound to a client role may
 * change, rather than what it may read.
 *
 * Tenant isolation decides which rows a policy shows a request. It says nothing
 * about whether the request should be able to write the row at all, and every
 * write in this product is a server action: the web application reads Postgres
 * through row-level security as `authenticated`, and the API and the workers write
 * as `service_role`. So `authenticated` reads and nothing more, and `anon`, which
 * carries no tenant claim, reaches nothing at all.
 *
 * Each test runs its statements the way PostgREST would, inside a transaction
 * that is always rolled back, and then counts what is left of the tenant's trade
 * record with the role reset: a refusal that leaves the record standing and an
 * acceptance that empties it read differently, and the difference is the point.
 */
describe('the writes a client-bound request cannot make', () => {
  let client: Client;
  let tenant: string;
  let connection: string;

  interface Attempt {
    /** What the database did, in one line: `accepted` or `refused` and why. */
    outcome: string;
    /** What is left of the tenant's audit trail and orders afterwards. */
    audit: number;
    orders: number;
  }

  interface Attempted {
    sql: string;
    params?: unknown[];
  }

  /** The first line of a driver error, because a Postgres message carries a hint
   * and a position that say nothing a test reader needs. */
  function firstLine(message: string): string {
    return message.split('\n')[0].trim();
  }

  async function countFor(table: string): Promise<number> {
    const { rows } = await client.query<{ n: string }>(
      `select count(*) as n from public.${table} where tenant_id = $1`,
      [tenant],
    );
    return Number(rows[0].n);
  }

  /**
   * Runs these statements as `role`, carrying these claims, in a transaction that
   * is always rolled back, and reports what happened. A refused statement is
   * rolled back to its savepoint so the counts afterwards can still be read.
   */
  async function attempt(
    role: 'anon' | 'authenticated',
    claims: Record<string, string> | null,
    statements: readonly Attempted[],
  ): Promise<Attempt> {
    await client.query('begin');
    try {
      if (claims !== null) {
        await client.query('select set_config($1, $2, true)', [
          'request.jwt.claims',
          JSON.stringify(claims),
        ]);
      }
      await client.query(`set local role ${role}`);
      let outcome = `accepted: all ${statements.length} statements`;
      for (const [index, statement] of statements.entries()) {
        await client.query('savepoint attempted');
        try {
          const result = await client.query(statement.sql, [...(statement.params ?? [])]);
          if (statements.length === 1) {
            outcome = `accepted: ${result.rowCount} row${result.rowCount === 1 ? '' : 's'}`;
          }
        } catch (error) {
          outcome = `refused at statement ${index + 1} of ${statements.length}: `
            + firstLine((error as Error).message);
          await client.query('rollback to savepoint attempted');
          break;
        }
      }
      await client.query('reset role');
      return { outcome, audit: await countFor('audit_events'), orders: await countFor('orders') };
    } finally {
      await client.query('rollback');
    }
  }

  /** A refusal by privilege, which is the only refusal this block accepts: a
   * statement that failed a foreign key or a check constraint was still allowed
   * to reach the table. */
  const REFUSED = /^refused[^:]*: permission denied/;

  beforeAll(async () => {
    client = await connect();
    const missing = await absent(client, [
      'tenants', 'connections', 'orders', 'audit_events', 'settlements', 'settlement_lines',
      'claims', 'invoices', 'statements', 'headroom_entries',
    ]);
    if (missing.length > 0) {
      throw new Error(
        'This test cannot say anything about what a client-bound request may write: '
        + `${missing.join(', ')} ${missing.length === 1 ? 'does' : 'do'} not exist in the public `
        + 'schema. The trade record migrations have not been applied; apply them with '
        + '`pnpm db:reset`.',
      );
    }
    const seeded = await client.query<{ tenant_id: string }>(
      "insert into public.tenants (name) values ('Tenant writes') returning tenant_id",
    );
    tenant = seeded.rows[0].tenant_id;
    const seededConnection = await client.query<{ id: string }>(
      `insert into public.connections (tenant_id, marketplace, country, status)
       values ($1, 'bol', 'NL', 'active') returning id`,
      [tenant],
    );
    connection = seededConnection.rows[0].id;
    await client.query(
      `insert into public.orders (tenant_id, connection_id, marketplace, external_id, placed_at)
       values ($1, $2, 'bol', 'writes-test-order', now())`,
      [tenant, connection],
    );
    // Two events, because the gate writes one before every side effect and the
    // question is whether both of them can be made to disappear.
    await client.query(
      `insert into public.audit_events (tenant_id, event_type, actor)
       values ($1, 'test.first', 'test'), ($1, 'test.second', 'test')`,
      [tenant],
    );
    await client.query(
      `insert into public.invoices (tenant_id, period_start, period_end, total_cents, status)
       values ($1, date '2026-08-01', date '2026-08-31', 120000, 'open')`,
      [tenant],
    );
    await client.query(
      `insert into public.statements (tenant_id, period_start, period_end, total_recovered_cents)
       values ($1, date '2026-08-01', date '2026-08-31', 400000)`,
      [tenant],
    );
  });

  afterAll(async () => {
    if (tenant) {
      await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
    }
    await client?.end();
  });

  it('refuses the delete of the tenant row that would erase the whole trade record', async () => {
    // The cascade from public.tenants reaches every table, and it is the one
    // branch the append-only trigger on audit_events permits: the trigger lets a
    // delete through exactly when the owning tenant is already gone. So a delete
    // of the tenant row is not one row, it is the trade record and the audit trail
    // that exists to hold the agent, and the tenant, accountable.
    const attempted = await attempt('authenticated', { [TENANT_CLAIM]: tenant }, [
      { sql: 'delete from public.tenants where tenant_id = $1', params: [tenant] },
    ]);
    expect(
      attempted.outcome,
      'a signed-in user of the tenant deleted the tenant row, and the cascade took the trade '
      + `record with it: of the 2 audit events and 1 order the tenant had, ${attempted.audit} `
      + `audit ${attempted.audit === 1 ? 'event' : 'events'} and ${attempted.orders} `
      + `${attempted.orders === 1 ? 'order' : 'orders'} are left`,
    ).toMatch(REFUSED);
    expect(attempted.audit, "the tenant's audit events did not survive the attempt").toBe(2);
    expect(attempted.orders, "the tenant's orders did not survive the attempt").toBe(1);
  });

  it('refuses the three writes that would manufacture a billable credit', async () => {
    // A credit is billable only as an ingested settlement line linked to a claim.
    // These three statements are that link, written by the party that would be
    // invoiced for it: a settlement nobody ingested, a compensation line of
    // EUR 9,999.00 nobody was paid, and a claim that says it was credited by it.
    const settlement = randomUUID();
    const line = randomUUID();
    const attempted = await attempt('authenticated', { [TENANT_CLAIM]: tenant }, [
      {
        sql: `insert into public.settlements
                (id, tenant_id, connection_id, marketplace, external_id, total_cents)
              values ($1, $2, $3, 'bol', 'invented-settlement', 999900)`,
        params: [settlement, tenant, connection],
      },
      {
        sql: `insert into public.settlement_lines
                (id, tenant_id, settlement_id, marketplace, external_id, line_type, amount_cents)
              values ($1, $2, $3, 'bol', 'invented-line', 'compensation', 999900)`,
        params: [line, tenant, settlement],
      },
      {
        sql: `insert into public.claims
                (tenant_id, marketplace, rule, mode, amount_cents, status,
                 credited_by_settlement_line_id)
              values ($1, 'bol', 'commission_overcharged', 'assisted', 999900, 'credited', $2)`,
        params: [tenant, line],
      },
    ]);
    expect(
      attempted.outcome,
      'the tenant wrote its own settlement line and its own credited claim, which is a billable '
      + 'event created by a person rather than ingested',
    ).toMatch(REFUSED);
  });

  it('refuses to void the invoice the tenant is being charged by', async () => {
    const attempted = await attempt('authenticated', { [TENANT_CLAIM]: tenant }, [
      {
        sql: `update public.invoices set total_cents = 0, status = 'void' where tenant_id = $1`,
        params: [tenant],
      },
    ]);
    expect(attempted.outcome, 'the tenant zeroed and voided its own invoice').toMatch(REFUSED);
  });

  it('refuses to delete the statement that evidences what was recovered', async () => {
    const attempted = await attempt('authenticated', { [TENANT_CLAIM]: tenant }, [
      { sql: 'delete from public.statements where tenant_id = $1', params: [tenant] },
    ]);
    expect(attempted.outcome, 'the tenant deleted its own signed statement').toMatch(REFUSED);
  });

  it('refuses to state its own headroom figure', async () => {
    // The Price module meters headroom_entries and nothing else may state a
    // headroom figure, so a refusal that comes from a foreign key rather than from
    // the privilege is not a refusal: the next attempt carries a real
    // price_change_id.
    const attempted = await attempt('authenticated', { [TENANT_CLAIM]: tenant }, [
      {
        sql: `insert into public.headroom_entries
                (tenant_id, price_change_id, counted_on, headroom_cents)
              values ($1, gen_random_uuid(), current_date, 500000)`,
        params: [tenant],
      },
    ]);
    expect(attempted.outcome, 'the tenant metered its own headroom').toMatch(REFUSED);
  });

  it('holds no write privilege on any table a billable event is built out of', async () => {
    const { rows } = await client.query<{ table_name: string; role: string; privilege: string }>(
      `select t.table_name, r.role, p.privilege
         from unnest($1::text[]) as t(table_name)
         cross join unnest(array['anon', 'authenticated']) as r(role)
         cross join unnest(array['insert', 'update', 'delete', 'truncate']) as p(privilege)
        where has_table_privilege(r.role, format('public.%I', t.table_name), p.privilege)`,
      [[...BILLING_CRITICAL_TABLES]],
    );
    const held = rows.map((row) => `${row.role} may ${row.privilege} ${row.table_name}`);
    expect(
      held,
      `${held.length} write privileges on the tables a billable event is built out of are held by `
      + `a role a browser is bound to: ${held.join('; ')}`,
    ).toEqual([]);
  });

  it('lets the same request read its own rows, so the revoke is not over-broad', async () => {
    // The other half: a boundary that also stopped the console reading the trade
    // record would be no use to anyone.
    const attempted = await attempt('authenticated', { [TENANT_CLAIM]: tenant }, [
      { sql: 'select id from public.orders', params: [] },
    ]);
    expect(attempted.outcome, 'a signed-in user of the tenant cannot read its own orders')
      .toBe('accepted: 1 row');
  });

  it('refuses a read to a caller who never signed in', async () => {
    // anon carries no tenant claim, so the policy already yields it nothing. The
    // privilege goes too, so that a table which later loses its policy is not
    // readable by the unauthenticated on top of everything else.
    const attempted = await attempt('anon', null, [
      { sql: 'select id from public.orders', params: [] },
    ]);
    expect(attempted.outcome, 'an unauthenticated caller reached public.orders at all')
      .toMatch(REFUSED);
  });
});
