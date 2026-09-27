/**
 * Criterion 5: the marketplaces seed contains the six marketplaces with the
 * capabilities of the routing table in `docs/architecture.md`.
 *
 * The matrix is read out of the document at test time, through the one parser in
 * `marketplaces.ts`, and compared against the seeded rows. Nothing in this file
 * writes the matrix down: a test carrying its own copy would compare the copy to
 * itself and pass while the document and the catalogue disagreed, which is the one
 * failure this test exists to prevent. Reword a row, add a marketplace or change a
 * cell in the document and this test fails until the migration is reseeded.
 *
 * It also asserts the two things the seed had to decide. The catalogue is static
 * reference data and `public.marketplaces` is a tenant table, so the seed lives
 * once in `seen.marketplace_catalogue` and is copied per tenant: the first block
 * reads the source, the second reads what a tenant actually sees through its own
 * policy, because a catalogue that exists and is invisible is not seeded. And
 * `connections.marketplace` is bound to the catalogue by a foreign key, which the
 * first two slices left out deliberately because a key before a seed would make
 * ingest depend on seeding order.
 */
import { readFileSync } from 'node:fs';

import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import {
  MARKETPLACE_COLUMNS, MARKETPLACE_IDS, MarketplaceId, parseRoutingTable,
} from './marketplaces';
import { TENANT_CLAIM } from './tables';

// The local Supabase stack's Postgres, the address `pnpm dev:up` prints when it
// starts. Overridden by SEEN_DATABASE_URL so CI or a second stack needs no code
// change; the default is the local development credential the CLI fixes for
// every project and is the only connection string this repository ever spells.
const LOCAL_DEFAULT = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres';
const DATABASE_URL = process.env.SEEN_DATABASE_URL ?? LOCAL_DEFAULT;

/** The document the routing table is the authority in, read from disk per run. */
const ARCHITECTURE = new URL('../../../docs/architecture.md', import.meta.url);

/** The matrix as the document states it today: six marketplaces, nine capabilities. */
const ROUTING = parseRoutingTable(readFileSync(ARCHITECTURE, 'utf8'));

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
 * test therefore proves nothing about the catalogue. The two failures have to read
 * differently: a red that fails because Docker is down is not a red. */
async function connect(): Promise<Client> {
  const client = new Client({ connectionString: DATABASE_URL });
  try {
    await client.connect();
  } catch (cause) {
    await client.end().catch(() => undefined);
    throw new Error(
      `No Postgres answering at ${where(DATABASE_URL)}, so this test proves nothing about the `
      + 'marketplaces catalogue. Start the local stack with `pnpm dev:up`, apply the migrations '
      + 'with `pnpm db:reset`, or point SEEN_DATABASE_URL at another stack. The driver said: '
      + `${(cause as Error).message}`,
      { cause },
    );
  }
  return client;
}

interface CatalogueRow {
  marketplace: string;
  name: string;
  capabilities: Record<string, { mode: string; detail: string | null }>;
}

describe('the static marketplaces catalogue', () => {
  let client: Client;
  let seeded: CatalogueRow[];

  beforeAll(async () => {
    client = await connect();
    const { rows } = await client.query<{ name: string | null }>(
      "select to_regclass('seen.marketplace_catalogue')::text as name",
    );
    if (rows[0].name === null) {
      throw new Error(
        'The static marketplaces catalogue does not exist: seen.marketplace_catalogue is not in '
        + 'the database, so none of the six marketplaces of the routing table and none of their '
        + 'nine capabilities have been seeded. Apply the migrations with `pnpm db:reset`.',
      );
    }
    const found = await client.query<CatalogueRow>(
      'select marketplace, name, capabilities from seen.marketplace_catalogue order by marketplace',
    );
    seeded = found.rows;
  });

  afterAll(async () => {
    await client?.end();
  });

  it('holds the six marketplaces the routing table has a column for', () => {
    const present = seeded.map((row) => row.marketplace);
    expect(
      present,
      `The catalogue holds ${present.length} of the six marketplaces the routing table names: `
      + `${present.join(', ') || 'none at all'}`,
    ).toEqual([...MARKETPLACE_IDS]);
  });

  it("names each marketplace as the routing table's own column heading", () => {
    const named = Object.fromEntries(seeded.map((row) => [row.marketplace, row.name]));
    const expected = Object.fromEntries(
      MARKETPLACE_IDS.map((id) => [id, MARKETPLACE_COLUMNS[id]]),
    );
    expect(named, 'The catalogue names a marketplace something the document does not')
      .toEqual(expected);
  });

  it('stores every capability as the routing table states it, one value per cell', () => {
    // The assertion this file exists for. The left side is the database, the right
    // side is the document parsed a moment ago, and neither is a copy of the other.
    for (const id of MARKETPLACE_IDS) {
      const row = seeded.find((candidate) => candidate.marketplace === id);
      expect(
        row?.capabilities ?? null,
        `The capabilities seeded for ${id} are not what the routing table in `
        + 'docs/architecture.md states. The document is the authority: reseed the catalogue in '
        + 'the commerce and marketplaces migration to match it.',
      ).toEqual(ROUTING[id as MarketplaceId]);
    }
  });

  it('would notice an edit to the document, which is what makes the comparison worth it', () => {
    // The guard on the assertion above. If the matrix were read from anything but
    // the document, or the document were read from anything but disk, every
    // assertion here would pass a copy against itself and say nothing. One cell is
    // changed in a copy of the document held in memory, and the parse of it must
    // disagree with what the database holds.
    const edited = parseRoutingTable(
      readFileSync(ARCHITECTURE, 'utf8').replace(
        '| API (Orders, Reports) |', '| assisted (a case by hand) |',
      ),
    );
    const seededAmazon = seeded.find((row) => row.marketplace === 'amazon')?.capabilities;
    expect(
      edited.amazon.ingest_orders,
      'changing a cell of the routing table did not change what this test reads, so it is not '
      + 'reading the document at all',
    ).not.toEqual(seededAmazon?.ingest_orders);
    expect(edited.amazon.ingest_orders).toEqual({ mode: 'assisted', detail: 'a case by hand' });
  });
});

