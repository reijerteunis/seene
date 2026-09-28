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
 *
 * Each catalogue assertion is a named checker taking a schema name rather than a
 * query inside a test, for two reasons. Every one of them answers with the tables
 * that fail it, so it cannot pass by finding nothing when there is nothing to
 * find: the same checker is run against a schema with no tables at all and has to
 * refuse. And the tenancy checker is read by the test that injects a second
 * permissive policy, which is the only way to show that the assertion sees a
 * policy set and not the existence of one policy.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import {
  APPEND_ONLY_PRIVILEGES, APPEND_ONLY_TABLES, BUYER_PII_COLUMNS, BUYER_PII_COMMENT_TERMS,
  CROSS_TENANT_FOREIGN_KEY_EXEMPTIONS, DATA_API_ROLES, FORBIDDEN_PRIVILEGE_STATEMENTS,
  GOVERNED_PRIVILEGES, HASHED_REPOSITORY_DOCUMENTS, MIGRATION_SET_HEADER, MIGRATIONS_DIRECTORY,
  TABLE_PRIVILEGES, TENANCY_CLAUSES, TENANT_CLAIM,
  TRADE_RECORD_MIGRATION_MARKER, TRADE_RECORD_TABLES,
} from './tables';

/** The repository root, from this file's own location: `packages/core/db`. */
const REPOSITORY_ROOT = fileURLToPath(new URL('../../..', import.meta.url));

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

async function tablesIn(client: Client, schema: string): Promise<string[]> {
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = 'r'
      order by c.relname`,
    [schema],
  );
  return rows.map((row) => row.name);
}

/**
 * The guard every catalogue assertion below is made of.
 *
 * Each of them asks the catalogue which tables fail a property and passes when
 * the answer is empty, and an empty schema answers every such question with
 * nothing: the assertion passed against a database with no tables at all at
 * record 8, which is worth nothing at all.
 */
function assertPopulated(tables: string[], what: string): void {
  if (tables.length === 0) {
    throw new Error(
      `There are no tables to assert anything about, so "${what}" proves nothing. Apply the `
      + 'migrations with `pnpm db:reset`, or point SEEN_DATABASE_URL at a stack that has them.',
    );
  }
}

/** The tables in the schema with no `tenant_id` column. */
async function tenantIdGapsIn(client: Client, schema: string): Promise<string[]> {
  const tables = await tablesIn(client, schema);
  assertPopulated(tables, `a tenant_id column on every table in schema ${schema}`);
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = 'r'
        and not exists (
          select 1 from pg_catalog.pg_attribute a
           where a.attrelid = c.oid and a.attname = 'tenant_id'
             and a.attnum > 0 and not a.attisdropped)
      order by c.relname`,
    [schema],
  );
  return rows.map((row) => row.name);
}

