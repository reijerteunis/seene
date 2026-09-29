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

import { BILLING_CRITICAL_TABLES, CLIENT_BOUND_ROLES, TENANT_CLAIM } from './tables';

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

/**
 * CODEX-01: what a policy cannot say anything about, which is whose parent a row
 * has.
 *
 * Every table carries `tenant_id` and a tenancy policy, and the first three blocks
 * of this file prove that a request bound to tenant A reads none of tenant B's
 * rows. None of that is a statement about the relationship between two rows. A key
 * written `references public.connections (id)` accepts any connection in the
 * database beside any `tenant_id`, so an ingest run that carries a mismatched
 * parent id writes a child row of tenant B hanging from a parent of tenant A, and
 * the cascade then makes tenant A's erasure delete tenant B's row. Measured
 * against the local stack before the fix: the insert was accepted, deleting
 * tenant A removed the order, and tenant B was still there to notice it gone.
 *
 * These tests are written as `service_role`, not as `authenticated`, because that
 * is the role the workers ingest with and the only role that can reach the insert
 * at all. Everything is inside a transaction that is rolled back, including the
 * erasures, so the block leaves the database as it found it.
 */
describe('a parent row belonging to another tenant', () => {
  let client: Client;

  /** The SQLSTATE the database answered with, or `accepted` when it did not
   * refuse. 23503 is a foreign key violation, which is the refusal wanted here.
   *
   * Behind a savepoint, because the erasure test has to carry on asking questions
   * after the refusal and a failed statement otherwise aborts the whole
   * transaction. Before the fix there was nothing to recover from and the
   * savepoint was dead code; that is the shape of a test that has to pass in both
   * states to be worth recording. */
  async function said(body: () => Promise<unknown>): Promise<string> {
    await client.query('savepoint attempted');
    try {
      await body();
      await client.query('release savepoint attempted');
      return 'accepted';
    } catch (error) {
      await client.query('rollback to savepoint attempted');
      return (error as { code?: string }).code ?? (error as Error).message;
    }
  }

  /** One tenant with a connection of its own, written as `service_role`. */
  async function seed(name: string, marketplace: string): Promise<{
    tenant: string; connection: string;
  }> {
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
    return { tenant: tenantId, connection: connection.rows[0].id };
  }

  /** How many rows of `table` this tenant has, read with the role reset. */
  async function countFor(table: string, tenant: string): Promise<number> {
    const { rows } = await client.query<{ total: string }>(
      `select count(*) as total from public.${table} where tenant_id = $1`,
      [tenant],
    );
    return Number(rows[0].total);
  }

  /** Everything inside, rolled back: the erasures below are real deletes. */
  async function rolledBack<T>(body: () => Promise<T>): Promise<T> {
    await client.query('begin');
    try {
      await client.query('set local role service_role');
      return await body();
    } finally {
      await client.query('rollback');
    }
  }

  beforeAll(async () => {
    client = await connect();
    const missing = await absent(client, [
      'tenants', 'connections', 'orders', 'order_lines', 'products', 'audit_events',
      'agent_runs', 'agent_actions', 'approvals', 'settlements', 'settlement_lines',
      'claims', 'invoices', 'statements',
    ]);
    if (missing.length > 0) {
      throw new Error(
        'This test cannot say anything about whose parent a row has: '
        + `${missing.join(', ')} ${missing.length === 1 ? 'does' : 'do'} not exist in the public `
        + 'schema. The trade record migrations have not been applied; apply them with '
        + '`pnpm db:reset`.',
      );
    }
  });

  afterAll(async () => {
    await client?.end();
  });

  it("refuses an order whose connection belongs to another tenant", async () => {
    // The reviewer's own scenario, written out: tenants A and B, a Bol connection
    // belonging to A, and an order carrying B's tenant_id and A's connection_id.
    // Two independent keys each see something they recognise; the pair of them is
    // a row of tenant B hanging from a parent of tenant A.
    const answer = await rolledBack(async () => {
      const a = await seed('Tenant parent A', 'bol');
      const b = await seed('Tenant parent B', 'bol');
      return said(() => client.query(
        `insert into public.orders (tenant_id, connection_id, marketplace, external_id, placed_at)
         values ($1, $2, 'bol', 'cross-tenant-probe', now())`,
        [b.tenant, a.connection],
      ));
    });
    expect(
      answer,
      'An order carrying tenant B\'s tenant_id and tenant A\'s connection_id was '
      + `${answer === 'accepted' ? 'accepted' : `refused with SQLSTATE ${answer}`}, where a `
      + 'foreign key violation (23503) is what keeps one tenant\'s ingest run out of another '
      + 'tenant\'s trade record',
    ).toBe('23503');
  });

  it("does not let one tenant's erasure reach another tenant's rows", async () => {
    // The consequence the insert above is refused for. Whatever the database let
    // be written, erasing tenant A must not change how many rows tenant B has.
    const { before, after, probe, survived } = await rolledBack(async () => {
      const a = await seed('Tenant erasure A', 'bol');
      const b = await seed('Tenant erasure B', 'ebay');
      await client.query(
        `insert into public.orders (tenant_id, connection_id, marketplace, external_id, placed_at)
         values ($1, $2, 'ebay', 'tenant-b-own-order', now())`,
        [b.tenant, b.connection],
      );
      const accepted = await said(() => client.query(
        `insert into public.orders (tenant_id, connection_id, marketplace, external_id, placed_at)
         values ($1, $2, 'bol', 'cross-tenant-probe', now())`,
        [b.tenant, a.connection],
      ));
      const held = await countFor('orders', b.tenant);
      await client.query('delete from public.tenants where tenant_id = $1', [a.tenant]);
      return {
        before: held,
        after: await countFor('orders', b.tenant),
        probe: accepted,
        survived: await countFor('tenants', b.tenant),
      };
    });
    expect(survived, 'tenant B did not survive tenant A\'s erasure at all').toBe(1);
    expect(
      after,
      `Tenant B had ${before} ${before === 1 ? 'order' : 'orders'} and has ${after} after tenant `
      + `A was erased, because the cross-tenant order was ${probe === 'accepted' ? 'accepted' : `refused with SQLSTATE ${probe}`} `
      + "and the cascade from tenant A then carried it away. One tenant's deletion on request "
      + "destroyed part of another tenant's trade record",
    ).toBe(before);
  });

  it('still erases a tenant completely, through every key the fix touches', async () => {
    // The other side of the same constraint. Deletion on request is a promise of
    // the PRD and SEEN-083 has to keep it, so the cascade must still empty the
    // trade record: a composite key with `on delete restrict` would refuse the
    // delete mid-statement, and one whose `set null` reached tenant_id would fail
    // the not-null constraint on the way through. Each table here is on the far
    // side of a key of one of those shapes, including audit_events, whose
    // append-only trigger permits exactly this one delete.
    const left = await rolledBack(async () => {
      const a = await seed('Tenant erased whole', 'bol');
      const product = await client.query<{ id: string }>(
        `insert into public.products (tenant_id, sku) values ($1, 'erasure-sku') returning id`,
        [a.tenant],
      );
      const order = await client.query<{ id: string }>(
        `insert into public.orders (tenant_id, connection_id, marketplace, external_id, placed_at)
         values ($1, $2, 'bol', 'erasure-order', now()) returning id`,
        [a.tenant, a.connection],
      );
      const line = await client.query<{ id: string }>(
        `insert into public.order_lines (tenant_id, order_id, product_id, quantity)
         values ($1, $2, $3, 1) returning id`,
        [a.tenant, order.rows[0].id, product.rows[0].id],
      );
      const settlement = await client.query<{ id: string }>(
        `insert into public.settlements (tenant_id, connection_id, marketplace, external_id)
         values ($1, $2, 'bol', 'erasure-settlement') returning id`,
        [a.tenant, a.connection],
      );
      const settlementLine = await client.query<{ id: string }>(
        `insert into public.settlement_lines
           (tenant_id, settlement_id, order_line_id, marketplace, external_id, line_type,
            amount_cents)
         values ($1, $2, $3, 'bol', 'erasure-line', 'compensation', 1250) returning id`,
        [a.tenant, settlement.rows[0].id, line.rows[0].id],
      );
      await client.query(
        `insert into public.claims
           (tenant_id, marketplace, rule, mode, amount_cents, status,
            credited_by_settlement_line_id)
         values ($1, 'bol', 'commission_overcharged', 'assisted', 1250, 'credited', $2)`,
        [a.tenant, settlementLine.rows[0].id],
      );
      const invoice = await client.query<{ id: string }>(
        `insert into public.invoices (tenant_id, period_start, period_end, total_cents, status)
         values ($1, date '2026-08-01', date '2026-08-31', 1250, 'open') returning id`,
        [a.tenant],
      );
      await client.query(
        `insert into public.statements
           (tenant_id, invoice_id, period_start, period_end, total_recovered_cents)
         values ($1, $2, date '2026-08-01', date '2026-08-31', 1250)`,
        [a.tenant, invoice.rows[0].id],
      );
      const approval = await client.query<{ id: string }>(
        'insert into public.approvals (tenant_id) values ($1) returning id',
        [a.tenant],
      );
      const run = await client.query<{ id: string }>(
        'insert into public.agent_runs (tenant_id) values ($1) returning id',
        [a.tenant],
      );
      const action = await client.query<{ id: string }>(
        `insert into public.agent_actions (tenant_id, agent_run_id, approval_id, tool)
         values ($1, $2, $3, 'erasure_probe') returning id`,
        [a.tenant, run.rows[0].id, approval.rows[0].id],
      );
      await client.query(
        `insert into public.audit_events (tenant_id, agent_action_id, event_type, actor)
         values ($1, $2, 'test.erasure', 'test')`,
        [a.tenant, action.rows[0].id],
      );
      await client.query('delete from public.tenants where tenant_id = $1', [a.tenant]);
      const remaining: string[] = [];
      for (const table of [
        'tenants', 'connections', 'products', 'orders', 'order_lines', 'settlements',
        'settlement_lines', 'claims', 'invoices', 'statements', 'approvals', 'agent_runs',
        'agent_actions', 'audit_events',
      ]) {
        const held = await countFor(table, a.tenant);
        if (held > 0) remaining.push(`${table}: ${held}`);
      }
      return remaining;
    });
    expect(
      left,
      'The erased tenant still has rows, so deletion on request no longer empties the trade '
      + `record: ${left.join('; ')}`,
    ).toEqual([]);
  });
});

