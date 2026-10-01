/**
 * Criterion 4: the unique index on `(tenant_id, marketplace, external_id)` exists
 * on orders, shipments, returns, settlements and settlement_lines.
 *
 * Asserted as behaviour rather than as an index name: what ingest depends on is
 * that the second write of a row a marketplace has already been read for is
 * refused, and an index renamed or replaced by a constraint keeps that promise
 * while a test on `pg_indexes` would fail. The refusal is checked as the raised
 * unique violation, SQLSTATE 23505.
 *
 * The other two halves of the key are asserted as well, because a unique index on
 * `external_id` alone would pass the first assertion and be wrong in the two ways
 * that matter: two tenants selling on the same marketplace do see the same order
 * id, and one tenant's id on Bol says nothing about the same id on eBay.
 *
 * This test was written in the third slice and passed on its first run. The index
 * it proves was created by the first slice, which the accepted change list told it
 * to do, so there is no state of this branch in which the test could fail first:
 * that is the plan defect recorded at record 10 of this ticket's journal, and the
 * honest answer to it is to record the pass as part of the green rather than to
 * drop an index and manufacture a red.
 */
import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import { ERASURE_REGISTRY_TABLE, EXTERNALLY_SOURCED_TABLES, TABLE_RELKINDS } from './tables';

// The local Supabase stack's Postgres, the address `pnpm dev:up` prints when it
// starts. Overridden by SEEN_DATABASE_URL so CI or a second stack needs no code
// change; the default is the local development credential the CLI fixes for
// every project and is the only connection string this repository ever spells.
const LOCAL_DEFAULT = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres';
const DATABASE_URL = process.env.SEEN_DATABASE_URL ?? LOCAL_DEFAULT;

/** The tables this test writes to before it can say anything about a key. */
const NEEDED = [
  'tenants',
  'connections',
  'orders',
  'shipments',
  'returns',
  'settlements',
  'settlement_lines',
] as const;

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

/** A connection, or a refusal that says the database is unreachable and that this
 * test therefore proves nothing about idempotent ingest. The two failures have to
 * read differently: a red that fails because Docker is down is not a red. */
async function connect(): Promise<Client> {
  const client = new Client({ connectionString: DATABASE_URL });
  try {
    await client.connect();
  } catch (cause) {
    await client.end().catch(() => undefined);
    throw new Error(
      `No Postgres answering at ${where(DATABASE_URL)}, so this test proves nothing about the ` +
        'upsert key. Start the local stack with `pnpm dev:up`, apply the migrations with ' +
        '`pnpm db:reset`, or point SEEN_DATABASE_URL at another stack. The driver said: ' +
        `${(cause as Error).message}`,
      { cause },
    );
  }
  return client;
}

/** The parent rows one marketplace's externally sourced rows hang from. */
interface Rail {
  connection: string;
  order: string;
  settlement: string;
}

/**
 * One tenant and a rail per marketplace it sells on.
 *
 * A rail per marketplace rather than one set of parents, because part 9 keys a
 * child's `marketplace` to the parent it hangs from: an order is a row of the
 * connection it was read through, and a shipment is a row of its order, so the
 * eBay probe below needs eBay parents rather than the same Bol ones under another
 * name. The assertion the probe makes is unchanged, and it is the same assertion:
 * one tenant's id on Bol says nothing about the same id on eBay.
 */
interface Fixture {
  tenant: string;
  rails: Record<string, Rail>;
}

/** Refuses the erasure registry holding a tombstone for any tenant this file
 * created. Part 8 makes a tombstone permanent on purpose and nothing can remove
 * one, so a fixture that erases its tenant outside a transaction leaves a row in
 * `seen.erased_tenants` on every run, in every database the suite is pointed at.
 * The fixtures here live in a transaction that is rolled back instead, which
 * takes the tombstone with them. This is hygiene and not correctness: every
 * tenant id in this suite is server-generated and never supplied, so no test can
 * collide with a tombstone and the growth can fail nothing.
 */