/** The tables in the schema without row-level security enabled. */
async function rlsGapsIn(client: Client, schema: string): Promise<string[]> {
  const tables = await tablesIn(client, schema);
  assertPopulated(tables, `row-level security on every table in schema ${schema}`);
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = 'r' and not c.relrowsecurity
      order by c.relname`,
    [schema],
  );
  return rows.map((row) => row.name);
}

interface PolicyRow {
  tablename: string;
  policyname: string;
  cmd: string;
  permissive: string;
  qual: string | null;
  with_check: string | null;
}

async function policiesIn(client: Client, schema: string): Promise<PolicyRow[]> {
  const { rows } = await client.query<PolicyRow>(
    `select tablename, policyname, cmd, permissive, qual, with_check
       from pg_catalog.pg_policies
      where schemaname = $1
      order by tablename, policyname`,
    [schema],
  );
  return rows;
}

/** One clause with its whitespace collapsed, so that a Postgres release which
 * re-renders the same expression with different spacing does not read as a leak. */
function collapsed(clause: string): string {
  return clause.replace(/\s+/g, ' ').trim();
}

/**
 * Every way the schema's policy set fails to bind a table to the one tenancy
 * expression, named one by one.
 */
async function tenancyGapsIn(client: Client, schema: string): Promise<string[]> {
  const tables = await tablesIn(client, schema);
  assertPopulated(tables, `the tenancy expression on every table in schema ${schema}`);
  const rows = await policiesIn(client, schema);
  // The whole policy set per table, not the existence of one policy in it. Row
  // level security ORs permissive policies together, so a second permissive policy
  // widens whatever the first one narrowed, and a table is bound only if every
  // permissive policy on it is. Restrictive policies are ANDed and can only
  // narrow, so they are not asked to name the tenant.
  //
  // Both clauses are read. USING decides which existing rows a command sees, which
  // is what governs select, update and delete; WITH CHECK decides which rows it
  // may leave behind, which is what governs insert and update. A policy that names
  // the tenant in one and allows anything in the other is bound for one half of
  // the commands it covers and open for the other.
  //
  // One helper, `seen.current_tenant()`, rather than the expression copied per
  // table: a policy that spells its own comparison is a policy that can be
  // subtly different from the other twenty-eight.
  //
  // A clause is compared with `TENANCY_CLAUSES` as a whole and not searched for a
  // word in. The first version of this asked whether the clause contained the text
  // `current_tenant`, which is a deny-list of one pattern, and the second Codex
  // review of SEEN-008 walked two clauses past it: `seen.current_tenant() IS NOT
  // NULL`, which shows every tenant's rows to anyone holding any tenant claim, and
  // the tenancy comparison with `OR true` after it. Both read the helper and
  // neither compares anything to it. There is always another expression, so the
  // question asked is the one that has a finite answer: is this clause one of the
  // clauses the schema is allowed to carry. Anything else is a gap, including a
  // clause that narrows further and is perfectly safe, which costs its author a
  // line in that list and a reviewer's eye on it.
  const recognised = new Set(TENANCY_CLAUSES.map(collapsed));
  const gaps: string[] = [];
  for (const table of tables) {
    const permissive = rows.filter(
      (row) => row.tablename === table && row.permissive === 'PERMISSIVE',
    );
    if (permissive.length === 0) {
      gaps.push(`${table}: no permissive policy at all`);
      continue;
    }
    for (const policy of permissive) {
      const clauses: [string, string | null][] = [
        ['using', policy.qual], ['with check', policy.with_check],
      ];
      const written = clauses.filter(([, clause]) => clause !== null);
      if (written.length === 0) {
        gaps.push(`${table}.${policy.policyname} (${policy.cmd}): no clause at all`);
        continue;
      }
      for (const [name, clause] of written) {
        if (!recognised.has(collapsed(clause ?? ''))) {
          gaps.push(
            `${table}.${policy.policyname} (${policy.cmd}): its ${name} clause is not one of the `
            + `tenancy expressions this schema binds a table with, it reads ${clause}`,
          );
        }
      }
    }
  }
  return gaps;
}

/** The privileges each Data API role holds on each table, from the table's own
 * access control list, which is the only place the answer is complete: a default
 * privilege granted at schema level and a grant written in a migration both land
 * here, and a blanket `grant on all tables` that undid an earlier revoke is
 * visible here and nowhere in the migration that wrote it. */
async function privilegesIn(
  client: Client,
  schema: string,
): Promise<Map<string, string[]>> {
  const { rows } = await client.query<{ table_name: string; role: string; privilege: string }>(
    `select c.relname as table_name,
            a.grantee::regrole::text as role,
            a.privilege_type as privilege
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
       cross join lateral aclexplode(c.relacl) a
      where n.nspname = $1 and c.relkind = 'r'
        and a.grantee::regrole::text = any($2)`,
    [schema, [...DATA_API_ROLES]],
  );
  const held = new Map<string, string[]>();
  for (const row of rows) {
    if (!(GOVERNED_PRIVILEGES as readonly string[]).includes(row.privilege)) continue;
    const key = `${row.table_name}|${row.role}`;
    held.set(key, [...(held.get(key) ?? []), row.privilege].sort());
  }
  return held;
}

/** Every migration file, as a path relative to the repository root, newest last. */
function migrationFiles(): string[] {
  const directory = join(REPOSITORY_ROOT, MIGRATIONS_DIRECTORY);
  if (!existsSync(directory)) {
    throw new Error(
      `There is no ${MIGRATIONS_DIRECTORY} directory under ${REPOSITORY_ROOT}, so a test that `
      + 'reads the migrations proves nothing. This test resolves the repository root from its own '
      + 'location and that assumption has broken.',
    );
  }
  const files = readdirSync(directory).filter((name) => name.endsWith('.sql')).sort();
  if (files.length === 0) {
    throw new Error(
      `There are no .sql files in ${MIGRATIONS_DIRECTORY}, so a test that reads the migrations `
      + 'proves nothing.',
    );
  }
  return files.map((name) => `${MIGRATIONS_DIRECTORY}/${name}`);
}

/**
 * The statements of a migration, with its comments removed.
 *
 * The comments have to go before anything is matched in them: part 4 of the trade
 * record quotes the blanket grant it forbids, twice, in order to say what it is
 * undoing, and a scanner that could not tell a quotation from a statement would
 * either fail on the file that fixed the problem or be written loosely enough to
 * miss the statement itself.
 */
function statementsOf(sql: string): string[] {
  const withoutComments = sql
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/--[^\n]*/g, ' ');
  return withoutComments.split(';').map((statement) => statement.trim()).filter(Boolean);
}