/**
 * Criterion 3 against every table in the public schema, rather than against the
 * three the blocks above seed by hand.
 *
 * The first two blocks read `orders`, `findings` and `claims`, which was read as
 * proof of tenant isolation until the second Codex review of SEEN-008 (CODEX-02)
 * pointed at the twenty-six tables nothing queries. A permissive select policy on
 * `public.evidence` reading `using (seen.current_tenant() is not null)` hands
 * every tenant's buyer name and buyer address to any signed-in user of any other
 * tenant, and every test in this repository passed with it in place: the
 * behavioural tests never touched the table, and the catalogue assertion in
 * `schema.test.ts` was reading the clause for the word `current_tenant`.
 *
 * A test that reads the text of a policy is beaten by the next expression somebody
 * writes; `OR true` beat the first version of that assertion and `IS NOT NULL` beat
 * it too. This block asks the database instead. It seeds a row into every table of
 * the public schema for two tenants, from the catalogue rather than from a list of
 * table names, and reads each table back as `authenticated` carrying one tenant's
 * claim. A policy that exposes another tenant's rows fails here because it does,
 * whatever its clause says, and a table a later migration adds is probed without
 * anyone remembering to extend this file.
 *
 * The fixture is built from `pg_catalog` for the same reason: the required columns
 * of a table, and the parents its mandatory foreign keys demand, are facts the
 * database already holds, and a hand-written fixture would go stale one migration
 * later and start passing by seeding nothing.
 *
 * What this cannot reach is the WITH CHECK half of a policy: `authenticated` holds
 * no insert privilege on any table, so no cross-tenant write probe gets as far as
 * the clause. That half is asserted from the catalogue in `schema.test.ts`.
 */
