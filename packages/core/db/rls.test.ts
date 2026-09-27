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
import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { TENANT_CLAIM } from './tables';

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