/** One member of the trade record v1 migration set: its path and its first line. */
interface SetMember { file: string; firstLine: string }

/**
 * The members of the trade record v1 set whose header misstates the size of the
 * set, or states no part number at all, given every member's first line in
 * migration order.
 *
 * Pure over the members it is handed, so that the test below can show it a set of
 * five, which the four files on disk cannot demonstrate: the size it compares
 * against is the number of members it was given and never a literal, so a fifth
 * migration is added by numbering it and correcting the four in front of it, not by
 * editing this test.
 */
function misnumberedSetHeaders(members: readonly SetMember[]): string[] {
  const size = members.length;
  const offenders: string[] = [];
  members.forEach((member, index) => {
    const stated = MIGRATION_SET_HEADER.exec(member.firstLine);
    if (stated === null) {
      offenders.push(
        `${member.file}: its first line states no part number, and the set has ${size} files`,
      );
      return;
    }
    const [, part, total] = stated;
    if (Number(total) !== size) {
      offenders.push(
        `${member.file}: its first line says \`part ${part} of ${total}\`, and the set has `
        + `${size} files`,
      );
      return;
    }
    if (Number(part) !== index + 1) {
      offenders.push(
        `${member.file}: its first line says \`part ${part} of ${total}\`, and it is file `
        + `${index + 1} of the set in migration order`,
      );
    }
  });
  return offenders;
}

/** Every member of the trade record v1 set with its first line, oldest first. */
function tradeRecordSetHeaders(): SetMember[] {
  const members = migrationFiles()
    .filter((file) => file.includes(TRADE_RECORD_MIGRATION_MARKER));
  if (members.length === 0) {
    throw new Error(
      `No file in ${MIGRATIONS_DIRECTORY} carries \`${TRADE_RECORD_MIGRATION_MARKER}\` in its `
      + 'name, so a test that reads the set\'s headers proves nothing. The migrations of this '
      + 'ticket have been renamed and the marker has not followed them.',
    );
  }
  return members.map((file) => ({
    file,
    firstLine: readFileSync(join(REPOSITORY_ROOT, file), 'utf8').split('\n')[0] ?? '',
  }));
}

/** Every forbidden privilege statement in the migrations, named with its file. */
function blanketPrivilegeStatements(): string[] {
  const found: string[] = [];
  for (const file of migrationFiles()) {
    const statements = statementsOf(readFileSync(join(REPOSITORY_ROOT, file), 'utf8'));
    for (const statement of statements) {
      for (const forbidden of FORBIDDEN_PRIVILEGE_STATEMENTS) {
        if (forbidden.pattern.test(statement)) {
          found.push(`${file}: ${forbidden.name}, as \`${statement.replace(/\s+/g, ' ')}\``);
        }
      }
    }
  }
  return found;
}

/**
 * The files turbo hashes to decide whether `@seen/core#test` may be replayed from
 * the cache, measured from turbo itself rather than read out of `turbo.json`.
 *
 * `--dry=json` computes the hash and its input list without running the task, so
 * this is the same question the cache asks, asked from inside the suite the cache
 * would be replaying. Reading the configuration instead would assert what somebody
 * wrote, not what turbo resolved: a root-relative glob that turbo silently ignored
 * would read as a fix and hash nothing.
 */