describe('tenant isolation on every table in the public schema', () => {
  let client: Client;
  /** Every table of the public schema, in the order a row can be seeded into them. */
  let governed: string[];
  let a: string;
  let b: string;

  /** A column a row cannot be written without: not null, no default, not generated. */
  interface Required { table: string; column: string; type: string }

  /** A foreign key whose child columns are all required, so a parent must exist first. */
  interface Mandatory { table: string; columns: string[]; parent: string; parentColumns: string[] }

  let required: Required[];
  let mandatory: Mandatory[];

  async function requiredColumns(): Promise<Required[]> {
    const { rows } = await client.query<Required>(
      `select c.relname as table, a.attname as column,
              format_type(a.atttypid, a.atttypmod) as type
         from pg_catalog.pg_attribute a
         join pg_catalog.pg_class c on c.oid = a.attrelid
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
         left join pg_catalog.pg_attrdef d on d.adrelid = c.oid and d.adnum = a.attnum
        where n.nspname = 'public' and c.relkind = 'r'
          and a.attnum > 0 and not a.attisdropped and a.attnotnull
          and d.adbin is null and a.attidentity = '' and a.attgenerated = ''
        order by c.relname, a.attnum`,
    );
    return rows;
  }

  /**
   * The foreign keys every one of whose child columns is required, which are the
   * only ones a seeded row has to satisfy. Reading all of them instead would make
   * the seeding order cyclic over keys that are nullable and need no parent at all.
   */
  async function mandatoryKeys(): Promise<Mandatory[]> {
    const { rows } = await client.query<Mandatory>(
      `select c.relname as table, p.relname as parent,
              (select array_agg(att.attname order by k.ord)
                 from unnest(con.conkey) with ordinality k(attnum, ord)
                 join pg_catalog.pg_attribute att
                   on att.attrelid = con.conrelid and att.attnum = k.attnum)::text[] as columns,
              (select array_agg(att.attname order by k.ord)
                 from unnest(con.confkey) with ordinality k(attnum, ord)
                 join pg_catalog.pg_attribute att
                   on att.attrelid = con.confrelid and att.attnum = k.attnum)::text[]
                as "parentColumns"
         from pg_catalog.pg_constraint con
         join pg_catalog.pg_class c on c.oid = con.conrelid
         join pg_catalog.pg_class p on p.oid = con.confrelid
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and con.contype = 'f'`,
    );
    const isRequired = (table: string, column: string): boolean =>
      required.some((entry) => entry.table === table && entry.column === column);
    return rows.filter((key) => key.columns.every((column) => isRequired(key.table, column)));
  }

  /** The tables in an order that puts every mandatory parent before its child. */
  function seedOrder(tables: readonly string[]): string[] {
    const ordered: string[] = [];
    const placed = new Set<string>();
    const visit = (table: string, chain: string[]): void => {
      if (placed.has(table)) return;
      if (chain.includes(table)) {
        throw new Error(
          'The mandatory foreign keys of the public schema form a cycle, so no order seeds them '
          + `all: ${chain.concat(table).join(' -> ')}. A key in that cycle has to become `
          + 'nullable before a row can be written at all.',
        );
      }
      for (const key of mandatory) {
        if (key.table === table && key.parent !== table) visit(key.parent, chain.concat(table));
      }
      placed.add(table);
      ordered.push(table);
    };
    for (const table of tables) visit(table, []);
    return ordered;
  }

  /**
   * A value of this type, unique to this tenant and column so that a tenant-scoped
   * unique index never refuses the second tenant's row. A type nobody has written
   * a case for refuses loudly: a silent skip would write no row and leave the
   * table empty, which is how the probe below would pass by finding nothing.
   */
  function valueFor(type: string, label: string): string | number | boolean {
    if (type === 'uuid') return randomUUID();
    if (type === 'text' || type.startsWith('character')) return label;
    if (type === 'bigint' || type === 'integer' || type === 'smallint') return 1;
    if (type.startsWith('numeric')) return 1;
    if (type === 'date') return '2026-09-29';
    if (type.startsWith('timestamp')) return new Date().toISOString();
    if (type === 'boolean') return false;
    if (type === 'jsonb' || type === 'json') return '{}';
    throw new Error(
      `This fixture has no value for a column of type ${type}, so it cannot seed a row and the `
      + 'cross-tenant read below would pass against an empty table. Add the type to valueFor.',
    );
  }

  /** One tenant with a row in every table of the public schema, as the owner role. */
  async function seedTenant(label: string): Promise<string> {
    const created = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [label],
    );
    const tenant = created.rows[0].tenant_id;
    for (const table of governed) {
      if (table === 'tenants') continue;
      // A trigger seeds the marketplaces catalogue for a new tenant, and a row a
      // trigger wrote is as much this tenant's row as one written here.
      const already = await client.query(
        `select 1 from public.${table} where tenant_id = $1 limit 1`,
        [tenant],
      );
      if ((already.rowCount ?? 0) > 0) continue;
      const row: Record<string, unknown> = { tenant_id: tenant };
      for (const key of mandatory.filter((entry) => entry.table === table)) {
        if (key.parent === 'tenants') continue;
        const parent = await client.query<Record<string, unknown>>(
          `select ${key.parentColumns.join(', ')} from public.${key.parent}
            where tenant_id = $1 limit 1`,
          [tenant],
        );
        if (parent.rowCount === 0) {
          throw new Error(
            `No row in public.${key.parent} for ${label} to hang a row of public.${table} from, `
            + 'so this fixture cannot seed the table and the cross-tenant read below would pass '
            + 'against an empty table.',
          );
        }
        key.columns.forEach((column, index) => {
          row[column] = parent.rows[0][key.parentColumns[index]];
        });
      }
      for (const column of required.filter((entry) => entry.table === table)) {
        if (row[column.column] !== undefined) continue;
        row[column.column] = valueFor(
          column.type,
          `${label} ${table}.${column.column} ${randomUUID().slice(0, 8)}`,
        );
      }
      const names = Object.keys(row);
      try {
        await client.query(
          `insert into public.${table} (${names.join(', ')})
           values (${names.map((_, index) => `$${index + 1}`).join(', ')})`,
          names.map((name) => row[name]),
        );
      } catch (cause) {
        throw new Error(
          `This fixture could not seed public.${table} for ${label}, so the cross-tenant read `
          + `below would pass against an empty table. Postgres said: ${(cause as Error).message}`,
          { cause },
        );
      }
    }
    return tenant;
  }

  /**
   * Which tables a request carrying these claims can read rows of `owner` from, and
   * how many of them, read as `authenticated` the way PostgREST reads. Runs inside
   * a savepoint of an already open transaction, so a policy injected by the caller
   * is in force and the role and the claim are gone again afterwards.
   */
  async function visibleTo(
    claims: Record<string, string> | null, owner: string,
  ): Promise<Record<string, number>> {
    await client.query('savepoint probe');
    try {
      if (claims !== null) {
        await client.query('select set_config($1, $2, true)', [
          'request.jwt.claims',
          JSON.stringify(claims),
        ]);
      }
      await client.query('set local role authenticated');
      const seen: Record<string, number> = {};
      for (const table of governed) {
        const { rows } = await client.query<{ total: string }>(
          `select count(*) as total from public.${table} where tenant_id = $1`,
          [owner],
        );
        if (Number(rows[0].total) > 0) seen[table] = Number(rows[0].total);
      }
      return seen;
    } finally {
      await client.query('rollback to savepoint probe');
    }
  }

  /** Everything inside, rolled back: the policies injected below are real policies. */
  async function rolledBack<T>(body: () => Promise<T>): Promise<T> {
    await client.query('begin');
    try {
      return await body();
    } finally {
      await client.query('rollback');
    }
  }

  beforeAll(async () => {
    client = await connect();
    const { rows } = await client.query<{ name: string }>(
      `select c.relname as name
         from pg_catalog.pg_class c
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = 'r'
        order by c.relname`,
    );
    if (rows.length === 0) {
      throw new Error(
        'There is not one table in the public schema, so a cross-tenant read proves nothing '
        + 'about any policy. The trade record migrations have not been applied; apply them with '
        + '`pnpm db:reset`.',
      );
    }
    required = await requiredColumns();
    mandatory = await mandatoryKeys();
    governed = seedOrder(rows.map((row) => row.name));
    a = await seedTenant('Tenant every table A');
    b = await seedTenant('Tenant every table B');
  });

  afterAll(async () => {
    if (a) {
      await client.query('delete from public.tenants where tenant_id = any($1)', [
        [a, b].filter(Boolean),
      ]);
    }
    await client?.end();
  });

  it('holds a row of each tenant in every table, so no table passes by being empty', async () => {
    // The guard on the three assertions below. Each of them is of the shape "the
    // tables this request could read another tenant's rows from are none", and a
    // table with no rows in it answers that with nothing whatever its policy says.
    const empty: string[] = [];
    for (const table of governed) {
      for (const [name, tenant] of [['A', a], ['B', b]] as const) {
        const { rows } = await client.query<{ total: string }>(
          `select count(*) as total from public.${table} where tenant_id = $1`,
          [tenant],
        );
        if (Number(rows[0].total) === 0) empty.push(`${table} for tenant ${name}`);
      }
    }
    expect(
      empty,
      `${empty.length} of the ${governed.length * 2} tenant-and-table pairs this block reads hold `
      + 'no row at all, so a policy on them could expose every tenant and the read below would '
      + `still find nothing: ${empty.join(', ')}`,
    ).toEqual([]);
  });

  it("shows a request carrying tenant A's claim none of tenant B's rows, in any table", async () => {
    const leaked = await rolledBack(() => visibleTo({ [TENANT_CLAIM]: a }, b));
    expect(
      Object.keys(leaked),
      'A request carrying tenant A\'s claim read rows belonging to tenant B from '
      + `${Object.keys(leaked).length} of the ${governed.length} tables in the public schema: `
      + Object.entries(leaked).map(([table, total]) => `${table} (${total})`).join(', '),
    ).toEqual([]);
  });

  it("shows a request carrying tenant B's claim none of tenant A's rows, in any table", async () => {
    const leaked = await rolledBack(() => visibleTo({ [TENANT_CLAIM]: b }, a));
    expect(
      Object.keys(leaked),
      'A request carrying tenant B\'s claim read rows belonging to tenant A from '
      + `${Object.keys(leaked).length} of the ${governed.length} tables in the public schema: `
      + Object.entries(leaked).map(([table, total]) => `${table} (${total})`).join(', '),
    ).toEqual([]);
  });

  it('shows a request carrying no claim at all nothing, in any table', async () => {
    // A policy that is permissive when the claim is missing passes both comparisons
    // above and still leaks the whole schema to a caller who never authenticated.
    const leaked = await rolledBack(() => visibleTo(null, a));
    expect(
      Object.keys(leaked),
      'A request carrying no tenant claim read rows from '
      + `${Object.keys(leaked).length} of the ${governed.length} tables in the public schema: `
      + Object.entries(leaked).map(([table, total]) => `${table} (${total})`).join(', '),
    ).toEqual([]);
  });

  it("shows a view over the buyer PII table none of another tenant's rows", async () => {
    // The behavioural half of F19, written as the migration SEEN-046 or SEEN-024
    // will want it: three columns of public.shipments, which is a table holding
    // buyer name and buyer address, published as a view in the schema the Data API
    // serves.
    //
    // Everything the twenty-nine tables are guarded by is per table and stops at
    // `relkind = 'r'`. A view is a different relation kind, it is born holding
    // schema public's default access control list, and it is not subject to the
    // row-level security of the tables underneath it unless it was created `with
    // (security_invoker = true)`: by default it runs with its owner's rights, and
    // the owner is the migration role. Measured before this was fixed: `anon` was
    // refused public.shipments with SQLSTATE 42501 and read both tenants' buyer
    // name and buyer address through the view.
    //
    // A refusal counts as a pass here and so does an empty read, because the two
    // are the same answer to the question asked: the privilege is one way to be
    // unable to read another tenant's rows and the policy is the other. What keeps
    // that from passing vacuously is the assertion above it, that the view exists
    // and that the session that created it does read tenant B's rows through it.
    await rolledBack(async () => {
      await client.query(
        'create view public.seen_buyer_book_probe as '
        + 'select tenant_id, buyer_name, buyer_address from public.shipments',
      );
      const owner = await client.query<{ total: string }>(
        'select count(*) as total from public.seen_buyer_book_probe where tenant_id = $1',
        [b],
      );
      expect(
        Number(owner.rows[0].total),
        'The session that created the view reads none of tenant B\'s rows through it, so this '
        + 'test would report no leak whatever the view exposed to anyone else',
      ).toBeGreaterThan(0);

      const leaked: string[] = [];
      for (const role of CLIENT_BOUND_ROLES) {
        await client.query('savepoint view_probe');
        try {
          // Tenant A's claim, reading tenant B's rows: the request a signed-in user
          // of one brand makes against another brand's buyer data.
          await client.query('select set_config($1, $2, true)', [
            'request.jwt.claims',
            JSON.stringify({ [TENANT_CLAIM]: a }),
          ]);
          await client.query(`set local role ${role}`);
          const { rows } = await client.query<{ total: string }>(
            'select count(*) as total from public.seen_buyer_book_probe where tenant_id = $1',
            [b],
          );
          if (Number(rows[0].total) > 0) {
            leaked.push(`${role} read ${rows[0].total} of tenant B's rows`);
          }
        } catch (cause) {
          // Refused outright, which is the outcome this asks for. Any other error
          // is this test failing to ask the question and has to be seen.
          if ((cause as { code?: string }).code !== '42501') throw cause;
        } finally {
          await client.query('rollback to savepoint view_probe');
        }
      }
      expect(
        leaked,
        'A view over public.shipments, which holds buyer name and buyer address, handed another '
        + `tenant's buyer data to ${leaked.length} of the ${CLIENT_BOUND_ROLES.length} roles a `
        + 'browser request is bound to, while the same roles are refused the table itself: '
        + leaked.join('; '),
      ).toEqual([]);
    });
  });

  it('reports the table a clause that never compares the tenant exposes, however it is spelled',
    async () => {
      // What the three assertions above are worth, measured rather than asserted.
      // Each of these clauses was accepted by the catalogue assertion that read a
      // policy for the word `current_tenant`, and the first of them is the review's
      // own scenario: any signed-in user of any tenant reads every tenant's evidence,
      // buyer name and buyer address included. A read of the table says so, and the
      // clause it is written in makes no difference to what it says.
      const spellings = [
        'seen.current_tenant() is not null',
        'tenant_id = seen.current_tenant() or true',
        'true',
      ];
      const unnoticed: string[] = [];
      for (const clause of spellings) {
        const leaked = await rolledBack(async () => {
          await client.query(
            `create policy leak_spelling on public.evidence for select to authenticated
             using (${clause})`,
          );
          return visibleTo({ [TENANT_CLAIM]: a }, b);
        });
        if (!Object.keys(leaked).includes('evidence')) unnoticed.push(clause);
      }
      expect(
        unnoticed,
        `${unnoticed.length} of the ${spellings.length} permissive policies on public.evidence `
        + "that expose every tenant's evidence to every other tenant were not seen by a request "
        + `reading the table: using (${unnoticed.join('), using (')})`,
      ).toEqual([]);
    });
});
