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
  BUYER_PII_MARKER, CLIENT_BOUND_ROLES, CROSS_TENANT_FOREIGN_KEY_EXEMPTIONS, DATA_API_ROLES,
  ERASURE_REGISTRY_COLUMNS, ERASURE_REGISTRY_TABLE,
  FORBIDDEN_PRIVILEGE_STATEMENTS, FREE_TEXT_TYPE_NAMES, GOVERNED_PRIVILEGES,
  HASHED_REPOSITORY_DOCUMENTS, MIGRATION_SET_HEADER, MIGRATIONS_DIRECTORY,
  NOT_BUYER_PII_MARKER, ROW_BEARING_RELKINDS,
  TABLE_PRIVILEGES, TENANCY_CLAUSES, TENANT_CLAIM,
  TRADE_RECORD_MIGRATION_MARKER, TRADE_RECORD_TABLES,
  VIEW_SECURITY_OPTION, VIEW_SECURITY_OPTION_TRUE,
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

/** A relation in a schema, with the single character `pg_class` names its kind by. */
interface Relation { name: string; kind: string }

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
 * Every relation in the schema that holds rows and is not an ordinary table,
 * with the kind `pg_class` gives it.
 *
 * `tablesIn` asks for `relkind = 'r'` and every guard in this suite is built on
 * it, which is the whole of the hole the third Codex review of SEEN-008 (F19)
 * found. A view added to `public` by a later migration answers to `'v'`, is born
 * holding the default access control list of schema `public`, which covers views
 * as surely as tables because `pg_default_acl` files both under
 * `defaclobjtype = 'r'`, and is not subject to the row-level security of the
 * tables underneath it unless it was created `with (security_invoker = true)`.
 * So the tenancy guard does not see it, the privilege guard does not see it, and
 * `anon` reads every tenant's rows through it.
 */
async function nonTableRelationsIn(client: Client, schema: string): Promise<Relation[]> {
  const { rows } = await client.query<Relation>(
    `select c.relname as name, c.relkind as kind
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = any($2)
      order by c.relname`,
    [schema, Object.keys(ROW_BEARING_RELKINDS)],
  );
  return rows;
}

