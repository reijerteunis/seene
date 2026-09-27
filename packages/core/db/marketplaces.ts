/**
 * The marketplaces catalogue: the six identifiers, the nine capabilities, and the
 * one rule for reading a cell of the routing table in `docs/architecture.md`.
 *
 * The routing table is the authority on what each marketplace lets the agent do,
 * and the migration seeds it into the catalogue. Two copies of a matrix drift, so
 * nothing here writes the matrix down: what is here is the vocabulary (which
 * identifier a column heading belongs to, which key a row heading becomes) and the
 * parser that turns one cell into the value the catalogue stores.
 * `marketplaces.test.ts` reads the document at test time through `parseRoutingTable`
 * and compares the result against the seeded rows, so an edit to the document fails
 * the test rather than leaving the database quietly behind it.
 *
 * The parser lives here rather than in the test on purpose. A test that carried its
 * own reading of the table would be a second reading, and the two could disagree
 * without anything failing; SEEN-009's capability matrix needs the same reading and
 * should find it rather than write a third.
 *
 * Capabilities are stored as the table states them, one value per capability per
 * marketplace, and never as booleans: `assisted` and `none` are different answers
 * and the claims rail routes on the difference.
 */

/** The identifier every table in the trade record carries in its `marketplace` column. */
export const MARKETPLACE_IDS = [
  'amazon',
  'bol',
  'ebay',
  'kaufland',
  'otto',
  'shopify',
] as const;

export type MarketplaceId = (typeof MARKETPLACE_IDS)[number];

/**
 * The column heading each identifier appears under in the routing table, which is
 * also the name the catalogue is seeded with: one string, not a heading and a
 * display name that could differ.
 */
export const MARKETPLACE_COLUMNS: Record<MarketplaceId, string> = {
  bol: 'Bol',
  amazon: 'Amazon (SP-API)',
  ebay: 'eBay',
  kaufland: 'Kaufland',
  otto: 'Otto',
  shopify: 'Shopify',
};

/**
 * The nine capability rows, in the document's order, each with the row heading it
 * is read from. The key is what the catalogue stores and what a module asks for;
 * the heading is what the document says, so rewording a row in the document fails
 * the test rather than silently dropping a capability.
 */
export const CAPABILITY_ROWS = [
  { key: 'ingest_orders', heading: 'Ingest orders, shipments, returns' },
  { key: 'ingest_settlements', heading: 'Ingest settlements, fees, invoices' },
  { key: 'detect_errors', heading: 'Detect fee errors, lost shipments, return shortfalls' },
  { key: 'file_claims', heading: 'File claims with evidence' },
  { key: 'track_credit', heading: 'Track claim outcome to credit' },
  { key: 'fix_listings', heading: 'Fix listings and content' },
  { key: 'buyer_messages', heading: 'Buyer messages and correspondence' },
  { key: 'competing_offers', heading: 'Competing offers and price changes' },
  { key: 'sponsored_placements', heading: 'Sponsored placements' },
] as const;

export type CapabilityKey = (typeof CAPABILITY_ROWS)[number]['key'];

/**
 * What a cell can say. `api` is the agent acting end to end, `assisted` is the
 * agent preparing and a human submitting in one click, `code` is deterministic
 * work on already ingested data and needs no marketplace capability at all,
 * `none` is out of scope for the MVP, `none found` is research having found no
 * API where one might still exist, and `n/a` is a capability the marketplace is
 * not asked for. The last two are kept apart from `none` because they are
 * different facts: one is an open question and the other is a closed one.
 */
export const CAPABILITY_MODES = ['api', 'assisted', 'code', 'none', 'none found', 'n/a'] as const;

export type CapabilityMode = (typeof CAPABILITY_MODES)[number];

/** One cell of the routing table: the mode, and whatever the cell said after it. */
export interface Capability {
  mode: CapabilityMode;
  detail: string | null;
}

/** The whole matrix, by identifier and then by capability key. */
export type RoutingMatrix = Record<MarketplaceId, Record<CapabilityKey, Capability>>;

// Longest first, so `none found` is not read as `none` with a detail of `found`.
const MODE_PREFIXES: readonly CapabilityMode[] = [
  'none found', 'none', 'assisted', 'api', 'code', 'n/a',
];

/**
 * The cells that do not begin with one of the modes, mapped by hand because there
 * is no rule to derive them from. Shopify's own price is not a competing offer, so
 * the capability is absent and the cell's words are kept as the detail. Anything
 * else unrecognised raises rather than being guessed at, which is what makes a new
 * kind of cell in the document a failure somebody has to answer.
 */
const EXCEPTIONS: Record<string, CapabilityMode> = { 'own price only': 'none' };

/**
 * One cell of the routing table as the catalogue stores it.
 *
 * The rule, in full: the cell begins with one of the modes, and the rest of the
 * cell is the detail, with its wrapping brackets removed when the whole of the
 * rest is one bracketed group and kept verbatim when it is not. So
 * `API (Orders, Reports)` is `api` with `Orders, Reports`, `code on ingested data`
 * is `code` with `on ingested data`, and
 * `API (reimbursement and settlement reports) plus inbound mail` keeps its
 * brackets because the sentence continues past them. A cell that is only a mode
 * has no detail at all.
 */