describe('the catalogue a tenant reads through its own policy', () => {
  // A static catalogue in a tenant table is only seeded if a tenant can see it.
  // Both tenants are created here and read back as `authenticated` with their own
  // claim, the way PostgREST reads for a request.
  let client: Client;
  let first: string | undefined;
  let second: string | undefined;

  /** What `select marketplace from marketplaces` returns for a request carrying
   * these claims, or carrying none at all, read as `authenticated`. */
  async function visible(claims: Record<string, string> | null): Promise<string[]> {
    await client.query('begin');
    try {
      if (claims !== null) {
        await client.query('select set_config($1, $2, true)', [
          'request.jwt.claims', JSON.stringify(claims),
        ]);
      }
      await client.query('set local role authenticated');
      const { rows } = await client.query<{ marketplace: string }>(
        'select marketplace from public.marketplaces order by marketplace',
      );
      return rows.map((row) => row.marketplace);
    } finally {
      await client.query('rollback');
    }
  }

  beforeAll(async () => {
    client = await connect();
    const a = await client.query<{ tenant_id: string }>(
      "insert into public.tenants (name) values ('Tenant catalogue A') returning tenant_id",
    );
    first = a.rows[0].tenant_id;
    const b = await client.query<{ tenant_id: string }>(
      "insert into public.tenants (name) values ('Tenant catalogue B') returning tenant_id",
    );
    second = b.rows[0].tenant_id;
  });

  afterAll(async () => {
    await client.query('delete from public.tenants where tenant_id = any($1)', [
      [first, second].filter(Boolean),
    ]);
    await client?.end();
  });

  it('gives a tenant the whole catalogue, with the capabilities of the document', async () => {
    const mine = await visible({ [TENANT_CLAIM]: first as string });
    expect(
      mine,
      `A tenant reads ${mine.length} of the six marketplaces: ${mine.join(', ') || 'none at all'}. `
      + 'A catalogue that exists and is invisible to the tenant that has to route on it is not '
      + 'seeded.',
    ).toEqual([...MARKETPLACE_IDS]);

    const { rows } = await client.query<CatalogueRow>(
      `select marketplace, name, capabilities from public.marketplaces
        where tenant_id = $1 order by marketplace`,
      [first],
    );
    for (const row of rows) {
      expect(
        row.capabilities,
        `The copy of ${row.marketplace} this tenant holds is not what the routing table states`,
      ).toEqual(ROUTING[row.marketplace as MarketplaceId]);
    }
  });

  it('gives the next tenant the same catalogue, without a migration', async () => {
    const theirs = await visible({ [TENANT_CLAIM]: second as string });
    expect(
      theirs,
      'The second tenant created after the seed reads a different catalogue from the first, so '
      + 'the catalogue reaches a tenant only when a migration runs',
    ).toEqual([...MARKETPLACE_IDS]);
  });

  it('shows the catalogue to no request carrying no claim at all', async () => {
    // The catalogue is public knowledge, but it is held in a tenant table, and a
    // policy permissive on a missing claim is permissive on every other table
    // the loop wrote the same policy onto.
    expect(
      await visible(null),
      'a request with no tenant claim can read the marketplaces table',
    ).toEqual([]);
  });
});

describe('connections are bound to the catalogue', () => {
  let client: Client;
  let tenant: string | undefined;

  /** The SQLSTATE the database answered a connection to this marketplace with, or
   * `accepted` when it did not refuse. The state and not the message: what matters
   * is that the refusal is a foreign key violation, 23503, and a test on the
   * constraint's name would fail the day the key is rewritten as something that
   * keeps the same promise. Every write here is rolled back. */
  async function attempt(marketplace: string): Promise<string> {
    await client.query('begin');
    try {
      await client.query(
        `insert into public.connections (tenant_id, marketplace, country, status)
         values ($1, $2, 'NL', 'pending')`,
        [tenant, marketplace],
      );
      return 'accepted';
    } catch (error) {
      return (error as { code?: string }).code ?? (error as Error).message;
    } finally {
      await client.query('rollback');
    }
  }

  beforeAll(async () => {
    client = await connect();
    const created = await client.query<{ tenant_id: string }>(
      "insert into public.tenants (name) values ('Tenant catalogue key') returning tenant_id",
    );
    tenant = created.rows[0].tenant_id;
  });

  afterAll(async () => {
    if (tenant) await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
    await client?.end();
  });

  it('refuses a connection to a marketplace the catalogue does not hold', async () => {
    const said = await attempt('mercadolibre');
    expect(
      said,
      'connections.marketplace accepts a marketplace that is not in the catalogue, so a typo at '
      + 'ingest opens a connection to a marketplace that does not exist and every row keyed to it '
      + 'is unreachable from the catalogue the modules route on',
    ).not.toBe('accepted');
    expect(
      said,
      `The connection was refused with SQLSTATE ${said}, where a foreign key violation (23503) `
      + 'is what says the refusal came from the catalogue rather than from something else',
    ).toBe('23503');
  });

  it('accepts a connection to a marketplace it does hold', async () => {
    expect(
      await attempt('bol'),
      'the foreign key refuses a marketplace the catalogue holds, so the seed and the key '
      + 'disagree',
    ).toBe('accepted');
  });
});