async function assertNoTombstones(client: Client, tenants: (string | undefined)[]): Promise<void> {
  const created = tenants.filter((id): id is string => Boolean(id));
  if (created.length === 0) return;
  const { rows } = await client.query<{ tenant_id: string }>(
    `select tenant_id from ${ERASURE_REGISTRY_TABLE} where tenant_id = any($1)`,
    [created],
  );
  expect(
    rows.map((row) => row.tenant_id),
    'Tenants this file created are tombstoned in the erasure registry, so its fixtures erased ' +
      'them outside a transaction and nothing can take those rows back',
  ).toEqual([]);
}

describe('the upsert key on every externally sourced table', () => {
  let client: Client;
  let a: Fixture;
  let b: Fixture;

  /** The marketplaces this file writes rows for, each with parents of its own. */
  const RAILS = ['bol', 'ebay'] as const;

  /** One tenant with the parent rows the five tables hang from, on each marketplace
   * it sells through, as the owner role. */
  async function seed(name: string, slug: string): Promise<Fixture> {
    const tenant = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    const tenantId = tenant.rows[0].tenant_id;
    const rails: Record<string, Rail> = {};
    for (const marketplace of RAILS) {
      const connection = await client.query<{ id: string }>(
        `insert into public.connections (tenant_id, marketplace, country, status)
         values ($1, $2, 'NL', 'active') returning id`,
        [tenantId, marketplace],
      );
      const order = await client.query<{ id: string }>(
        `insert into public.orders (tenant_id, connection_id, marketplace, external_id)
         values ($1, $2, $3, $4) returning id`,
        [tenantId, connection.rows[0].id, marketplace, `${slug}-${marketplace}-order`],
      );
      const settlement = await client.query<{ id: string }>(
        `insert into public.settlements (tenant_id, connection_id, marketplace, external_id)
         values ($1, $2, $3, $4) returning id`,
        [tenantId, connection.rows[0].id, marketplace, `${slug}-${marketplace}-settlement`],
      );
      rails[marketplace] = {
        connection: connection.rows[0].id,
        order: order.rows[0].id,
        settlement: settlement.rows[0].id,
      };
    }
    return { tenant: tenantId, rails };
  }

  /** One row of `table` keyed to this tenant, marketplace and external id, with
   * the parents it cannot exist without and nothing else. */
  async function insert(
    table: (typeof EXTERNALLY_SOURCED_TABLES)[number],
    fixture: Fixture,
    marketplace: string,
    externalId: string,
  ): Promise<void> {
    const keyed = [fixture.tenant, marketplace, externalId];
    const rail = fixture.rails[marketplace];
    if (rail === undefined) {
      throw new Error(
        `This fixture has no ${marketplace} parents for a row of ${table} to hang from, so the ` +
          'probe would measure a missing connection rather than the upsert key. Add the ' +
          'marketplace to RAILS.',
      );
    }
    switch (table) {
      case 'orders':
        await client.query(
          `insert into public.orders (tenant_id, marketplace, external_id, connection_id)
           values ($1, $2, $3, $4)`,
          [...keyed, rail.connection],
        );
        return;
      case 'shipments':
        await client.query(
          `insert into public.shipments (tenant_id, marketplace, external_id, order_id)
           values ($1, $2, $3, $4)`,
          [...keyed, rail.order],
        );
        return;
      case 'returns':
        await client.query(
          `insert into public.returns (tenant_id, marketplace, external_id, order_id)
           values ($1, $2, $3, $4)`,
          [...keyed, rail.order],
        );
        return;
      case 'settlements':
        await client.query(
          `insert into public.settlements (tenant_id, marketplace, external_id, connection_id)
           values ($1, $2, $3, $4)`,
          [...keyed, rail.connection],
        );
        return;
      case 'settlement_lines':
        await client.query(
          `insert into public.settlement_lines
             (tenant_id, marketplace, external_id, settlement_id, line_type, amount_cents)
           values ($1, $2, $3, $4, 'commission', -1250)`,
          [...keyed, rail.settlement],
        );
        return;
      default:
        throw new Error(`No fixture knows how to write a row of ${table}`);
    }
  }

  /** Every write here is rolled back: the fixtures are the only rows that stay.
   * To a savepoint rather than in a transaction of its own, because the fixtures
   * are themselves held in one that stays open for the whole file, and a plain
   * `rollback` would take them with it. */
  async function rolledBack<T>(body: () => Promise<T>): Promise<T> {
    await client.query('savepoint probe');
    try {
      return await body();
    } finally {
      await client.query('rollback to savepoint probe');
      await client.query('release savepoint probe');
    }
  }

  /** The SQLSTATE the database answered with, or `accepted` when it did not refuse. */
  async function said(body: () => Promise<void>): Promise<string> {
    try {
      await body();
      return 'accepted';
    } catch (error) {
      return (error as { code?: string }).code ?? (error as Error).message;
    }
  }

  beforeAll(async () => {
    client = await connect();
    // On both relation families, and it is worth saying what that does and does
    // not buy, because it is not the gap F36 closed in `rls.test.ts`. This is an
    // existence gate over five named tables, not a catalogue-driven inventory: its
    // failure mode is a loud refusal to run, never a pass. What widening answers is
    // the day one of these five is partitioned by date, which `orders` and
    // `settlement_lines` are the obvious candidates for: asking for `relkind = 'r'`
    // alone would report a table that plainly exists as missing and send its author
    // to `pnpm db:reset` for a schema that is already applied.
    const { rows } = await client.query<{ name: string }>(
      `select c.relname as name
         from pg_catalog.pg_class c
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = any($2) and c.relname = any($1)`,
      [[...NEEDED], Object.keys(TABLE_RELKINDS)],
    );
    const present = rows.map((row) => row.name);
    const missing = NEEDED.filter((table) => !present.includes(table));
    if (missing.length > 0) {
      throw new Error(
        `This test cannot write a row at all: ${missing.join(', ')} ` +
          `${missing.length === 1 ? 'does' : 'do'} not exist in the public schema, so there is no ` +
          'upsert key to prove anything about. Apply the migrations with `pnpm db:reset`.',
      );
    }
    // The fixtures are written inside a transaction that is never committed, and
    // the whole file runs in it. Deleting them at the end would clean up just as
    // well, but erasing a tenant writes a tombstone into the erasure registry that
    // nothing can remove by design, so a suite that tidies up by erasing its
    // tenants grows that table by a row on every run, in every database it is
    // pointed at. A rollback takes the tombstone back with the rows.
    await client.query('begin');
    a = await seed('Tenant uniqueness A', 'uniq-a');
    b = await seed('Tenant uniqueness B', 'uniq-b');
  });

  afterAll(async () => {
    await client?.query('rollback');
    if (client) await assertNoTombstones(client, [a?.tenant, b?.tenant]);
    await client?.end();
  });

  for (const table of EXTERNALLY_SOURCED_TABLES) {
    it(`refuses a second row of the same triple in ${table}`, async () => {
      const answer = await rolledBack(async () => {
        await insert(table, a, 'bol', 'repeated-page');
        return said(() => insert(table, a, 'bol', 'repeated-page'));
      });
      expect(
        answer,
        `A second insert of the same (tenant_id, marketplace, external_id) into ${table} was ` +
          `${answer === 'accepted' ? 'accepted' : `refused with SQLSTATE ${answer}`}, where a ` +
          'unique violation (23505) is what makes reading the same page of a marketplace twice ' +
          'write the row once',
      ).toBe('23505');
    });

    it(`accepts another tenant's row with the same external id in ${table}`, async () => {
      const answer = await rolledBack(async () => {
        await insert(table, a, 'bol', 'shared-across-tenants');
        return said(() => insert(table, b, 'bol', 'shared-across-tenants'));
      });
      expect(
        answer,
        `${table} refused a second tenant the external id the first tenant holds, so the key is ` +
          'not scoped to the tenant and two brands selling on the same marketplace collide',
      ).toBe('accepted');
    });

    it(`accepts the same external id on another marketplace in ${table}`, async () => {
      const answer = await rolledBack(async () => {
        await insert(table, a, 'bol', 'shared-across-marketplaces');
        return said(() => insert(table, a, 'ebay', 'shared-across-marketplaces'));
      });
      expect(
        answer,
        `${table} refused the same external id on a second marketplace, so the key does not carry ` +
          "the marketplace and one marketplace's ids suppress another's",
      ).toBe('accepted');
    });
  }
});