/** One such relation, named the way a failure message should name it. */
function named(relation: Relation): string {
  return `${relation.name} (${ROW_BEARING_RELKINDS[relation.kind] ?? `relkind ${relation.kind}`})`;
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

/**
 * Every privilege a client-bound role holds on a relation in the schema that is
 * not an ordinary table, named one by one.
 *
 * The privilege guard above reads `relkind = 'r'` and so measures nothing at all
 * about a view. `anon` and `authenticated` should hold nothing on one: a view
 * that a later ticket deliberately publishes has to grant its own select, and say
 * so in the migration that publishes it.
 */
async function clientPrivilegesOnNonTablesIn(client: Client, schema: string): Promise<string[]> {
  const { rows } = await client.query<{ name: string; kind: string; role: string; privilege: string }>(
    `select c.relname as name, c.relkind as kind,
            a.grantee::regrole::text as role,
            a.privilege_type as privilege
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
       cross join lateral aclexplode(c.relacl) a
      where n.nspname = $1 and c.relkind = any($2)
        and a.grantee::regrole::text = any($3)
      order by c.relname, role, privilege`,
    [schema, Object.keys(ROW_BEARING_RELKINDS), [...CLIENT_BOUND_ROLES]],
  );
  return rows
    .filter((row) => (GOVERNED_PRIVILEGES as readonly string[]).includes(row.privilege))
    .map((row) => `${named(row)}: ${row.role} holds ${row.privilege}`);
}

/**
 * Every view in the schema that does not read its base tables with the caller's
 * own rights and claims.
 *
 * A view without `security_invoker = true` runs as its owner, which here is the
 * migration role, and the row-level security of the tables underneath it is not
 * applied to the request at all. The option is read out of `reloptions` by name
 * rather than matched as a string, because Postgres stores a boolean storage
 * parameter as it was written and `on`, `yes` and `1` are the same setting.
 */
async function viewsWithoutInvokerRightsIn(client: Client, schema: string): Promise<string[]> {
  const { rows } = await client.query<{ name: string; kind: string; setting: string | null }>(
    `select c.relname as name, c.relkind as kind,
            (select o.option_value
               from pg_catalog.pg_options_to_table(c.reloptions) o
              where o.option_name = $2) as setting
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = 'v'
      order by c.relname`,
    [schema, VIEW_SECURITY_OPTION],
  );
  return rows
    .filter((row) => !(VIEW_SECURITY_OPTION_TRUE as readonly string[])
      .includes((row.setting ?? '').toLowerCase()))
    .map((row) => `${named(row)}: ${VIEW_SECURITY_OPTION} is `
      + `${row.setting === null ? 'not set at all' : row.setting}`);
}

/**
 * Every materialised view in the schema.
 *
 * There is no `security_invoker` for one and there could not be. A materialised
 * view is a stored copy of the rows its owner could see when it was refreshed, so
 * a request reading it is reading rows that were selected before the request
 * existed and there is nothing for a policy to be applied to. The rule is
 * therefore not how to create one but where: not in a schema the Data API serves.
 */
async function materialisedViewsIn(client: Client, schema: string): Promise<string[]> {
  const relations = await nonTableRelationsIn(client, schema);
  return relations.filter((relation) => relation.kind === 'm').map(named);
}

/**
 * Every default privilege a client-bound role holds on the relations the
 * migration role creates in the schema, named one by one.
 *
 * `alter default privileges` grants on objects that do not exist yet, and
 * `defaclobjtype = 'r'` is not "table": it is every relation kind a `create
 * table`, `create view`, `create materialized view` or `create foreign table`
 * produces. Supabase ships schema `public` with all of `arwdDxtm` defaulted to
 * `anon` and `authenticated`, so a view a later migration adds is readable by a
 * caller who never signed in before that migration's last line has run.
 *
 * Scoped to the role this session is connected as, which is the role the
 * migrations run as, because a default privilege applies to the objects one role
 * creates and says nothing about another's. The second grantor in this database
 * is `supabase_admin`, and its entry is not asserted here: it governs relations
 * `supabase_admin` itself creates in `public`, no migration in this repository
 * creates one, and the migration role is not a member of `supabase_admin` and
 * cannot revoke it. Part 6 states that as the limit it could not close.
 */
async function defaultPrivilegesForClientRolesIn(
  client: Client, schema: string,
): Promise<string[]> {
  const { rows } = await client.query<{ grantor: string; role: string; privilege: string }>(
    `select d.defaclrole::regrole::text as grantor,
            a.grantee::regrole::text as role,
            a.privilege_type as privilege
       from pg_catalog.pg_default_acl d
       cross join lateral aclexplode(d.defaclacl) a
      where d.defaclnamespace = (select oid from pg_catalog.pg_namespace where nspname = $1)
        and d.defaclobjtype = 'r'
        and d.defaclrole = current_user::regrole
        and a.grantee::regrole::text = any($2)
      order by role, privilege`,
    [schema, [...CLIENT_BOUND_ROLES]],
  );
  return rows.map((row) => `${row.role} holds ${row.privilege} on every relation ${row.grantor} `
    + `creates in ${schema}`);
}

/** One column that can hold a sentence, with the classification its own comment
 * carries, or the empty string when it carries none. */
interface FreeTextColumn { column: string; type: string; comment: string }

/**
 * Every column in the schema that can hold a buyer's name or address, read from
 * the catalogue by type and never by name.
 *
 * The inventory assertions used to ask for `attname like 'buyer%'`, which can
 * only ever return columns already named for the buyer: the set searched for an
 * unlisted column was the set of listed ones, so "no column named for the buyer
 * is missing from the list" was a sentence about itself. Three columns hold a
 * buyer's name and address by their own documented purpose and are spelled
 * otherwise, and F20 is that none of them was ever looked at.
 *
 * So the question asked is the one with a finite answer, as it is for a tenancy
 * clause: every column whose type can hold prose is a candidate, and each has to
 * say which it is. A column nobody classified is the failure, and it names
 * itself.
 */
async function freeTextColumnsIn(client: Client, schema: string): Promise<FreeTextColumn[]> {
  const { rows } = await client.query<FreeTextColumn>(
    `select c.relname || '.' || a.attname as column,
            pg_catalog.format_type(a.atttypid, a.atttypmod) as type,
            coalesce(pg_catalog.col_description(c.oid, a.attnum), '') as comment
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
       join pg_catalog.pg_attribute a on a.attrelid = c.oid
       join pg_catalog.pg_type t on t.oid = a.atttypid
       left join pg_catalog.pg_type e on e.oid = t.typelem
      where n.nspname = $1 and c.relkind in ('r', 'p')
        and a.attnum > 0 and not a.attisdropped
        and (t.typname = any($2) or (t.typcategory = 'A' and e.typname = any($2)))
      order by 1`,
    [schema, [...FREE_TEXT_TYPE_NAMES]],
  );
  return rows;
}

/** The candidates whose comment classifies them neither way, named as a failure
 * message should name them: an unclassified column is the defect, so it carries
 * its type with it and a reader can see what it can hold. */
function unclassified(columns: readonly FreeTextColumn[]): string[] {
  return columns
    .filter((column) => !column.comment.startsWith(BUYER_PII_MARKER)
      && !column.comment.startsWith(NOT_BUYER_PII_MARKER))
    .map((column) => `${column.column} (${column.type})`);
}

/** The candidates the schema itself declares to hold buyer data. */
function declaredBuyerPii(columns: readonly FreeTextColumn[]): FreeTextColumn[] {
  return columns.filter((column) => column.comment.startsWith(BUYER_PII_MARKER));
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

/** Refuses the erasure registry holding a tombstone for any tenant this file
 * created. Part 8 makes a tombstone permanent on purpose and nothing can remove
 * one, so a fixture that erases its tenant outside a transaction leaves a row in
 * `seen.erased_tenants` on every run, in every database the suite is pointed at.
 * The fixtures here live in a transaction that is rolled back instead, which
 * takes the tombstone with them. This is hygiene and not correctness: every
 * tenant id in this suite is server-generated and never supplied, so no test can
 * collide with a tombstone and the growth can fail nothing.
 */
async function assertNoTombstones(
  client: Client,
  tenants: (string | undefined)[],
): Promise<void> {
  const created = tenants.filter((id): id is string => Boolean(id));
  if (created.length === 0) return;
  const { rows } = await client.query<{ tenant_id: string }>(
    `select tenant_id from ${ERASURE_REGISTRY_TABLE} where tenant_id = any($1)`,
    [created],
  );
  expect(
    rows.map((row) => row.tenant_id),
    'Tenants this file created are tombstoned in the erasure registry, so its fixtures erased '
    + 'them outside a transaction and nothing can take those rows back',
  ).toEqual([]);
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

  it('classifies every column that can hold a buyer, so one nobody looked at cannot pass',
    async () => {
      // F20: the inventory below used to be read out of `attname like 'buyer%'`,
      // so the set it searched for an unlisted column was the set of columns
      // already named for the buyer and the guarantee it claimed was circular.
      // Three columns hold a buyer's name and address by their own documented
      // purpose and are spelled otherwise: `claims.claim_text` is the text a
      // marketplace was told, which for a lost parcel is the buyer's name and
      // address; `messages.body` and `message_threads.subject` are where a buyer
      // types their own delivery address.
      //
      // So every column that can hold prose is a candidate and each has to say
      // which it is, the same shape as the tenancy clauses: there is no third
      // answer for a column nobody anticipated, and an author who adds one
      // without saying meets this rather than a silent pass.
      const columns = await freeTextColumnsIn(client, 'public');
      assertPopulated(
        columns.map((column) => column.column),
        'a classification on every column of schema public that can hold a buyer\'s name',
      );
      const unsaid = unclassified(columns);
      expect(
        unsaid,
        `${unsaid.length} of the ${columns.length} columns in schema public that can hold a `
        + 'sentence say neither that they hold buyer data nor why a buyer\'s name and address '
        + 'cannot reach them, so SEEN-083 cannot know which of them it has to expire: '
        + unsaid.join(', '),
      ).toEqual([]);
    });

  it('cannot be answered by reading the column name, whatever the column is called', async () => {
    // What makes the assertion above worth running. A classification read out of
    // the column's name can only find what was already named, so it is measured
    // against columns that hold a buyer and are spelled like nothing on any list,
    // including one that is an array of text rather than text: the type is what
    // decides what a column can hold, not its name and not its shape.
    await client.query('begin');
    try {
      const injected = [
        'recipient_address text',
        'delivery_note text',
        'sender_details jsonb',
        'cc_addresses text[]',
      ];
      for (const column of injected) {
        await client.query(`alter table public.evidence add column ${column}`);
      }
      const unsaid = unclassified(await freeTextColumnsIn(client, 'public'));
      const missed = injected
        .map((column) => `evidence.${column.split(' ')[0]}`)
        .filter((column) => !unsaid.some((entry) => entry.startsWith(`${column} (`)));
      expect(
        missed,
        `${missed.length} columns added to public.evidence that hold a buyer's name or address `
        + 'under a name no list anticipated were not reported as unclassified, so the '
        + `classification is answerable by the column's name after all: ${missed.join(', ')}`,
      ).toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });

  it('names every buyer PII column as PII with the 30-day expiry it owes', async () => {
    // Read in both directions between the list `tables.ts` carries and what the
    // schema itself declares: every column on the list declares itself buyer PII
    // in the catalogue, and every column that so declares itself is on the list.
    // SEEN-083 has to expire this data after 30 days and should find a list, not
    // do a search.
    const columns = await freeTextColumnsIn(client, 'public');
    const found = declaredBuyerPii(columns).map((column) => column.column);
    assertPopulated(found, 'the buyer PII the schema declares');
    const missing = BUYER_PII_COLUMNS.filter((column) => !found.includes(column));
    const unlisted = found.filter(
      (column) => !(BUYER_PII_COLUMNS as readonly string[]).includes(column),
    );
    expect(
      missing,
      'Columns BUYER_PII_COLUMNS lists that the schema does not declare as buyer PII in their '
      + `own comment: ${missing.join(', ')}`,
    ).toEqual([]);
    expect(
      unlisted,
      'Columns the schema declares to hold buyer data that BUYER_PII_COLUMNS does not list, so '
      + `SEEN-083 would not expire them: ${unlisted.join(', ')}`,
    ).toEqual([]);

    const silent = declaredBuyerPii(columns)
      .filter((column) => !column.comment.includes('PII') || !column.comment.includes('30 days'))
      .map((column) => column.column);
    expect(
      silent,
      'Buyer PII columns whose own comment does not say they are PII expiring after 30 days: '
      + silent.join(', '),
    ).toEqual([]);
  });

  it('reports a column that declares itself buyer PII and is on no list', async () => {
    // The other direction of the same circularity. A migration that marks a new
    // column as holding buyer data and stops there has told the catalogue and not
    // the expiry job, and the column it marks need not be spelled `buyer` either.
    await client.query('begin');
    try {
      await client.query('alter table public.evidence add column recipient_address text');
      await client.query(
        `comment on column public.evidence.recipient_address is
           '${BUYER_PII_MARKER}. Where the parcel was sent, as the carrier recorded it.'`,
      );
      const found = declaredBuyerPii(await freeTextColumnsIn(client, 'public'))
        .map((column) => column.column);
      expect(
        found.filter((column) => !(BUYER_PII_COLUMNS as readonly string[]).includes(column)),
        'A new column declaring itself buyer PII in its own comment was not reported as absent '
        + 'from BUYER_PII_COLUMNS, so the inventory reads the schema for a name rather than for '
        + 'what a column says it holds',
      ).toEqual(['evidence.recipient_address']);
    } finally {
      await client.query('rollback');
    }
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
      const rows = declaredBuyerPii(await freeTextColumnsIn(client, 'public'));
      assertPopulated(rows.map((row) => row.column), 'what each buyer PII column says is owed');
      const silent: string[] = [];
      for (const row of rows) {
        const unsaid = BUYER_PII_COMMENT_TERMS.filter((term) => !row.comment.includes(term));
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
      // The spelling that names the grantor, which is the one part 6 had to write
      // in its revoking form and so the one a later author is most likely to copy
      // and turn round. `on tables` in this grammar is not tables: it is every
      // relation kind, views and materialised views among them, which is F19.
      'alter default privileges for role postgres in schema public grant select on tables to anon',
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
      // And the revoking form, which is the only statement that takes a default
      // privilege away and is the whole of part 6's prevention. A rule that
      // refused `alter default privileges` in both directions would have refused
      // the fix for the hazard it was written about.
      'alter default privileges for role postgres in schema public '
      + 'revoke all on tables from anon, authenticated',
      'alter default privileges in schema public revoke select on tables from anon',
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
    // The fixtures are written inside a transaction that is never committed, and
    // the whole describe runs in it, the erasure below included. Deleting them at
    // the end would clean up just as well, but erasing a tenant writes a tombstone
    // into the erasure registry that nothing can remove by design, so a suite that
    // tidies up by erasing its tenants grows that table by a row on every run, in
    // every database it is pointed at. A rollback takes the tombstone back with
    // the rows.
    await client.query('begin');
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
    await client?.query('rollback');
    if (client) await assertNoTombstones(client, [tenant]);
    await client?.end();
  });

  /** One statement, inside a savepoint that is rolled back whatever it answers.
   * The fixtures live in a transaction that stays open for the whole describe, and
   * a refused statement aborts the transaction it was refused in: without the
   * savepoint the first refusal asked for below would take every question after it
   * with it. */
  async function attempted(sql: string, params: unknown[]): Promise<void> {
    await client.query('savepoint attempted');
    try {
      await client.query(sql, params);
    } finally {
      await client.query('rollback to savepoint attempted');
      await client.query('release savepoint attempted');
    }
  }

  it('refuses an update of an audit event, to the owner of the table as well', async () => {
    // The connection is the owner role, which bypasses row-level security and
    // holds every privilege the table grants: if the update is refused here it is
    // refused for everyone SQL can bind.
    await expect(
      attempted("update public.audit_events set actor = 'rewritten' where id = $1", [event]),
    ).rejects.toThrow(/append-only/);
  });

  it('refuses a delete of an audit event, to the owner of the table as well', async () => {
    await expect(
      attempted('delete from public.audit_events where id = $1', [event]),
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
  });
});

/**
 * F23: the one delete the append-only guarantee permits asked whether the tenant
 * row was visible to the caller, not whether it was there.
 *
 * `seen.refuse_audit_mutation()` lets a delete through when `not exists (select 1
 * from public.tenants where tenant_id = old.tenant_id)`, which its own comment
 * calls the erasure cascade and nothing else. The function carried the invoker's
 * rights, so that subquery was evaluated under the caller's row-level security,
 * and `public.tenants` carries one policy bound `to authenticated`. A caller the
 * policy does not name reads no tenant at all, whatever claim it holds, so the
 * branch stood open for every tenant including the caller's own.
 *
 * It was harmless by coincidence rather than by design. The two roles that hold
 * delete on `public.audit_events` today, `service_role` and the owner, both
 * bypass row-level security, so for them an absent row and an invisible one are
 * the same answer. A later migration granting delete to a role a request is bound
 * to would have turned the exception into permission to erase the audit trail one
 * event at a time, and the only thing left standing would have been that the
 * policy set on `public.audit_events` carries no delete policy.
 *
 * So this block writes the migration that would have done it, inside a
 * transaction that is rolled back: the privilege, and the two policies in the one
 * tenancy expression every other table carries. Nothing it grants is over-broad
 * and the caller asks only for its own tenant's event, which is the point. What is
 * asserted is the refusal, with the tenant row standing; and then the erasure,
 * because the branch that permits it has just been rewritten and a fix that closed
 * the hole by closing the cascade would be a worse defect than the one it closes.
 */
describe('the exception the append-only trigger makes, asked by a request-bound role', () => {
  /** The role a later migration would add and grant delete to. No migration
   * creates it: it is made and rolled back inside each test, so the privilege this
   * block reasons about never outlives the transaction that measured it. */
  const PROBE_ROLE = 'seen_f23_request_bound_probe';

  let client: Client;

  /** The SQLSTATE the database answered with, or `accepted` when it did not
   * refuse. Behind a savepoint, because each test carries on asking questions
   * after a refusal and a failed statement otherwise aborts the transaction. */
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

  /** Everything inside, rolled back. Each test starts as the owner, because the
   * fixtures and the grants are a migration's work, and puts on the role it is
   * asking about itself. */
  async function rolledBack<T>(body: () => Promise<T>): Promise<T> {
    await client.query('begin');
    try {
      return await body();
    } finally {
      await client.query('rollback');
    }
  }

  /** How many rows of `relation` carry this tenant id, with whatever role is set. */
  async function rowsFor(relation: string, tenant: string): Promise<number> {
    const { rows } = await client.query<{ total: string }>(
      `select count(*) as total from ${relation} where tenant_id = $1`,
      [tenant],
    );
    return Number(rows[0].total);
  }

  /** A tenant that exists, with one audit event behind it: the pair the exception
   * branch has to tell apart from a tenant that has been erased. */
  async function seedWithAuditEvent(name: string): Promise<{ tenant: string; event: string }> {
    const seeded = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    const tenant = seeded.rows[0].tenant_id;
    const written = await client.query<{ id: string }>(
      `insert into public.audit_events (tenant_id, event_type, actor)
       values ($1, 'test.written_before_the_probe', 'test') returning id`,
      [tenant],
    );
    return { tenant, event: written.rows[0].id };
  }

  /** The later migration, written out. A request-bound role, the delete privilege
   * the finding supposes, and a select and a delete policy in the same tenancy
   * expression the other twenty-nine tables carry, so the role reads and removes
   * its own tenant's rows and nothing else.
   *
   * Select on `public.tenants` is granted too, and deliberately: the trigger's
   * subquery reads that table under the invoker's rights, and a refusal for want
   * of a privilege would prove something other than what this block is about. The
   * role holds the privilege and still sees nothing, because the tenancy policy is
   * bound to `authenticated` and names no other role. That gap between what is
   * there and what is visible is the whole of the defect. */
  async function grantTheDeleteToARequest(): Promise<void> {
    try {
      await client.query(`create role ${PROBE_ROLE} nologin`);
      await client.query(`grant ${PROBE_ROLE} to current_user`);
    } catch (cause) {
      throw new Error(
        'This test cannot say anything about the exception the append-only trigger makes: the '
        + `connection may not create ${PROBE_ROLE}, so there is no role a request could be bound `
        + 'to to ask with. Point SEEN_DATABASE_URL at a stack whose role may create roles. The '
        + `database said: ${(cause as Error).message}`,
        { cause },
      );
    }
    await client.query(`grant usage on schema seen to ${PROBE_ROLE}`);
    await client.query(`grant execute on function seen.current_tenant() to ${PROBE_ROLE}`);
    await client.query(`grant select on public.tenants to ${PROBE_ROLE}`);
    await client.query(`grant select, delete on public.audit_events to ${PROBE_ROLE}`);
    await client.query(
      `create policy f23_probe_select on public.audit_events for select to ${PROBE_ROLE}
         using (tenant_id = seen.current_tenant())`,
    );
    await client.query(
      `create policy f23_probe_delete on public.audit_events for delete to ${PROBE_ROLE}
         using (tenant_id = seen.current_tenant())`,
    );
  }

  beforeAll(async () => {
    client = await connect();
    const present = await tablesIn(client, 'public');
    const missing = ['tenants', 'audit_events'].filter((table) => !present.includes(table));
    if (missing.length > 0) {
      throw new Error(
        'This test cannot say anything about the one delete the append-only guarantee permits: '
        + `${missing.join(', ')} ${missing.length === 1 ? 'does' : 'do'} not exist in the public `
        + 'schema. Apply the trade record migrations with `pnpm db:reset`.',
      );
    }
  });

  afterAll(async () => {
    await client?.end();
  });

  it('refuses the delete of an audit event whose tenant row is there', async () => {
    const measured = await rolledBack(async () => {
      const { tenant, event } = await seedWithAuditEvent('Tenant a request can reach');
      await grantTheDeleteToARequest();
      await client.query(
        "select set_config('request.jwt.claims', json_build_object('tenant_id', $1::text)::text,"
        + ' true)',
        [tenant],
      );
      await client.query(`set local role ${PROBE_ROLE}`);
      const seenByTheCaller = await rowsFor('public.tenants', tenant);
      const deleted = await said(() => client.query(
        'delete from public.audit_events where id = $1',
        [event],
      ));
      await client.query('reset role');
      return {
        tenantRowsTheCallerCouldSee: seenByTheCaller,
        tenantRowsThereReally: await rowsFor('public.tenants', tenant),
        deleted,
        auditEventsLeft: await rowsFor('public.audit_events', tenant),
      };
    });
    expect(
      measured,
      'A role a request can be bound to asked to delete an audit event of a tenant that is '
      + `there, carrying that tenant's own claim, and the database answered ${measured.deleted}, `
      + `leaving ${measured.auditEventsLeft} audit events. The caller could see `
      + `${measured.tenantRowsTheCallerCouldSee} of the ${measured.tenantRowsThereReally} tenant `
      + 'rows that exist, so an exception branch that reads invisibility as absence hands it the '
      + 'audit trail it is held accountable by, one event at a time. A refusal (23001) is what '
      + 'keeps the exception the one delete it says it is',
    ).toEqual({
      tenantRowsTheCallerCouldSee: 0,
      tenantRowsThereReally: 1,
      deleted: '23001',
      auditEventsLeft: 1,
    });
  });

  it("still lets the erasure cascade take a tenant's audit events with it", async () => {
    // The other half, and the reason the exception exists. Deletion on request is
    // a promise the PRD makes and SEEN-083 performs as `service_role`, and an
    // audit table nothing could delete from would make it impossible to keep. F21
    // asks this of its own registry; it is asked again here because the branch
    // that permits the cascade is the branch this finding rewrote, and a fix that
    // closed the hole by closing the cascade would pass every other test in this
    // file.
    const measured = await rolledBack(async () => {
      const { tenant } = await seedWithAuditEvent('Tenant erased on request');
      await client.query('set local role service_role');
      const before = await rowsFor('public.audit_events', tenant);
      const erased = await said(() => client.query(
        'delete from public.tenants where tenant_id = $1',
        [tenant],
      ));
      const after = {
        tenantRowsAfter: await rowsFor('public.tenants', tenant),
        auditEventsAfter: await rowsFor('public.audit_events', tenant),
      };
      await client.query('reset role');
      return { auditEventsBefore: before, erased, ...after };
    });
    expect(
      measured,
      'Erasing a tenant as service_role, which is what deletion on request is, answered '
      + `${measured.erased} and left ${measured.tenantRowsAfter} tenant rows and `
      + `${measured.auditEventsAfter} audit events behind, against ${measured.auditEventsBefore} `
      + 'audit events before it',
    ).toEqual({
      auditEventsBefore: 1, erased: 'accepted', tenantRowsAfter: 0, auditEventsAfter: 0,
    });
  });
});

/**
 * F21: the append-only guarantee has one permitted delete, and nothing stopped
 * the tenant being put back after it.
 *
 * `public.tenants.tenant_id` is a plain uuid primary key with a default, so it is
 * settable on insert. Measured against this stack as `service_role`, which is the
 * role the API and the workers write as, before the registry below existed:
 * delete the tenant, insert a tenant carrying the same id, and the id resolves
 * again with no audit events behind it. Everything else the cascade removed is
 * re-ingestible, because orders, settlements and returns are read back from the
 * marketplace APIs by design, so the audit trail is the only thing permanently
 * lost while the id still resolves in every token, every Stripe customer mapping
 * and every invoice that names it. An erasure and an absence of one become the
 * same observation, which is the opposite of what an audit trail is for.
 *
 * F27 is the same defect one statement further on. The refusal was a `before
 * insert` trigger and nothing else, so an update reached the state an insert could
 * not: erase a tenant, create a fresh one, clear the rows its insert seeded, and
 * set its id to the erased one. Accepted. And because the tombstone registry is
 * keyed by tenant_id, an id that came back and was erased again made the erasure
 * itself fail on the primary key, so the defect did not merely undo a tombstone,
 * it turned deletion on request into an error for that tenant.
 *
 * What this block asks, in this order. The re-creation is refused, and so is the
 * update, whatever id it moves to, while the rest of the tenant row stays
 * ordinarily updatable. The erasure itself still works and still takes the audit
 * events with it, and works a second time on an id whose tombstone already stands,
 * because deletion on request is a promise this schema has to keep and a fix that
 * broke it would be worse than the defect. The tombstone the erasure leaves cannot be deleted or
 * updated away by the roles the application uses, or the whole of the fix is
 * undone by removing the tombstone first. And the tombstone says only that an id
 * is spent and when, because a registry of erasures that held a name would be a
 * retained record of the customer the erasure was performed for.
 *
 * Every test is written as `service_role` inside a transaction that is rolled
 * back: the erasures are real deletes, and the tombstone they leave is permanent
 * by construction.
 */
describe('the tenant id an erasure has consumed', () => {
  let client: Client;

  /** The SQLSTATE the database answered with, or `accepted` when it did not
   * refuse. Behind a savepoint, because each test carries on asking questions
   * after a refusal and a failed statement otherwise aborts the transaction. */
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

  /** Everything inside, as `service_role` and rolled back. */
  async function rolledBack<T>(body: () => Promise<T>): Promise<T> {
    await client.query('begin');
    try {
      await client.query('set local role service_role');
      return await body();
    } finally {
      await client.query('rollback');
    }
  }

  /** One tenant with one audit event behind it, which is the pair an erasure has
   * to remove together and the pair a re-creation would separate. */
  async function seedErasable(name: string): Promise<string> {
    const tenant = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    await client.query(
      `insert into public.audit_events (tenant_id, event_type, actor)
       values ($1, 'test.written_before_erasure', 'test')`,
      [tenant.rows[0].tenant_id],
    );
    return tenant.rows[0].tenant_id;
  }

  /** A living tenant with the six catalogue rows its insert seeds cleared away,
   * and how many were cleared.
   *
   * An update of `tenant_id` on a tenant that still has children is refused by
   * their foreign keys with 23503, which is protection by accident: it says that
   * the rows underneath a tenant hold it in place, not that the id itself refuses
   * a new value. The tests below clear the children first, so the refusal they
   * measure is the rule and not the leftovers, which is how F27 was measured. If a
   * later migration seeds a second child table the count moves and the refusal
   * turns back into 23503, and both are read in the failure text. */
  async function seedWithNoChildren(name: string): Promise<{ tenant: string; cleared: number }> {
    const { rows } = await client.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    const tenant = rows[0].tenant_id;
    const cleared = await client.query(
      'delete from public.marketplaces where tenant_id = $1',
      [tenant],
    );
    return { tenant, cleared: cleared.rowCount ?? 0 };
  }

  /** How many rows of `relation` carry this tenant id, with whatever role is set. */
  async function rowsFor(relation: string, tenant: string): Promise<number> {
    const { rows } = await client.query<{ total: string }>(
      `select count(*) as total from ${relation} where tenant_id = $1`,
      [tenant],
    );
    return Number(rows[0].total);
  }

  beforeAll(async () => {
    client = await connect();
    const present = await tablesIn(client, 'public');
    const missing = ['tenants', 'audit_events'].filter((table) => !present.includes(table));
    if (missing.length > 0) {
      throw new Error(
        'This test cannot say anything about what an erasure consumes: '
        + `${missing.join(', ')} ${missing.length === 1 ? 'does' : 'do'} not exist in the public `
        + 'schema. Apply the trade record migrations with `pnpm db:reset`.',
      );
    }
  });

  afterAll(async () => {
    await client?.end();
  });

  it('is refused when it is created again, so an erasure can be told from no erasure',
    async () => {
      const measured = await rolledBack(async () => {
        const tenant = await seedErasable('Tenant erased and put back');
        await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
        const recreated = await said(() => client.query(
          "insert into public.tenants (tenant_id, name) values ($1, 'Tenant put back')",
          [tenant],
        ));
        return {
          recreated,
          tenantRowsStanding: await rowsFor('public.tenants', tenant),
          auditEventsBehindIt: await rowsFor('public.audit_events', tenant),
        };
      });
      expect(
        measured,
        `An erased tenant id was ${measured.recreated === 'accepted'
          ? `inserted again, leaving ${measured.tenantRowsStanding} tenant row standing with `
            + `${measured.auditEventsBehindIt} audit events behind it, so the erasure of that `
            + 'tenant is indistinguishable from no erasure having happened'
          : `refused with SQLSTATE ${measured.recreated}`}, where a refusal (23001) is what `
        + 'keeps the id spent and the erasure legible',
      ).toEqual({ recreated: '23001', tenantRowsStanding: 0, auditEventsBehindIt: 0 });
    });

  it('is refused when an update hands it to a living tenant, which is the same resurrection '
    + 'one statement further on', async () => {
    // F27: the refusal above was a `before insert` trigger and nothing else, so
    // the id came back through an update instead. Measured as `service_role`: erase
    // a tenant, create a fresh one, clear the rows its insert seeded, and set the
    // fresh tenant's id to the erased one. Accepted, and the id resolved again with
    // no audit events behind it, which is exactly what the refusal above exists to
    // prevent. The route matters less than the rule: what an update of this column
    // does is decided below, and both halves of F27 are asked here.
    const measured = await rolledBack(async () => {
      const erased = await seedErasable('Tenant erased and updated back');
      await client.query('delete from public.tenants where tenant_id = $1', [erased]);
      const { tenant: living, cleared } = await seedWithNoChildren('Tenant given the erased id');
      const handedBack = await said(() => client.query(
        'update public.tenants set tenant_id = $1 where tenant_id = $2',
        [erased, living],
      ));
      return {
        childRowsCleared: cleared,
        handedBack,
        rowsCarryingTheErasedId: await rowsFor('public.tenants', erased),
        auditEventsBehindIt: await rowsFor('public.audit_events', erased),
        theLivingTenantStands: await rowsFor('public.tenants', living),
      };
    });
    expect(
      measured,
      `An update setting a living tenant's id to an erased one was ${measured.handedBack}, where `
      + 'a refusal (23001) is what keeps an erasure from being undone by an update rather than '
      + `by an insert. It left ${measured.rowsCarryingTheErasedId} tenant rows carrying the `
      + `erased id with ${measured.auditEventsBehindIt} audit events behind it, and the tenant `
      + `whose id was to be overwritten stands in ${measured.theLivingTenantStands} rows. `
      + `${measured.childRowsCleared} seeded child rows were cleared first: with any left, a `
      + 'foreign key refuses the update with 23503 and this test passes for the wrong reason',
    ).toEqual({
      childRowsCleared: 6,
      handedBack: '23001',
      rowsCarryingTheErasedId: 0,
      auditEventsBehindIt: 0,
      theLivingTenantStands: 1,
    });
  });

  it('is refused whatever the new id is, because a tenant id is an identity and not a value',
    async () => {
      // The narrow repair for F27 would refuse an update that lands on a tombstoned
      // id. The rule chosen instead is that the column is never updatable at all,
      // so this asks for a target no erasure has ever touched: twenty-eight tables
      // carry a foreign key to public.tenants, and an update that changed a tenant
      // id would rewrite or orphan the tenancy of every row beneath it. The rest of
      // the row is untouched by the rule, and the rename below says so: a fix that
      // froze the whole tenant row would break the ordinary update the schema
      // expects, which is a worse defect than the one it closes.
      const measured = await rolledBack(async () => {
        const { tenant, cleared } = await seedWithNoChildren('Tenant given a brand new id');
        const toAnIdNobodyHasUsed = await said(() => client.query(
          'update public.tenants set tenant_id = gen_random_uuid() where tenant_id = $1',
          [tenant],
        ));
        const renamed = await said(() => client.query(
          "update public.tenants set name = 'Tenant renamed' where tenant_id = $1",
          [tenant],
        ));
        const { rows } = await client.query<{ name: string }>(
          'select name from public.tenants where tenant_id = $1',
          [tenant],
        );
        return {
          childRowsCleared: cleared,
          toAnIdNobodyHasUsed,
          renamed,
          nameAfter: rows[0]?.name,
          itKeptItsOwnId: await rowsFor('public.tenants', tenant),
        };
      });
      expect(
        measured,
        `Changing a tenant id to one no erasure has consumed was ${measured.toAnIdNobodyHasUsed} `
        + `and renaming the same tenant was ${measured.renamed}, leaving the name as `
        + `${measured.nameAfter}. The id is the identity twenty-eight foreign keys hang off, so `
        + 'it is refused every new value (23001); the rest of the row stays ordinary',
      ).toEqual({
        childRowsCleared: 6,
        toAnIdNobodyHasUsed: '23001',
        renamed: 'accepted',
        nameAfter: 'Tenant renamed',
        itKeptItsOwnId: 1,
      });
    });

  it('is still erasable, with its audit events going with it', async () => {
    // Deletion on request is a promise this schema has to keep: the PRD gives a
    // tenant 30 days and SEEN-083 performs it as `service_role`. A fix that made
    // the erasure refuse, or that left the audit events standing after it, would
    // be a worse defect than the one it closes, so this is asked every run rather
    // than once when the registry was written.
    const measured = await rolledBack(async () => {
      const tenant = await seedErasable('Tenant erased on request');
      const before = await rowsFor('public.audit_events', tenant);
      const erased = await said(() => client.query(
        'delete from public.tenants where tenant_id = $1',
        [tenant],
      ));
      return {
        auditEventsBefore: before,
        erased,
        tenantRowsAfter: await rowsFor('public.tenants', tenant),
        auditEventsAfter: await rowsFor('public.audit_events', tenant),
      };
    });
    expect(
      measured,
      'Erasing a tenant as service_role, which is what deletion on request is, answered '
      + `${measured.erased} and left ${measured.tenantRowsAfter} tenant rows and `
      + `${measured.auditEventsAfter} audit events behind, against ${measured.auditEventsBefore} `
      + 'audit events before it',
    ).toEqual({
      auditEventsBefore: 1, erased: 'accepted', tenantRowsAfter: 0, auditEventsAfter: 0,
    });
  });

  it('is still erasable when its tombstone already stands, so deletion on request cannot fail '
    + 'on the registry', async () => {
    // The second half of F27, and the half that turns a reversible erasure into an
    // unkeepable promise. seen.record_tenant_erasure inserts into a registry keyed
    // by tenant_id, so an id that is tombstoned and comes back cannot be erased a
    // second time: the insert violates the primary key and the delete fails with
    // 23505. Deletion on request is owed within 30 days, and a tenant it refuses
    // for is worse off than one whose id was reusable.
    //
    // The route back is deliberately outside the refusals above, as a superuser or
    // the owner turning a trigger off is: with those refusals in place no id should
    // come back at all, and this asks what happens if one does anyway. A promise
    // this load-bearing should not rest on another guarantee holding.
    const measured = await rolledBack(async () => {
      const tenant = await seedErasable('Tenant erased, resurrected, erased again');
      const first = await said(() => client.query(
        'delete from public.tenants where tenant_id = $1',
        [tenant],
      ));
      await client.query('reset role');
      await client.query('alter table public.tenants disable trigger refuse_erased_tenant_id');
      await client.query(
        'insert into public.tenants (tenant_id, name) values ($1, $2)',
        [tenant, 'Tenant back by a route the triggers do not cover'],
      );
      await client.query('alter table public.tenants enable trigger refuse_erased_tenant_id');
      await client.query('set local role service_role');
      const second = await said(() => client.query(
        'delete from public.tenants where tenant_id = $1',
        [tenant],
      ));
      await client.query('reset role');
      return {
        first,
        second,
        tenantRowsAfter: await rowsFor('public.tenants', tenant),
        tombstones: await rowsFor(ERASURE_REGISTRY_TABLE, tenant),
      };
    });
    expect(
      measured,
      `Erasing a tenant answered ${measured.first}, and erasing the same id again once it had `
      + `come back answered ${measured.second}, leaving ${measured.tenantRowsAfter} tenant rows `
      + `and ${measured.tombstones} tombstones. A second erasure that fails (23505) is deletion `
      + 'on request refusing for the one tenant that has already asked once',
    ).toEqual({
      first: 'accepted', second: 'accepted', tenantRowsAfter: 0, tombstones: 1,
    });
  });

  it('leaves a tombstone the application cannot delete, update or read', async () => {
    // Without this the fix is defeated in one statement: delete the tombstone,
    // then insert the tenant again. So the registry is append-only the way
    // audit_events is, and by the same three layers. The roles the application
    // uses hold no privilege on it at all, which is why their refusal is 42501 and
    // not the trigger's; the owner reaches the table and is refused by the trigger,
    // which is 23001. The read is asked for as well: a registry of which brands
    // have left is not something a request should be able to enumerate.
    const measured = await rolledBack(async () => {
      const tenant = await seedErasable('Tenant tombstoned');
      await client.query('delete from public.tenants where tenant_id = $1', [tenant]);
      const asServiceRole = {
        deleted: await said(() => client.query(
          `delete from ${ERASURE_REGISTRY_TABLE} where tenant_id = $1`, [tenant],
        )),
        updated: await said(() => client.query(
          `update ${ERASURE_REGISTRY_TABLE} set erased_at = now() where tenant_id = $1`, [tenant],
        )),
        read: await said(() => client.query(
          `select tenant_id from ${ERASURE_REGISTRY_TABLE} where tenant_id = $1`, [tenant],
        )),
      };
      await client.query('reset role');
      const asOwner = {
        tombstones: await rowsFor(ERASURE_REGISTRY_TABLE, tenant),
        deleted: await said(() => client.query(
          `delete from ${ERASURE_REGISTRY_TABLE} where tenant_id = $1`, [tenant],
        )),
        updated: await said(() => client.query(
          `update ${ERASURE_REGISTRY_TABLE} set erased_at = now() where tenant_id = $1`, [tenant],
        )),
      };
      return { asServiceRole, asOwner };
    });
    expect(
      measured,
      `What ${ERASURE_REGISTRY_TABLE} answered, as service_role and then as the role that owns `
      + `it: ${JSON.stringify(measured)}. A tombstone a role can remove is a tenant id that can `
      + 'be used again a statement later',
    ).toEqual({
      asServiceRole: { deleted: '42501', updated: '42501', read: '42501' },
      asOwner: { tombstones: 1, deleted: '23001', updated: '23001' },
    });
  });

  it('is all the tombstone says, so the registry is not a record of erased customers',
    async () => {
      // The registry exists to make an id unusable, and an id is all it may hold.
      // A name, a user or an address kept here would survive the erasure that was
      // asked for, which is the thing the tenant deleted its account to prevent,
      // and part 7's classification does not reach schema seen to catch it.
      const { rows } = await client.query<{ column: string }>(
        `select a.attname as column
           from pg_catalog.pg_attribute a
          where a.attrelid = to_regclass($1) and a.attnum > 0 and not a.attisdropped
          order by a.attname`,
        [ERASURE_REGISTRY_TABLE],
      );
      const held = rows.map((row) => row.column);
      assertPopulated(held, `the columns of ${ERASURE_REGISTRY_TABLE}`);
      expect(
        held,
        `${ERASURE_REGISTRY_TABLE} holds ${held.join(', ')}, where a tombstone may say only that `
        + 'an id is spent and when it was spent',
      ).toEqual([...ERASURE_REGISTRY_COLUMNS]);
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

  /** One tenant, and a claim credited by a settlement line, which is the far end of
   * `claims_credited_by_settlement_line_id_fkey`. Two tests below drop that one key
   * and put a different delete rule in its place, so both start from the same rows
   * and the only difference between what they measure is the rule. Rolled back by
   * the caller's transaction; nothing here is left behind. */
  async function creditedClaim(): Promise<{ tenant: string; line: string; claim: string }> {
    const tenant = (await client.query<{ tenant_id: string }>(
      "insert into public.tenants (name) values ('Tenant with a credited claim') "
      + 'returning tenant_id',
    )).rows[0].tenant_id;
    const connection = (await client.query<{ id: string }>(
      "insert into public.connections (tenant_id, marketplace) values ($1, 'bol') returning id",
      [tenant],
    )).rows[0].id;
    const settlement = (await client.query<{ id: string }>(
      `insert into public.settlements (tenant_id, connection_id, marketplace, external_id)
       values ($1, $2, 'bol', 'SETTLEMENT-CREDITED-CLAIM') returning id`,
      [tenant, connection],
    )).rows[0].id;
    const line = (await client.query<{ id: string }>(
      `insert into public.settlement_lines
         (tenant_id, settlement_id, marketplace, external_id, line_type, amount_cents)
       values ($1, $2, 'bol', 'LINE-CREDITED-CLAIM', 'compensation', 1234) returning id`,
      [tenant, settlement],
    )).rows[0].id;
    const claim = (await client.query<{ id: string }>(
      `insert into public.claims (tenant_id, marketplace, credited_by_settlement_line_id)
       values ($1, 'bol', $2) returning id`,
      [tenant, line],
    )).rows[0].id;
    return { tenant, line, claim };
  }

  /** What the database answered a statement with: `accepted`, or the SQLSTATE it was
   * refused with. The savepoint is what lets a refusal be measured and the enclosing
   * transaction carry on to the next measurement rather than end aborted. */
  async function answered(body: () => Promise<unknown>): Promise<string> {
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

  it('holds no key that refuses the delete of the row it points at', async () => {
    // A composite key is the fix, and `on delete restrict` is the way to write one
    // that makes a parent row undeletable: the child refuses the parent's delete
    // outright, so a settlement line or a connection could not be removed or
    // re-ingested while anything pointed at it, which ingest does on every
    // correction a marketplace sends. So no key between tenant-owned tables may
    // restrict. The test below measures that cost on one key rather than leaving
    // the reason to be believed.
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
      `${restricting.length} foreign keys refuse a delete of the parent outright, so the row `
      + 'each points at cannot be removed or re-ingested while it stands: '
      + restricting.join('; '),
    ).toEqual([]);
  });

  it('costs the ordinary delete of a parent row, which is the reason no key restricts',
    async () => {
      // What a restricting key would cost, measured rather than stated, on the same
      // one key as the set-null measurement below, so the only difference between the
      // two is the rule put in its place. Deleting the settlement line a claim was
      // credited by is refused with 23503, and that is the whole of the reason: a
      // settlement line could not be removed or re-ingested while a claim pointed at
      // it, which ingest does on every correction the marketplace sends.
      //
      // A tenant's erasure is not the case that proves it, and the comment above this
      // test used to say it was. With the restricting key in place, `delete from
      // public.tenants` is accepted: the cascade removes the claim before the restrict
      // can be reached. That is the order Postgres schedules two sibling cascade
      // actions in, exactly as with the bare set-null below, and it is not a guarantee
      // to rest a reason on either way. The exclusion of restrict stands on the
      // ordinary parent-row delete, which reproduces every time.
      await client.query('begin');
      let measured;
      try {
        const seeded = await creditedClaim();
        await client.query(
          'alter table public.claims drop constraint claims_credited_by_settlement_line_id_fkey',
        );
        await client.query(
          `alter table public.claims add constraint claims_credited_by_settlement_line_id_fkey
             foreign key (tenant_id, credited_by_settlement_line_id)
             references public.settlement_lines (tenant_id, id) on delete restrict`,
        );
        measured = {
          deletingTheParentRow: await answered(() => client.query(
            'delete from public.settlement_lines where id = $1', [seeded.line],
          )),
          erasingTheTenant: await answered(() => client.query(
            'delete from public.tenants where tenant_id = $1', [seeded.tenant],
          )),
        };
      } finally {
        await client.query('rollback');
      }
      expect(
        measured,
        'With `on delete restrict` in place of the key a claim is credited by, deleting the '
        + `settlement line answered ${measured.deletingTheParentRow} and erasing the tenant `
        + `answered ${measured.erasingTheTenant}. A restricting key is excluded because it makes `
        + "the parent row undeletable while a child points at it, not because it blocks a "
        + "tenant's erasure: the cascade reaches the child first, which is scheduling and not a "
        + 'guarantee',
      ).toEqual({ deletingTheParentRow: '23503', erasingTheTenant: 'accepted' });
    });

  it('nulls the reference and not the tenant when a set-null parent is deleted', async () => {
    // Eight of the twenty-eight rewritten keys set null, and each names the column
    // to null. What the column-list form buys, and what the bare form costs, is
    // measured here rather than stated, because a reason is the part of a schema
    // that rots without anybody noticing.
    //
    // The shipped form first: deleting the settlement line a claim was credited by
    // nulls the reference and leaves tenant_id standing, so the claim survives its
    // parent. Then the bare form in its place, inside the same rolled-back
    // transaction: it nulls every column of the key, tenant_id among them, and
    // tenant_id is not null, so the ordinary delete of the parent row is refused
    // with 23502 and that settlement line cannot be removed or re-ingested at all
    // while a claim points at it.
    //
    // A tenant's erasure is not the case that proves it, and the Outcome used to
    // say it was. Measured with the bare form in place, `delete from public.tenants`
    // is accepted, because the cascade removes the claim before the set-null can
    // reach it, and which of two sibling cascade actions Postgres schedules first
    // is not a guarantee to rest a reason on.
    await client.query('begin');
    let measured;
    try {
      const seeded = await creditedClaim();
      await client.query('savepoint as_shipped');
      const shippedDelete = await answered(() => client.query(
        'delete from public.settlement_lines where id = $1', [seeded.line],
      ));
      const { rows } = await client.query<{
        tenant_id: string | null; credited_by_settlement_line_id: string | null;
      }>(
        'select tenant_id, credited_by_settlement_line_id from public.claims where id = $1',
        [seeded.claim],
      );
      await client.query('rollback to savepoint as_shipped');

      // The same delete with a bare `on delete set null` in the key's place, which
      // is the form the Outcome's sentence is about.
      await client.query(
        'alter table public.claims drop constraint claims_credited_by_settlement_line_id_fkey',
      );
      await client.query(
        `alter table public.claims add constraint claims_credited_by_settlement_line_id_fkey
           foreign key (tenant_id, credited_by_settlement_line_id)
           references public.settlement_lines (tenant_id, id) on delete set null`,
      );
      const bareDelete = await answered(() => client.query(
        'delete from public.settlement_lines where id = $1', [seeded.line],
      ));
      measured = {
        shipped: {
          deletingTheParentRow: shippedDelete,
          claimsLeft: rows.length,
          keepsItsTenant: rows[0]?.tenant_id === seeded.tenant,
          nullsTheReference: rows[0]?.credited_by_settlement_line_id === null,
        },
        bare: { deletingTheParentRow: bareDelete },
      };
    } finally {
      await client.query('rollback');
    }
    expect(
      measured,
      'Deleting the settlement line a claim was credited by answered '
      + `${measured.shipped.deletingTheParentRow} with the key as it ships and `
      + `${measured.bare.deletingTheParentRow} with a bare set-null in its place, and the claim `
      + `${measured.shipped.keepsItsTenant ? 'kept' : 'lost'} its tenant_id. The column-list form `
      + 'is what keeps a not-null tenant_id out of the set: without it the parent row cannot be '
      + 'deleted at all (23502) while a child points at it',
    ).toEqual({
      shipped: {
        deletingTheParentRow: 'accepted',
        claimsLeft: 1,
        keepsItsTenant: true,
        nullsTheReference: true,
      },
      bare: { deletingTheParentRow: '23502' },
    });
  });
});

describe('the relations in the public schema that are not tables', () => {
  // Every guard above asks pg_catalog for `relkind = 'r'`, and so does part 4's
  // per-table revoke and its self-check. That is an ordinary table and nothing
  // else. Four other relation kinds hold rows, are served by the Data API exactly
  // as a table is, and were invisible to all of it.
  //
  // Measured against this stack in a rolled-back transaction by the third Codex
  // review of SEEN-008 (F19), with two tenants seeded: `anon` is refused
  // `public.shipments` with SQLSTATE 42501, and reads both tenants' `buyer_name`
  // and `buyer_address` through `create view public.buyer_book as select
  // tenant_id, buyer_name, buyer_address from public.shipments`. Twenty-nine
  // relations of kind `r` were counted and no view was seen. SEEN-046 and SEEN-024
  // are the tickets that will add exactly such a view.
  //
  // Two properties, and the schema needs both. A view has to be born unreachable,
  // which is the default privileges; and a view somebody deliberately grants has
  // to read its base tables as the caller, which is `security_invoker`. A
  // materialised view can do neither, so it does not belong in this schema at all.

  let client: Client;

  beforeAll(async () => {
    client = await connect();
  });

  afterAll(async () => {
    await client?.end();
  });

  it('is born unreachable: no client-bound role holds a default privilege on a new relation',
    async () => {
      // This is the prevention half and it is the one that closes the hole. With
      // the default access control list of schema public standing, a view is
      // readable by `anon` from the moment `create view` returns, and no statement
      // in the migration that created it says so. The Outcome of the first review
      // named this and left it open as "detection rather than prevention"; a view
      // is what made detection impossible as well, because nothing looked at one.
      const held = await defaultPrivilegesForClientRolesIn(client, 'public');
      expect(
        held,
        `${held.length} default privileges stand on schema public, so every table, view and `
        + 'materialised view a later migration creates there is born holding them, and a view '
        + 'is not subject to row-level security unless it says `security_invoker = true`: '
        + held.join('; '),
      ).toEqual([]);
    });

  it('grants no client-bound role anything on a view or a materialised view', async () => {
    const held = await clientPrivilegesOnNonTablesIn(client, 'public');
    expect(
      held,
      `${held.length} privileges on relations that are not tables are held by a role a browser `
      + 'request is bound to, and the privilege guard on the twenty-nine tables reads none of '
      + 'them: ' + held.join('; '),
    ).toEqual([]);
  });

  it('carries no view that reads its base tables with anything but the caller\'s own rights',
    async () => {
      const owned = await viewsWithoutInvokerRightsIn(client, 'public');
      expect(
        owned,
        `${owned.length} views in the public schema run with their owner's rights, so the `
        + 'row-level security of the tables underneath them is not applied to the request at '
        + 'all and every tenant\'s rows are readable through them: ' + owned.join('; '),
      ).toEqual([]);
    });

  it('carries no materialised view, because row-level security can never reach one', async () => {
    const stored = await materialisedViewsIn(client, 'public');
    expect(
      stored,
      `${stored.length} materialised views are in the public schema. A materialised view is a `
      + 'stored copy of the rows its owner could see when it was refreshed, so no policy is '
      + 'ever applied to a request that reads it and no option makes one apply: '
      + stored.join('; '),
    ).toEqual([]);
  });

  it('would see a view and a materialised view a later migration added', async () => {
    // The three assertions above pass against a schema with no view in it, and so
    // would a checker that measured nothing. This is what they are for, written as
    // the migration SEEN-046 will want: a view over the table that holds buyer
    // name and buyer address.
    await client.query('begin');
    try {
      await client.query(
        'create view public.seen_view_probe as '
        + 'select tenant_id, buyer_name, buyer_address from public.shipments',
      );
      await client.query(
        'create materialized view public.seen_matview_probe as '
        + 'select tenant_id, buyer_name from public.shipments',
      );
      const relations = (await nonTableRelationsIn(client, 'public')).map((row) => row.name);
      expect(
        relations,
        'The relation listing does not see a view added to the public schema, so nothing below '
        + 'it can either',
      ).toEqual(expect.arrayContaining(['seen_matview_probe', 'seen_view_probe']));

      const owned = await viewsWithoutInvokerRightsIn(client, 'public');
      expect(
        owned.filter((entry) => entry.startsWith('seen_view_probe')),
        'A view created without `security_invoker = true` was not reported, so the assertion '
        + `passes by finding nothing: it reported ${owned.join('; ') || 'nothing at all'}`,
      ).not.toEqual([]);

      const stored = await materialisedViewsIn(client, 'public');
      expect(
        stored.filter((entry) => entry.startsWith('seen_matview_probe')),
        'A materialised view in the public schema was not reported, so the assertion passes by '
        + `finding nothing: it reported ${stored.join('; ') || 'nothing at all'}`,
      ).not.toEqual([]);

      // And a privilege granted on a view is reported, whether the default access
      // control list put it there or a later migration wrote the grant by hand.
      await client.query('grant select on public.seen_view_probe to authenticated');
      const held = await clientPrivilegesOnNonTablesIn(client, 'public');
      expect(
        held.filter((entry) => entry.startsWith('seen_view_probe')),
        'A select granted to `authenticated` on a view was not reported, so the privilege '
        + `assertion on the non-table relations measures nothing: it reported ${held.join('; ') || 'nothing at all'}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });

  it('would see a default privilege a later migration granted back', async () => {
    // The same question of the prevention half. `alter default privileges` is the
    // one statement that can reopen this, and the forbidden-statement scanner
    // refuses it in its granting form; this is the database answering rather than
    // the file.
    await client.query('begin');
    try {
      await client.query(
        'alter default privileges in schema public grant select on tables to anon',
      );
      const held = await defaultPrivilegesForClientRolesIn(client, 'public');
      expect(
        held.filter((entry) => entry.startsWith('anon')),
        'A default privilege granted back to `anon` on schema public was not reported, so the '
        + `assertion passes by finding nothing: it reported ${held.join('; ') || 'nothing at all'}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });
});