function testTaskInputs(): string[] {
  const turbo = join(REPOSITORY_ROOT, 'node_modules', '.bin', 'turbo');
  if (!existsSync(turbo)) {
    throw new Error(
      `No turbo binary at ${turbo}, so this test cannot measure what the test task hashes and `
      + 'proves nothing about the cache. Install the workspace with `pnpm install`.',
    );
  }
  let output: string;
  try {
    output = execFileSync(
      turbo,
      ['run', 'test', '--filter=@seen/core', '--dry=json'],
      { cwd: REPOSITORY_ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
    );
  } catch (cause) {
    throw new Error(
      'turbo could not report what the test task hashes, so this test proves nothing about the '
      + `cache. turbo said: ${(cause as Error).message}`,
      { cause },
    );
  }
  const plan = JSON.parse(output.slice(output.indexOf('{'))) as {
    tasks?: { taskId?: string; inputs?: Record<string, string> }[];
  };
  const task = (plan.tasks ?? []).find((entry) => entry.taskId === '@seen/core#test');
  if (!task) {
    throw new Error(
      'turbo reported no @seen/core#test task at all, so this test proves nothing about the '
      + `cache. It reported: ${(plan.tasks ?? []).map((entry) => entry.taskId).join(', ')}`,
    );
  }
  return Object.keys(task.inputs ?? {});
}

describe('the trade record schema', () => {
  let client: Client;
  let present: string[];

  beforeAll(async () => {
    client = await connect();
    present = await tablesIn(client, 'public');
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
    const without = await tenantIdGapsIn(client, 'public');
    expect(without, `Tables in the public schema without a tenant_id column: ${without.join(', ')}`)
      .toEqual([]);
  });

  it('has row-level security enabled on every table in the public schema', async () => {
    const without = await rlsGapsIn(client, 'public');
    expect(without, `Tables in the public schema without RLS enabled: ${without.join(', ')}`)
      .toEqual([]);
  });

  it('binds every table to the one tenancy expression', async () => {
    const unbound = await tenancyGapsIn(client, 'public');
    expect(
      unbound,
      `Policies in the public schema that do not bind the tenant: ${unbound.join('; ')}`,
    ).toEqual([]);
  });

  it('proves nothing against a schema with no tables, and says so', async () => {
    // Every assertion above is of the shape "the tables failing this property are
    // none", and a schema with no tables satisfies all of them. Record 8 observed
    // exactly that: the RLS assertion passed against an empty database. A checker
    // that cannot tell the two apart is not an assertion.
    await client.query('begin');
    try {
      await client.query('create schema seen_vacuity_probe');
      await expect(
        rlsGapsIn(client, 'seen_vacuity_probe'),
        'the RLS assertion passes against a schema with no tables',
      ).rejects.toThrow(/proves nothing/);
      await expect(
        tenantIdGapsIn(client, 'seen_vacuity_probe'),
        'the tenant_id assertion passes against a schema with no tables',
      ).rejects.toThrow(/proves nothing/);
      await expect(
        tenancyGapsIn(client, 'seen_vacuity_probe'),
        'the tenancy assertion passes against a schema with no tables',
      ).rejects.toThrow(/proves nothing/);
    } finally {
      await client.query('rollback');
    }
  });

  it('sees a second permissive policy added beside tenant_isolation', async () => {
    // Row-level security ORs permissive policies together, so a policy added
    // beside tenant_isolation widens what tenant_isolation narrowed: this one
    // would hand every tenant's buyer_name and buyer_address to every signed-in
    // user of every other tenant. An assertion that asks whether any one policy
    // on the table reads the tenant cannot see it.
    await client.query('begin');
    try {
      await client.query(
        'create policy leak on public.evidence for select to authenticated using (true)',
      );
      const gaps = await tenancyGapsIn(client, 'public');
      expect(
        gaps.filter((gap) => gap.startsWith('evidence')),
        'A second permissive policy on public.evidence reading `using (true)` exposes every '
        + "tenant's evidence, and the tenancy assertion reported "
        + `${gaps.length === 0 ? 'nothing at all' : gaps.join('; ')}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });

  it('reads the with_check clause of a policy as well as the using clause', async () => {
    // A policy with no USING clause has nothing for the previous assertion to
    // read, so a write policy that checks nothing is invisible to it.
    await client.query('begin');
    try {
      await client.query(
        'create policy leak_write on public.evidence for insert to authenticated with check (true)',
      );
      const gaps = await tenancyGapsIn(client, 'public');
      expect(
        gaps.filter((gap) => gap.startsWith('evidence')),
        'A permissive insert policy on public.evidence with `with check (true)` lets a tenant '
        + 'write a row belonging to another tenant, and the tenancy assertion reported '
        + `${gaps.length === 0 ? 'nothing at all' : gaps.join('; ')}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });

  it('names a clause that does not compare the tenant, however the clause is spelled', async () => {
    // The two tests above show a clause of `true` being caught. `true` is the
    // spelling nobody writes. The second Codex review of SEEN-008 (CODEX-02) ran
    // the checker in memory against catalogue rows and found two clauses it
    // accepted: `seen.current_tenant() IS NOT NULL`, which asks only whether the
    // caller has a tenant and then shows them every tenant's rows, and the tenancy
    // comparison with `OR true` after it, which names the tenant and discards the
    // comparison. Both contain the text `current_tenant`, which was the whole of
    // the test, and the first of them on `public.evidence` hands every tenant's
    // buyer name and buyer address to any signed-in user of any other tenant.
    //
    // Each is written here as the clause an author would actually type, not as the
    // text the catalogue renders back, so what is exercised is the route a policy
    // takes from a migration into `pg_policies`. The with-check case is here as
    // well because that half of a policy cannot be exercised by reading at all:
    // `authenticated` holds no insert privilege, so no cross-tenant write probe can
    // reach the clause and this assertion is the only thing that reads it.
    const leaking = [
      { cmd: 'select', clause: 'using (seen.current_tenant() is not null)' },
      { cmd: 'select', clause: 'using (tenant_id = seen.current_tenant() or true)' },
      { cmd: 'insert', clause: 'with check (tenant_id = seen.current_tenant() or true)' },
      { cmd: 'select', clause: 'using (true)' },
    ];
    const accepted: string[] = [];
    for (const { cmd, clause } of leaking) {
      await client.query('begin');
      try {
        await client.query(
          `create policy leak_spelling on public.evidence for ${cmd} to authenticated ${clause}`,
        );
        const gaps = await tenancyGapsIn(client, 'public');
        if (gaps.filter((gap) => gap.startsWith('evidence')).length === 0) {
          accepted.push(`for ${cmd} ${clause}`);
        }
      } finally {
        await client.query('rollback');
      }
    }
    expect(
      accepted,
      `${accepted.length} of the ${leaking.length} permissive policies on public.evidence that `
      + 'expose every tenant\'s rows were reported as binding the tenant, so the assertion reads '
      + 'the clause for a word rather than for a comparison: ' + accepted.join('; '),
    ).toEqual([]);
  });

  it('grants each Data API role exactly what it is meant to hold, on every table', async () => {
    // The privilege half of the tenancy boundary, on all twenty-nine tables
    // rather than on audit_events alone. A policy decides which rows a role
    // reaches; the privilege decides whether it reaches the table at all, and the
    // second question was asked of one table out of twenty-nine.
    const held = await privilegesIn(client, 'public');
    assertPopulated(present, 'the privileges every Data API role holds on every table');
    const wrong: string[] = [];
    for (const table of present) {
      const expected = (APPEND_ONLY_TABLES as readonly string[]).includes(table)
        ? APPEND_ONLY_PRIVILEGES
        : TABLE_PRIVILEGES;
      for (const role of DATA_API_ROLES) {
        const actual = held.get(`${table}|${role}`) ?? [];
        const intended = [...expected[role]].sort();
        if (actual.join(',') !== intended.join(',')) {
          wrong.push(
            `${table}: ${role} holds ${actual.join('+') || 'nothing'}, `
            + `not ${intended.join('+') || 'nothing'}`,
          );
        }
      }
    }
    expect(
      wrong,
      `${wrong.length} table and role pairs hold privileges the trade record does not intend: `
      + wrong.join('; '),
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

  it('says in each buyer PII column which encryption at rest it relies on, and what is owed',
    async () => {
      // The six columns are plain `text`. CLAUDE.md says buyer PII is encrypted at
      // rest, and that sentence reads two ways: the volume the provider encrypts,
      // or the column itself, so that a restore-drill `pg_dump` and a support query
      // as service_role yield ciphertext rather than every tenant's buyer names and
      // addresses. This schema relies on the first and implements none of the
      // second. Nothing recorded which reading was in force, and an obligation
      // nobody has written down is one that disappears: the comment states it and
      // this test is what keeps the statement there.
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
      assertPopulated(rows.map((row) => row.column), 'what each buyer PII column says is owed');
      const silent: string[] = [];
      for (const row of rows) {
        const comment = row.comment ?? '';
        const unsaid = BUYER_PII_COMMENT_TERMS.filter((term) => !comment.includes(term));
        if (unsaid.length > 0) {
          silent.push(`${row.column} does not say ${unsaid.map((term) => `"${term}"`).join(', ')}`);
        }
      }
      expect(
        silent,
        'Buyer PII columns whose comment does not state which encryption at rest the schema '
        + 'relies on today and what is still owed and by whom: ' + silent.join('; '),
      ).toEqual([]);
    });
});

describe('the migrations that write the schema', () => {
  // Three properties of the migrations as files rather than of the database they
  // produce, because each is about what the next migration will do. The end state
  // after `pnpm db:reset` is correct in each case; what is wrong is what an author
  // reading these files, or a cache reading their hash, would conclude.

  it('hashes every migration into the test task, so the cache cannot replay a stale pass',
    () => {
      // These are the only database-dependent tests in the repository, and they sit
      // in a turbo task whose inputs are the files of one package. A migration that
      // adds a table with no tenant_id, or one born writable by `authenticated`,
      // changes nothing under packages/core, so `turbo run test` reports the old
      // pass from the cache and the tenancy, privilege and append-only guards never
      // see the new schema at all. CI escapes it today only because it caches the
      // pnpm store and not `.turbo`.
      const inputs = testTaskInputs();
      expect(inputs.length, 'turbo reported no inputs at all for @seen/core#test').toBeGreaterThan(0);
      const migrations = migrationFiles().map((file) => file.split('/').pop() as string);
      const hashed = migrations.filter(
        (name) => inputs.some((input) => input.includes(MIGRATIONS_DIRECTORY) && input.endsWith(name)),
      );
      expect(
        migrations.filter((name) => !hashed.includes(name)),
        `The cache key of @seen/core#test covers ${inputs.length} files and `
        + `${hashed.length} of ${migrations.length} migrations, so a turbo cache hit can report `
        + 'these database tests as passed without ever running them against a changed schema. '
        + `turbo hashes: ${inputs.join(', ')}`,
      ).toEqual([]);
    });

  it('hashes the documents the suite reads as an authority, not the migrations alone',
    () => {
      // The same hole as the migrations, in the other direction. `marketplaces.test.ts`
      // parses the routing table of docs/architecture.md and compares it cell by
      // cell with the seeded catalogue, and the document is the authority in that
      // comparison: change Amazon's ingest-orders cell from `API` to `assisted` and
      // the seed is wrong and the test has to say so. Nothing under packages/core
      // changes when the document does, so turbo replays the recorded pass and the
      // comparison never runs. Measured by the second Codex review: sixteen inputs,
      // every migration among them and no document at all.
      const inputs = testTaskInputs();
      expect(inputs.length, 'turbo reported no inputs at all for @seen/core#test').toBeGreaterThan(0);
      const unhashed = HASHED_REPOSITORY_DOCUMENTS.filter(
        (document) => !inputs.some((input) => input.replace(/\\/g, '/').endsWith(document)),
      );
      expect(
        unhashed,
        `The cache key of @seen/core#test covers ${inputs.length} files and none of these, which `
        + 'this suite reads from outside its own package and compares the database against, so a '
        + 'turbo cache hit can report the comparison as passed against a document it never read: '
        + `${unhashed.join(', ')}. turbo hashes: ${inputs.join(', ')}`,
      ).toEqual([]);
    });

  it('counts its own set in every header, so the route to part 4 is not a wrong number', () => {
    // The round that removed the blanket tails rewrote parts 1, 2 and 3 to point at
    // part 4 while their first lines still read `part 1 of 3`, `part 2 of 3` and
    // `part 3 of 3`, so each file contradicts itself about how many migrations the
    // set has. It is not a typo: part 3's tail says it grants no table privilege
    // because part 4 decides them per table, and an author who believes line 1 stops
    // at part 3, never reads that boundary or its self-check, and leaves the default
    // ACL standing on the table they have just created.
    const members = tradeRecordSetHeaders();
    const offenders = misnumberedSetHeaders(members);
    expect(
      offenders,
      `${offenders.length} of the ${members.length} migrations in the trade record v1 set state `
      + 'a size for it that the directory contradicts, so the file that decides every table\'s '
      + 'privileges is outside the set its own parts count: ' + offenders.join('; '),
    ).toEqual([]);
  });

  it('would number a fifth migration without this test being rewritten', () => {
    // The obvious assertion hard-codes four and fails the moment a fifth part is
    // added, which punishes the next author for doing the right thing. The size is
    // the number of members found on disk, so the checker is shown a set of five to
    // prove that: five headers that count five pass, and the same five still reading
    // `of 4` are all named. A file in the directory that is not of this set, the
    // evidence bucket today, is not counted and needs no header.
    const five = (total: number): SetMember[] => [1, 2, 3, 4, 5].map((part) => ({
      file: `${MIGRATIONS_DIRECTORY}/2027_${TRADE_RECORD_MIGRATION_MARKER}_part${part}.sql`,
      firstLine: `-- Trade record v1, part ${part} of ${total}: a table this ticket does not have.`,
    }));
    expect(
      misnumberedSetHeaders(five(5)),
      'A fifth migration that states the size of the set it joined is reported as an offender, '
      + 'so the assertion counts something other than the files it was given',
    ).toEqual([]);
    expect(
      misnumberedSetHeaders(five(4)).length,
      'Five migrations all still stating four are not all reported, so the assertion passes by '
      + 'finding nothing rather than by reading the headers',
    ).toBe(5);
    // And the numbering is read as well as the count: part 3 twice and no part 2 is
    // the drift a copied header produces, and it names the file that is out of order.
    const duplicated = five(5).map(
      (member, index) => (index === 1 ? { ...member, firstLine: member.firstLine.replace('part 2 of 5', 'part 3 of 5') } : member),
    );
    expect(
      misnumberedSetHeaders(duplicated).length,
      'A header copied from the part before it, numbering the set 1, 3, 3, 4, 5, is not reported',
    ).toBe(1);
  });

  it('contains no blanket grant, so the next migration has no such tail to copy', () => {
    // Parts 1, 2 and 3 each ended with `grant ... on all tables in schema public`,
    // the statement part 4's own comment forbids any later migration from writing,
    // and each one silently re-granted update and delete on audit_events to the
    // roles the part before it had just revoked them from. Part 4 runs last and
    // revokes per table, so the end state was right; the residual is that those
    // three tails are the template the next author reads, and part 4's self-check
    // does not re-run to catch the copy.
    const found = blanketPrivilegeStatements();
    expect(
      found,
      `${found.length} blanket privilege statements in the migrations, each of which reaches `
      + 'every table in the schema including the ones an earlier migration narrowed: '
      + found.join('; '),
    ).toEqual([]);
  });

  it('would see a blanket grant a later migration added, in any of its spellings', () => {
    // The assertion above passes when it finds nothing, and a scanner that matched
    // nothing would pass in exactly the same way. So the detector is shown what it
    // is for, including the two spellings that are not the one that was removed: a
    // grant broken over lines, and a default privilege, which grants on tables that
    // do not exist yet and is how anon held four privileges on all twenty-nine.
    const hazards = [
      'grant select, insert, update, delete on all tables in schema public to authenticated',
      'grant all on all tables in schema public to service_role',
      'grant\n  select\n  on all tables\n  in schema public\n  to anon',
      'alter default privileges in schema public grant all on tables to authenticated',
    ];
    const missed = hazards.filter(
      (hazard) => !FORBIDDEN_PRIVILEGE_STATEMENTS.some((rule) => rule.pattern.test(hazard)),
    );
    expect(missed, `Blanket privilege statements the detector does not see: ${missed.join('; ')}`)
      .toEqual([]);
    // And what it must not flag, or part 4 could not be written at all: a grant per
    // table, a grant on the helper schema, and the quotation of the hazard in a
    // comment that explains why it is forbidden.
    const allowed = [
      "execute format('grant select on public.%I to authenticated', target)",
      'grant usage on schema seen to anon, authenticated, service_role',
      '-- no later migration may end in `grant ... on all tables in schema public`',
    ];
    const misread = allowed.filter((statement) => statementsOf(statement).some(
      (cleaned) => FORBIDDEN_PRIVILEGE_STATEMENTS.some((rule) => rule.pattern.test(cleaned)),
    ));
    expect(misread, `Statements the detector wrongly flags: ${misread.join('; ')}`).toEqual([]);
  });
});

describe('the append-only guarantee on audit_events', () => {
  // What append-only means here, and what it does not. No application role holds
  // the update or delete privilege, no policy permits either command, and a
  // trigger refuses both for every role including the one that owns the table.
  // The single delete the guarantee allows is a tenant's erasure: the audit rows
  // go when the tenant goes, because the PRD promises deletion on request. That
  // delete is a service-role action, because no client-bound role holds delete on
  // public.tenants; SEEN-083 owns it.
  let client: Client;
  let tenant: string | undefined;
  let event: string | undefined;

  beforeAll(async () => {
    client = await connect();
    const present = await tablesIn(client, 'public');
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
    // tenant is already gone, which is only ever true inside that cascade, and
    // only a role holding delete on public.tenants can open it.
    await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
    const { rows } = await client.query(
      'select id from public.audit_events where tenant_id = $1',
      [tenant],
    );
    expect(rows, "the erased tenant's audit events survived the erasure").toEqual([]);
    tenant = undefined;
  });
});

/**
 * CODEX-01: a foreign key that references the parent's id alone lets a child row
 * name a parent belonging to another tenant, and the cascade then carries one
 * tenant's erasure into another tenant's trade record.
 *
 * Row-level security is per row and per table. It has nothing to say about the
 * relationship between two rows, so `orders_connection_id_fkey` written as
 * `references public.connections (id)` accepts any connection in the database
 * beside any `tenant_id`, and `orders_tenant_id_fkey` accepts any tenant beside
 * any connection. Each key is satisfied; the pair of them is a cross-tenant edge,
 * and `on delete cascade` makes it a destructive one.
 *
 * The behavioural half of this guarantee, the insert the database now refuses and
 * the erasure that no longer reaches the other tenant, is in `rls.test.ts`. This
 * block is the catalogue half: it reads every foreign key in the schema rather
 * than the ones this ticket wrote, so the twenty-ninth table added by a later
 * sprint cannot reintroduce the shape without a test naming it.
 */
describe('the foreign keys between tenant-owned tables', () => {
  let client: Client;

  /** Every foreign key joining two tables that carry `tenant_id` without carrying
   * `tenant_id` across the join, named with what it is written as today. */
  async function crossTenantKeys(schema: string): Promise<string[]> {
    const { rows } = await client.query<{
      name: string; child: string; parent: string; definition: string;
    }>(
      `select con.conname as name,
              src.relname as child,
              tgt.relname as parent,
              pg_catalog.pg_get_constraintdef(con.oid) as definition
         from pg_catalog.pg_constraint con
         join pg_catalog.pg_class src on src.oid = con.conrelid
         join pg_catalog.pg_class tgt on tgt.oid = con.confrelid
         join pg_catalog.pg_namespace n on n.oid = src.relnamespace
        where con.contype = 'f' and n.nspname = $1
          and exists (select 1 from pg_catalog.pg_attribute a
                       where a.attrelid = src.oid and a.attname = 'tenant_id'
                         and a.attnum > 0 and not a.attisdropped)
          and exists (select 1 from pg_catalog.pg_attribute a
                       where a.attrelid = tgt.oid and a.attname = 'tenant_id'
                         and a.attnum > 0 and not a.attisdropped)
          and not exists (
            select 1
              from unnest(con.conkey, con.confkey) as pair(child_attnum, parent_attnum)
              join pg_catalog.pg_attribute ca
                on ca.attrelid = src.oid and ca.attnum = pair.child_attnum
              join pg_catalog.pg_attribute pa
                on pa.attrelid = tgt.oid and pa.attnum = pair.parent_attnum
             where ca.attname = 'tenant_id' and pa.attname = 'tenant_id')
        order by src.relname, con.conname`,
      [schema],
    );
    return rows
      .filter((row) => !CROSS_TENANT_FOREIGN_KEY_EXEMPTIONS.includes(row.name))
      .map((row) => `${row.child}.${row.name} -> ${row.parent}: ${row.definition}`);
  }

  /** How many foreign keys there are at all, so an empty answer above is read as
   * a schema with keys that all carry the tenant and not as a schema with none. */
  async function foreignKeyCount(schema: string): Promise<number> {
    const { rows } = await client.query<{ total: string }>(
      `select count(*) as total
         from pg_catalog.pg_constraint con
         join pg_catalog.pg_class src on src.oid = con.conrelid
         join pg_catalog.pg_namespace n on n.oid = src.relnamespace
        where con.contype = 'f' and n.nspname = $1`,
      [schema],
    );
    return Number(rows[0].total);
  }

  beforeAll(async () => {
    client = await connect();
    const present = await tablesIn(client, 'public');
    assertPopulated(present, 'the foreign keys between tenant-owned tables');
  });

  afterAll(async () => {
    await client?.end();
  });

  it('carries tenant_id across every key that joins one tenant-owned table to another',
    async () => {
      const total = await foreignKeyCount('public');
      expect(
        total,
        'The public schema has no foreign keys at all, so an assertion about the tenant they '
        + 'carry proves nothing. Apply the migrations with `pnpm db:reset`.',
      ).toBeGreaterThan(0);
      const offenders = await crossTenantKeys('public');
      expect(
        offenders,
        `${offenders.length} of the ${total} foreign keys in the public schema reference their `
        + 'parent by id alone, so a child row may name a parent belonging to another tenant and '
        + "one tenant's erasure cascades into another tenant's trade record: "
        + offenders.join('; '),
      ).toEqual([]);
    });

  it('would see a key that referenced its parent by id alone', async () => {
    // The assertion above passes when it finds nothing, and finding nothing is
    // also what a query with a mistake in it does. So the shape the fix removed is
    // put back, inside a transaction that is rolled back, and has to be reported.
    await client.query('begin');
    try {
      await client.query(
        `alter table public.orders
           add constraint orders_connection_id_by_id_alone
           foreign key (connection_id) references public.connections (id) on delete cascade`,
      );
      const offenders = await crossTenantKeys('public');
      expect(
        offenders.filter((offender) => offender.includes('orders_connection_id_by_id_alone')),
        'A foreign key from orders to connections written as `references public.connections (id)` '
        + `was not reported, and the assertion found ${offenders.length === 0 ? 'nothing at all' : offenders.join('; ')}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });

  it('blocks no erasure, because a tenant must still be deletable on request', async () => {
    // A composite key is the fix, and `on delete restrict` is the way to write one
    // that makes deletion on request impossible: the cascade from public.tenants
    // reaches the child, the restrict refuses it mid-statement, and the whole
    // erasure rolls back. The PRD promises deletion within 30 days and SEEN-083
    // has to perform it, so no key between tenant-owned tables may restrict.
    const { rows } = await client.query<{ name: string; child: string; definition: string }>(
      `select con.conname as name,
              src.relname as child,
              pg_catalog.pg_get_constraintdef(con.oid) as definition
         from pg_catalog.pg_constraint con
         join pg_catalog.pg_class src on src.oid = con.conrelid
         join pg_catalog.pg_namespace n on n.oid = src.relnamespace
        where con.contype = 'f' and n.nspname = 'public' and con.confdeltype = 'r'
        order by src.relname, con.conname`,
    );
    const restricting = rows.map((row) => `${row.child}.${row.name}: ${row.definition}`);
    expect(
      restricting,
      `${restricting.length} foreign keys refuse a delete of the parent outright, which a `
      + "tenant's erasure is: " + restricting.join('; '),
    ).toEqual([]);
  });
});