export function parseCapabilityCell(cell: string): Capability {
  const text = cell.trim();
  const lower = text.toLowerCase();

  const exception = EXCEPTIONS[lower];
  if (exception !== undefined) return { mode: exception, detail: text };

  const mode = MODE_PREFIXES.find(
    (candidate) => lower === candidate
      || lower.startsWith(`${candidate} `)
      || lower.startsWith(`${candidate}(`),
  );
  if (mode === undefined) {
    throw new Error(
      `The routing table cell "${text}" begins with none of the capability modes `
      + `(${CAPABILITY_MODES.join(', ')}) and is not one of the exceptions this parser names. `
      + 'Whoever added it has to say which mode it is in packages/core/db/marketplaces.ts, '
      + 'because the claims rail routes on the mode and cannot route on a sentence.',
    );
  }

  const rest = text.slice(mode.length).trim();
  const bracketed = /^\((.*)\)$/.exec(rest);
  return { mode, detail: rest === '' ? null : (bracketed ? bracketed[1] : rest) };
}

/** The rows of the one markdown table whose first heading is `Capability`. */
function routingRows(markdown: string): string[][] {
  const tables: string[][][] = [];
  let current: string[][] | null = null;
  for (const line of markdown.split('\n')) {
    const trimmed = line.trim();
    if (trimmed.startsWith('|')) {
      const cells = trimmed.split('|').slice(1, -1).map((cell) => cell.trim());
      if (cells.every((cell) => /^:?-{2,}:?$/.test(cell))) continue;
      if (current === null) {
        current = [];
        tables.push(current);
      }
      current.push(cells);
    } else {
      current = null;
    }
  }
  const found = tables.filter((table) => table[0]?.[0] === 'Capability');
  if (found.length !== 1) {
    throw new Error(
      `The document has ${found.length} tables whose first heading is "Capability", so the `
      + 'capability routing table cannot be identified. It is the nine-by-six matrix under '
      + '"Capability routing per marketplace".',
    );
  }
  return found[0];
}

/**
 * The routing table of `docs/architecture.md`, read as the matrix the catalogue is
 * seeded from.
 *
 * Strict on purpose. A column heading that is not one of the six, a row heading
 * that is not one of the nine, a missing row and a cell whose mode cannot be read
 * all raise, naming what changed: this function exists so that editing the
 * document is what fails, rather than the database drifting away from it unseen.
 */
export function parseRoutingTable(markdown: string): RoutingMatrix {
  const rows = routingRows(markdown);
  const headings = rows[0].slice(1);

  const expected = MARKETPLACE_IDS.map((id) => MARKETPLACE_COLUMNS[id]);
  const byHeading = new Map<string, MarketplaceId>(
    MARKETPLACE_IDS.map((id) => [MARKETPLACE_COLUMNS[id], id]),
  );
  const unknown = headings.filter((heading) => !byHeading.has(heading));
  const absent = expected.filter((heading) => !headings.includes(heading));
  if (unknown.length > 0 || absent.length > 0) {
    throw new Error(
      'The routing table\'s marketplace columns are not the six the catalogue knows. '
      + `Columns the catalogue has no identifier for: ${unknown.join(', ') || 'none'}. `
      + `Identifiers with no column: ${absent.join(', ') || 'none'}. Reconcile `
      + 'MARKETPLACE_COLUMNS in packages/core/db/marketplaces.ts with the document, and seed '
      + 'the migration accordingly.',
    );
  }

  const matrix = Object.fromEntries(
    MARKETPLACE_IDS.map((id) => [id, {} as Record<CapabilityKey, Capability>]),
  ) as RoutingMatrix;

  const headingToKey = new Map<string, CapabilityKey>(
    CAPABILITY_ROWS.map((row) => [row.heading, row.key]),
  );
  const seen = new Set<CapabilityKey>();
  for (const row of rows.slice(1)) {
    const key = headingToKey.get(row[0]);
    if (key === undefined) {
      throw new Error(
        `The routing table has a capability row the catalogue does not know: "${row[0]}". `
        + 'Add it to CAPABILITY_ROWS in packages/core/db/marketplaces.ts and seed it, or put '
        + 'the row heading back as it was.',
      );
    }
    seen.add(key);
    headings.forEach((heading, column) => {
      matrix[byHeading.get(heading) as MarketplaceId][key] = parseCapabilityCell(row[column + 1]);
    });
  }

  const missing = CAPABILITY_ROWS.filter((row) => !seen.has(row.key)).map((row) => row.heading);
  if (missing.length > 0) {
    throw new Error(
      `The routing table no longer has ${missing.length} of the nine capability rows: `
      + `${missing.join('; ')}.`,
    );
  }

  return matrix;
}
