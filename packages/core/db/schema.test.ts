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
import { Client } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import {
  listRepositoryDirectory, packageSources, readRepositoryFile, repositoryPathExists,
  REPOSITORY_ROOT, testTaskInputs,
} from './repository';
import {
  APPEND_ONLY_PRIVILEGES, APPEND_ONLY_TABLES, BUYER_PII_COLUMNS, BUYER_PII_COMMENT_TERMS,
  BUYER_PII_MARKER, CLIENT_BOUND_ROLES, COLUMN_GRANTABLE_PRIVILEGES,
  CONSTRAINED_NOT_BUYER_PII_COLUMNS, CONSTRAINED_NOT_BUYER_PII_MARKER,
  CROSS_TENANT_FOREIGN_KEY_EXEMPTIONS, DATA_API_CONFIG, DATA_API_ROLES, DATA_API_SCHEMAS,
  DATA_API_SCHEMAS_SETTING, DEFAULT_ACL_OBJECT_CLASSES,
  ERASURE_REGISTRY_COLUMNS, ERASURE_REGISTRY_TABLE,
  FORBIDDEN_PRIVILEGE_STATEMENTS, FREE_TEXT_TYPE_NAMES, FUNCTION_PRIVILEGE,
  GOVERNED_PRIVILEGES,
  HASHED_REPOSITORY_DOCUMENTS, HELPER_SCHEMA, HELPER_SCHEMA_CALLABLE_ROUTINES,
  MIGRATION_SET_HEADER, MIGRATIONS_DIRECTORY,
  NON_TABLE_RELKINDS, NOT_BUYER_PII_MARKER, PROKIND_NAMES,
  RELATION_RULE_MIGRATION_MARKER, RELKIND_NAMES,
  SEQUENCE_PRIVILEGES, SEQUENCE_RELKIND,
  TABLE_PRIVILEGES, TABLE_RELKINDS, TENANCY_CLAUSES, TENANT_CLAIM, TICKETS_DIRECTORY,
  TRADE_RECORD_MIGRATION_MARKER, TRADE_RECORD_TABLES,
  VIEW_SECURITY_OPTION, VIEW_SECURITY_OPTION_TRUE, WITHDRAWN_BIRTH_CLAIMS,
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

/** A relation in a schema, with the single character `pg_class` names its kind by. */
interface Relation { name: string; kind: string }

/**
 * Every relation in the schema that this database's own policies govern, which is
 * what "every table in the public schema" means here and what every guard below
 * is built on.
 *
 * `TABLE_RELKINDS` is `'r'` and `'p'`: an ordinary table and a partitioned table.
 * This asked for `'r'` alone until the fifth Codex review of SEEN-008 (F29), which
 * is a filter and not a sentence: a partitioned table is a table in the public
 * schema, it holds rows, it is read through the Data API as a table is, and it can
 * carry an enabled policy, so leaving it out made criterion 2 a claim about
 * ordinary tables wearing the words "100% of them".
 *
 * A view, a materialised view and a foreign table are not here and are not an
 * oversight: this schema's tenancy cannot be expressed over any of the three, so
 * asking one for a `tenant_id` column and a policy would be asking for a guarantee
 * the database cannot keep. Part 6 gives each of them the rule it can keep, and
 * the guards for those are further down this file.
 */
async function tablesIn(client: Client, schema: string): Promise<string[]> {
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = any($2)
      order by c.relname`,
    [schema, Object.keys(TABLE_RELKINDS)],
  );
  return rows.map((row) => row.name);
}

/**
 * Every relation in the schema that holds rows and is not an ordinary table,
 * with the kind `pg_class` gives it.
 *
 * `tablesIn` asks for the kinds a policy of this database governs and every guard
 * above it is built on that, which is the whole of the hole the third Codex review
 * of SEEN-008 (F19) found. A view added to `public` by a later migration answers to
 * `'v'`, is born holding the default access control list of schema `public`, which
 * covers views as surely as tables because `pg_default_acl` files both under
 * `defaclobjtype = 'r'`, and is not subject to the row-level security of the
 * tables underneath it unless it was created `with (security_invoker = true)`.
 * So the tenancy guard does not see it, the privilege guard does not see it, and
 * `anon` reads every tenant's rows through it.
 *
 * Three kinds rather than the four F19 listed. A partitioned table was in this set
 * because nothing else looked at one, and it is a table: it now answers to
 * `tablesIn` and owes what every other table owes. What is left here is the
 * relations a tenancy policy of this database cannot be written on at all, which is
 * why the rule for each of them is a privilege and a place rather than a policy.
 */
async function nonTableRelationsIn(client: Client, schema: string): Promise<Relation[]> {
  const { rows } = await client.query<Relation>(
    `select c.relname as name, c.relkind as kind
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = any($2)
      order by c.relname`,
    [schema, Object.keys(NON_TABLE_RELKINDS)],
  );
  return rows;
}

/** One such relation, named the way a failure message should name it. */
function named(relation: Relation): string {
  return `${relation.name} (${RELKIND_NAMES[relation.kind] ?? `relkind ${relation.kind}`})`;
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

/** The tables in the schema with no `tenant_id` column, over the same two kinds
 * `tablesIn` lists: an ordinary table and a partitioned table. A partitioned table
 * carries the column its partitions store, so a missing `tenant_id` on the parent
 * is a missing `tenant_id` in every row underneath it. */
async function tenantIdGapsIn(client: Client, schema: string): Promise<string[]> {
  const tables = await tablesIn(client, schema);
  assertPopulated(tables, `a tenant_id column on every table in schema ${schema}`);
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = any($2)
        and not exists (
          select 1 from pg_catalog.pg_attribute a
           where a.attrelid = c.oid and a.attname = 'tenant_id'
             and a.attnum > 0 and not a.attisdropped)
      order by c.relname`,
    [schema, Object.keys(TABLE_RELKINDS)],
  );
  return rows.map((row) => row.name);
}

/**
 * The tables in the schema without row-level security enabled, over the same two
 * kinds again, and both are load-bearing rather than one covering the other.
 *
 * `relrowsecurity` is per relation and is not inherited either way. Measured on
 * the local stack: enabling it on a partitioned table leaves it false on the
 * partition, so a role holding select on the partition reads every tenant's rows
 * through it; and enabling it on a partition does nothing for a query that goes
 * through the parent. Each relation is asked for its own.
 */
async function rlsGapsIn(client: Client, schema: string): Promise<string[]> {
  const tables = await tablesIn(client, schema);
  assertPopulated(tables, `row-level security on every table in schema ${schema}`);
  const { rows } = await client.query<{ name: string }>(
    `select c.relname as name
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where n.nspname = $1 and c.relkind = any($2) and not c.relrowsecurity
      order by c.relname`,
    [schema, Object.keys(TABLE_RELKINDS)],
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

/** What the database answered a role a request can be bound to: `accepted` with
 * the number of rows it saw, or the SQLSTATE it was refused with.
 *
 * Wrapped in a savepoint rather than in a transaction of its own, because a
 * refusal aborts the transaction the probe is rolled back at the end of, and a
 * probe with a second question to ask would then be answered 25P02 whatever the
 * schema does. `set local role` is reverted by the rollback to the savepoint, so
 * the next line runs as the owner again without a `reset role` of its own.
 */
interface Answer { answer: string; rows: number | null }

async function answeredAs(client: Client, role: string, sql: string): Promise<Answer> {
  await client.query('savepoint seen_privilege_probe');
  try {
    await client.query(`set local role ${role}`);
    const result = await client.query(sql);
    return { answer: 'accepted', rows: result.rowCount };
  } catch (cause) {
    return { answer: (cause as { code?: string }).code ?? 'refused with no SQLSTATE', rows: null };
  } finally {
    await client.query('rollback to savepoint seen_privilege_probe');
  }
}

/**
 * What the database answered the owner when it was asked to run a statement:
 * `accepted`, or the SQLSTATE it was refused with.
 *
 * `answeredAs` asks what a role a request can be bound to may read; this asks what
 * the schema itself may be made to hold, which is a different question and is the
 * one a rule about a relation kind rests on. Savepoint-wrapped for the same reason:
 * a refusal aborts the transaction, and a probe measuring three refusals in a row
 * would be answered 25P02 for the second and third whatever the database does.
 */
async function refusedWith(client: Client, sql: string): Promise<string> {
  await client.query('savepoint seen_statement_probe');
  try {
    await client.query(sql);
    await client.query('release savepoint seen_statement_probe');
    return 'accepted';
  } catch (cause) {
    await client.query('rollback to savepoint seen_statement_probe');
    return (cause as { code?: string }).code ?? 'refused with no SQLSTATE';
  }
}

/** One privilege a role actually holds on one relation, with the columns it holds
 * it on when it does not hold it on the whole relation. */
interface Holding extends Relation { role: string; privilege: string; columns: string | null }

/**
 * What each of the given roles can actually do to each relation of the given
 * kinds, asked of the database rather than read out of the relation's own access
 * control list.
 *
 * The two guards below used to read `aclexplode(c.relacl)` and match the grantee
 * against the role names they govern, which is a different question from the one
 * they mean to ask and the fifth Codex review of SEEN-008 (F30) named three routes
 * past it. A grant to PUBLIC is filed with no role behind the grantee, so a guard
 * looking for `anon` by name walks past the grant that gave the privilege to
 * `anon` and to every other role at once. A grant on a single column is filed in
 * `pg_attribute.attacl` and does not appear in `pg_class.relacl` at all, so the
 * relation reads as holding nothing while a caller reads a buyer's name out of it.
 * And a privilege held through membership of another role is in the ACL of the
 * relation the member never appears in either.
 *
 * `has_table_privilege` answers all three at once, because it answers what a role
 * can do; it is what the append-only guard on `audit_events` has asked all along,
 * three guards from two that did not. A table-level answer still cannot see a
 * column grant, so every column of every relation is asked as well, for the three
 * privileges a column can carry.
 *
 * What it costs is measured rather than assumed: 29 tables by 3 roles by 5
 * privileges, with every column asked for 3 of those 5, is about 5,000 catalogue
 * lookups and returns in 4 milliseconds on the local stack, so nothing is narrowed
 * to keep it quick.
 *
 * What it still does not cover, said as carefully as what it does. It measures the
 * privilege a role holds and not what the rows underneath it are: a policy is the
 * other half of the boundary and the tenancy guards are what read it. It measures
 * one schema, so a relation this trade record reaches in another is not asked. It
 * cannot see a privilege a `security definer` function lends its caller, because
 * that privilege belongs to the function's owner and no catalogue files it against
 * the caller. And it is a measurement of the database as it stands, so a later
 * migration granting on a column is caught when this runs and not when it is
 * written; the same question is asked again by the self-check part 4 ends with, so
 * that the migration fails as it applies.
 */
async function effectivePrivilegesIn(
  client: Client,
  schema: string,
  relkinds: string[],
  roles: readonly string[],
): Promise<Holding[]> {
  const { rows } = await client.query<Holding>(
    `with relations as (
       select c.oid, c.relname as name, c.relkind as kind
         from pg_catalog.pg_class c
         join pg_catalog.pg_namespace n on n.oid = c.relnamespace
        where n.nspname = $1 and c.relkind = any($2)
     ), holders as (
       select r.oid, r.rolname as role
         from pg_catalog.pg_roles r
        where r.rolname = any($3)
     ), asked as (
       select unnest($4::text[]) as privilege
     )
     select rel.name, rel.kind, h.role, a.privilege,
            case when has_table_privilege(h.oid, rel.oid, a.privilege) then null else (
              select string_agg(att.attname, ', ' order by att.attnum)
                from pg_catalog.pg_attribute att
               where att.attrelid = rel.oid and att.attnum > 0 and not att.attisdropped
                 and a.privilege = any($5)
                 and has_column_privilege(h.oid, rel.oid, att.attnum, a.privilege)
            ) end as columns
       from relations rel
       cross join holders h
       cross join asked a
      where has_table_privilege(h.oid, rel.oid, a.privilege)
         or exists (
           select 1
             from pg_catalog.pg_attribute att
            where att.attrelid = rel.oid and att.attnum > 0 and not att.attisdropped
              and a.privilege = any($5)
              and has_column_privilege(h.oid, rel.oid, att.attnum, a.privilege)
         )
      order by rel.name, h.role, a.privilege`,
    [
      schema, relkinds, [...roles],
      [...GOVERNED_PRIVILEGES], [...COLUMN_GRANTABLE_PRIVILEGES],
    ],
  );
  return rows;
}

/** How a holding reads in a failure message: the privilege alone when the role
 * holds it on the whole relation, and the columns named when it holds it on some
 * of them, because "holds SELECT" and "holds SELECT on one column nobody listed"
 * are not the same finding and a message that spelled them the same way would
 * send the next reader to the relation's access control list, where the second is
 * not written down. */
function holdingLabel(holding: Holding): string {
  return holding.columns === null
    ? holding.privilege
    : `${holding.privilege} (${holding.columns})`;
}

/** The privileges each Data API role actually holds on each table, keyed by table
 * and role.
 *
 * The same two kinds as the tenancy guards, so that the two halves of the boundary
 * agree about a partitioned table: reading one through the parent is checked
 * against the parent's privileges alone, measured on the local stack, so a
 * partitioned table the Data API serves has to hold exactly what the trade record
 * intends and nothing more. Reading a partition directly is checked against the
 * partition's own, and a partition is a relation of kind `'r'` and is asked here on
 * its own account. */
async function privilegesIn(
  client: Client,
  schema: string,
): Promise<Map<string, string[]>> {
  const rows = await effectivePrivilegesIn(
    client, schema, Object.keys(TABLE_RELKINDS), DATA_API_ROLES,
  );
  const held = new Map<string, string[]>();
  for (const row of rows) {
    const key = `${row.name}|${row.role}`;
    held.set(key, [...(held.get(key) ?? []), holdingLabel(row)].sort());
  }
  return held;
}

/**
 * Every privilege a client-bound role holds on a relation in the schema that is
 * not an ordinary table, named one by one.
 *
 * The privilege guard above reads the kinds a policy governs and so measures
 * nothing at all about a view. `anon` and `authenticated` should hold nothing on
 * one: a view that a later ticket deliberately publishes has to grant its own
 * select, and say so in the migration that publishes it. Holding nothing is a
 * claim about every column of the view as well as about the view, which is why the
 * columns are asked: a grant of one column of a view over `public.shipments` lets
 * a caller who never signed in read a buyer's name, and the view's own access
 * control list stays empty while it does. A partitioned table is not asked this
 * question, because it is asked the other one: it holds the select `authenticated`
 * holds on every table, and the guard above is what reads it.
 */
async function clientPrivilegesOnNonTablesIn(client: Client, schema: string): Promise<string[]> {
  const rows = await effectivePrivilegesIn(
    client, schema, Object.keys(NON_TABLE_RELKINDS), CLIENT_BOUND_ROLES,
  );
  return rows.map((row) => `${named(row)}: ${row.role} holds ${row.privilege}`
    + (row.columns === null ? '' : ` on column ${row.columns}`));
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
 * Every foreign table in the schema.
 *
 * The same shape as the checker above it and, since the seventh review of SEEN-008
 * (F35), the same rule: a foreign table does not belong in a schema the Data API
 * serves. There is no `security_invoker` for one and no policy either. `create
 * policy` on one is refused 42809, "is not a table", and `enable row level
 * security` is refused 42809 as well, which is what makes criterion 2's exclusion
 * of the kind sound rather than convenient; and its rows are on another server, so
 * a tenant_id column on one would be a claim this database has no way to check and
 * part 5's reference to `public.tenants` cannot be written on it at all, refused
 * 0A000. `information_schema.tables` reports one as a table of the public schema
 * all the same.
 */
async function foreignTablesIn(client: Client, schema: string): Promise<string[]> {
  const relations = await nonTableRelationsIn(client, schema);
  return relations.filter((relation) => relation.kind === 'f').map(named);
}

/**
 * Every default privilege a client-bound role holds on the objects the migration
 * role creates in the schema, named one by one.
 *
 * `alter default privileges` grants on objects that do not exist yet, and
 * `defaclobjtype = 'r'` is not "table": it is every relation kind a `create
 * table`, `create view`, `create materialized view` or `create foreign table`
 * produces. Supabase ships schema `public` with all of `arwdDxtm` defaulted to
 * `anon` and `authenticated`, so a view a later migration adds is readable by a
 * caller who never signed in before that migration's last line has run.
 *
 * `'r'` is also not the only class `pg_default_acl` files, which is the sixth
 * review of SEEN-008 (F32): this asked for `'r'` alone, part 6's revoke was written
 * `on tables`, and a function is `'f'`. Supabase defaults EXECUTE on functions to
 * `anon` and `authenticated` as well, so a `security definer` function a later
 * migration creates in public is born callable with the anon key and runs as its
 * owner, which no policy in this schema governs. Both classes are read here and
 * each names itself, because a message reading "on every relation" about a function
 * would send the next reader to the wrong grammar.
 *
 * Scoped to the role this session is connected as, which is the role the
 * migrations run as, because a default privilege applies to the objects one role
 * creates and says nothing about another's. The second grantor in this database
 * is `supabase_admin`, and its entry is not asserted here: it governs relations
 * `supabase_admin` itself creates in `public`, no migration in this repository
 * creates one, and the migration role is not a member of `supabase_admin` and
 * cannot revoke it. Part 6 states that as the limit it could not close.
 *
 * PUBLIC is read as a grantee of its own, because it is the route past every
 * guard that matches a grantee by name and the fifth Codex review of SEEN-008
 * (F30) found the other two. `alter default privileges in schema public grant
 * select on tables to public` is filed as grantee 0, which `regrole` renders as a
 * hyphen and no role is spelled that way, and the next table created there is
 * born readable by a caller who never signed in. `has_table_privilege` is not the
 * answer to this one and could not be: a default privilege is a statement about
 * relations that do not exist yet, so there is nothing to ask it about, and
 * `pg_default_acl` is the only place the statement is written down.
 *
 * Entries filed against no schema at all are read beside the schema's own, and
 * that is the seventh review of SEEN-008 (F39) read in the direction the finding
 * did not go. `alter default privileges` with no `in schema` clause stores
 * `defaclnamespace = 0` and applies to the named schema as surely as an entry
 * naming it: part 6 uses that form to take PostgreSQL's built-in EXECUTE to PUBLIC
 * off every routine the migration role creates, which is the statement that makes
 * a function in public preventable rather than merely detectable. A guard reading
 * only the schema's own entries could not see that prevention granted back, which
 * is the same defect one scope out as F30 was one grantee out, so the scope is
 * reported in the message rather than assumed.
 */
async function defaultPrivilegesForClientRolesIn(
  client: Client, schema: string,
): Promise<string[]> {
  const { rows } = await client.query<{
    grantor: string; objectClass: string; role: string; privilege: string; scope: number;
  }>(
    `select d.defaclrole::regrole::text as grantor,
            d.defaclobjtype as "objectClass",
            d.defaclnamespace as scope,
            case when a.grantee = 0 then 'PUBLIC'
                 else a.grantee::regrole::text end as role,
            a.privilege_type as privilege
       from pg_catalog.pg_default_acl d
       cross join lateral aclexplode(d.defaclacl) a
      where (d.defaclnamespace = (select oid from pg_catalog.pg_namespace where nspname = $1)
             or d.defaclnamespace = 0)
        and d.defaclobjtype = any($3)
        and d.defaclrole = current_user::regrole
        and (a.grantee::regrole::text = any($2) or a.grantee = 0)
      order by "objectClass", role, privilege`,
    [schema, [...CLIENT_BOUND_ROLES], Object.keys(DEFAULT_ACL_OBJECT_CLASSES)],
  );
  return rows.map((row) => `${row.role} holds ${row.privilege} on every `
    + `${DEFAULT_ACL_OBJECT_CLASSES[row.objectClass] ?? row.objectClass} ${row.grantor} `
    + `creates in ${row.scope === 0 ? 'any schema' : schema}`);
}

/**
 * Every routine in the schema that a browser-bound role can execute, asked of the
 * database rather than read out of the routine's own access control list.
 *
 * This is the question no guard in this ticket asked until the sixth review of
 * SEEN-008 (F32), and the string `has_function_privilege` appeared nowhere in this
 * package. What it answers is worth being exact about, because a function is not a
 * relation with a different `relkind`: the privilege is EXECUTE and the rows it
 * lends the caller are decided by the body and by `security definer`, so a function
 * whose privileges look like nothing on any list can hand `anon` every tenant's
 * rows. Measured on the local stack in a rolled-back transaction: `anon` is refused
 * `public.tenants` with SQLSTATE 42501 and reads both tenants' names through
 * `create function public.probe_tenant_directory() returns setof text language sql
 * security definer as $$ select name from public.tenants $$`, which is the ordinary
 * Supabase RPC pattern and a `POST /rpc/probe_tenant_directory` endpoint because
 * `supabase/config.toml` serves schema public.
 *
 * Asked as `has_function_privilege` and not as `aclexplode(p.proacl)` for the
 * reason F30 established on the relations: a grant to PUBLIC names no role, and
 * PostgreSQL grants EXECUTE to PUBLIC on every function it creates whether any
 * migration says so or not, so the list is the one place the most common route is
 * not spelled. `proacl` is null on a routine nobody has granted or revoked
 * anything on, and null is the state in which every role there is can execute it.
 *
 * All four kinds of routine are asked, because all four are one class to the
 * privilege system and to PostgREST. What this cannot do is say what a routine
 * does with the privilege: `security definer` is reported beside it so that a
 * reader knows which findings bypass the tenancy rather than merely reach it, and
 * the tenancy guards remain the ones that read the policies.
 */
async function executableRoutinesIn(client: Client, schema: string): Promise<string[]> {
  const { rows } = await client.query<{
    signature: string; kind: string; definer: boolean; role: string;
  }>(
    `select p.proname || '('
              || pg_catalog.pg_get_function_identity_arguments(p.oid) || ')' as signature,
            p.prokind as kind,
            p.prosecdef as definer,
            r.rolname as role
       from pg_catalog.pg_proc p
       join pg_catalog.pg_namespace n on n.oid = p.pronamespace
       cross join pg_catalog.pg_roles r
      where n.nspname = $1
        and r.rolname = any($2)
        and has_function_privilege(r.oid, p.oid, $3)
      order by signature, role`,
    [schema, [...CLIENT_BOUND_ROLES], FUNCTION_PRIVILEGE],
  );
  return rows.map((row) => `${schema}.${row.signature} is `
    + `${PROKIND_NAMES[row.kind] ?? `a routine of kind ${row.kind}`}`
    + `${row.definer ? ' running with its owner rights' : ''} that ${row.role} can execute`);
}

/** The client-bound roles named in a routine's own access control list, and
 * whether PUBLIC is named there too.
 *
 * The two halves of what part 6's two revokes reach, kept apart because they are
 * two statements and a round that loses one of them would still read as safe on the
 * other. `alter default privileges ... in schema public ... from anon,
 * authenticated` takes the two named grants off every function the migration role
 * creates next, and `alter default privileges ... revoke execute on functions from
 * public`, filed against no schema, takes PostgreSQL's own grant to PUBLIC off it.
 * Five rounds of this ticket recorded the second as impossible, on a measurement of
 * the per-schema form which cannot subtract a grant that was never filed against a
 * schema; the seventh review (F39) is that the global form can, and both halves are
 * now asserted as guarantees. PUBLIC is read as a grantee of its own because it
 * names no role and is the one an ACL query matching by name walks past. */
async function routineAccessControlList(
  client: Client, signature: string,
): Promise<{ clientRolesNamed: string[]; publicIsNamed: boolean }> {
  const { rows } = await client.query<{ role: string }>(
    `select case when a.grantee = 0 then 'PUBLIC' else a.grantee::regrole::text end as role
       from pg_catalog.pg_proc p
       cross join lateral aclexplode(p.proacl) a
      where p.oid = $1::regprocedure
      order by role`,
    [signature],
  );
  const named = rows.map((row) => row.role);
  return {
    clientRolesNamed: named.filter((role) => (CLIENT_BOUND_ROLES as readonly string[])
      .includes(role)),
    publicIsNamed: named.includes('PUBLIC'),
  };
}

/**
 * Whether one named role can execute one routine, asked of the database.
 *
 * The other half of `routineAccessControlList`, and it is kept separate from the
 * inventory above because the question is not the same one: a list says which
 * grants were written down and this says what a role can do, and the gap between
 * the two is where every routine finding in this ticket lived. It takes the role as
 * an argument rather than looping over the browser-bound pair, because the
 * assertion that matters most about the default privileges is the one about
 * `service_role`, which is neither of them and must stay true.
 */
async function canExecute(client: Client, role: string, signature: string): Promise<boolean> {
  const { rows } = await client.query<{ allowed: boolean }>(
    'select has_function_privilege($1, $2::regprocedure, $3) as allowed',
    [role, signature, FUNCTION_PRIVILEGE],
  );
  return rows[0].allowed;
}

/**
 * Every sequence in the schema a browser-bound role can reach, and what reaching it
 * lends them, asked of the database rather than read out of the sequence's own
 * access control list.
 *
 * The third inventory this suite keeps, and the one nothing in this package had:
 * `relkind = 'S'` appeared in no guard and neither did `has_sequence_privilege`,
 * which is the sixth review of SEEN-008 (F33). A sequence is in neither relation
 * family and it is not a routine, so the twenty-nine-table privilege guard, the
 * guard on the relations that are not tables and the routine guard all pass over
 * one in silence; there is no filter to widen, because there was no question.
 *
 * What it can hand over is not a row and is worse than nothing for being neither.
 * Measured on this stack in a rolled-back transaction with the default privileges
 * standing: `anon` called `nextval` on a sequence in public and was accepted, read
 * `last_value`, which is a count of rows aggregated over every tenant and so is a
 * fact about tenants the caller can name none of, and called `setval(seq, 1)`,
 * which was accepted and makes the next ingest insert collide on the primary key
 * until the sequence catches up, tenant-wide, from a caller who never signed in.
 * Row-level security is not a defence against any of the three, because a sequence
 * holds no row for a policy to be applied to.
 *
 * Asked as `has_sequence_privilege` and not as `aclexplode(c.relacl)`, for the
 * reason F30 established on the relations: a grant to PUBLIC names no role, a
 * privilege held through membership of another role is in no list, and `relacl` is
 * null on a sequence nobody has granted or revoked anything on.
 */
async function sequencesReachableIn(client: Client, schema: string): Promise<string[]> {
  const { rows } = await client.query<{ name: string; role: string; privilege: string }>(
    `select c.relname as name, r.rolname as role, p.privilege as privilege
       from pg_catalog.pg_class c
       join pg_catalog.pg_namespace n on n.oid = c.relnamespace
       cross join pg_catalog.pg_roles r
       cross join unnest($3::text[]) as p(privilege)
      where n.nspname = $1 and c.relkind = $4
        and r.rolname = any($2)
        and has_sequence_privilege(r.oid, c.oid, p.privilege)
      order by name, role, privilege`,
    [schema, [...CLIENT_BOUND_ROLES], Object.keys(SEQUENCE_PRIVILEGES), SEQUENCE_RELKIND],
  );
  return rows.map((row) => `${schema}.${row.name} lets ${row.role} `
    + `${SEQUENCE_PRIVILEGES[row.privilege] ?? row.privilege.toLowerCase()}`);
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
      where n.nspname = $1 and c.relkind = any($3)
        and a.attnum > 0 and not a.attisdropped
        and (t.typname = any($2) or (t.typcategory = 'A' and e.typname = any($2)))
      order by 1`,
    [schema, [...FREE_TEXT_TYPE_NAMES], Object.keys(TABLE_RELKINDS)],
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
  if (!repositoryPathExists(MIGRATIONS_DIRECTORY)) {
    throw new Error(
      `There is no ${MIGRATIONS_DIRECTORY} directory under ${REPOSITORY_ROOT}, so a test that `
      + 'reads the migrations proves nothing. This test resolves the repository root from its own '
      + 'location and that assumption has broken.',
    );
  }
  const files = listRepositoryDirectory(MIGRATIONS_DIRECTORY).filter((name) => name.endsWith('.sql'));
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

/** The one migration whose filename carries the given fragment, as a path relative
 * to the repository root. Thrown rather than reported when there is not exactly
 * one, because a replay of "no file" passes by running nothing. */
function migrationNamed(marker: string): string {
  const matches = migrationFiles().filter((file) => file.includes(marker));
  if (matches.length !== 1) {
    throw new Error(
      `${matches.length} migrations in ${MIGRATIONS_DIRECTORY} carry \`${marker}\` in their `
      + `names, and a test that replays that migration needs exactly one: ${matches.join(', ') || 'none'}`,
    );
  }
  return matches[0] as string;
}

/**
 * The `do` blocks of a migration, in the order the file writes them.
 *
 * The checks a migration makes about the schema it leaves behind are all written
 * this way, because a check that raises is a check and a check in a comment is a
 * hope. They are read out whole rather than through `statementsOf`, which splits
 * on the semicolon and would cut a block into pieces that are not statements.
 *
 * The delimiter is matched on its own line, which is how every block in this set is
 * written; a `$$` inside a comment, as part 6 has when it quotes the function body
 * F32 was reported on, is on a line with other text and so cannot be mistaken for
 * one. The count is asserted by the caller rather than here, so that an extractor
 * which found nothing fails the test that needed the blocks instead of passing it.
 */
function checkedBlocksOf(file: string): string[] {
  const sql = readRepositoryFile(file);
  return sql.match(/^do \$\$$[\s\S]*?^\$\$;$/gm) ?? [];
}

/**
 * What a migration's own checks say about the schema as the caller has left it:
 * the exception the first of them raises, or null when every one of them passes.
 *
 * Each block runs inside a savepoint, so a raise leaves the transaction the caller
 * rolls back at the end usable rather than aborted, and the answer is the
 * database's own words rather than a restatement of them.
 */
async function replayedAgainstTheSchema(client: Client, file: string): Promise<string | null> {
  const blocks = checkedBlocksOf(file);
  if (blocks.length === 0) {
    throw new Error(
      `${file} contains no \`do\` block, so replaying it asserts nothing. Either the file no `
      + 'longer states its rules as checks that run, or the extractor no longer finds them.',
    );
  }
  for (const block of blocks) {
    await client.query('savepoint seen_replay_probe');
    try {
      await client.query(block);
      await client.query('release savepoint seen_replay_probe');
    } catch (cause) {
      await client.query('rollback to savepoint seen_replay_probe');
      return (cause as Error).message;
    }
  }
  return null;
}

/** One member of the trade record v1 migration set: its path and its first line. */
interface SetMember { file: string; firstLine: string }

/**
 * The members of the trade record v1 set whose header misstates the size of the
 * set, or states no part number at all, given every member's first line in
 * migration order.
 *
 * Pure over the members it is handed, so that the test below can show it a set of
 * a size the directory does not have, which is the only way to prove that nothing
 * here is a literal: the size it compares against is the number of members it was
 * given, so a part is added by numbering it and correcting the totals in front of
 * it, not by editing this test.
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
    firstLine: readRepositoryFile(file).split('\n')[0] ?? '',
  }));
}

/** A size a comment gives the set, and the comment that gives it. */
interface StatedSetSize { file: string; line: number; phrase: string; size: number }

/** One source the scanner is asked to read, as its path and its text. */
interface ScannedSource { file: string; contents: string }

/**
 * The spelled cardinals a comment about the set is read for.
 *
 * `one` is not among them. It is the English article far more often than it is a
 * count, so reading it would report `a later migration` and every sentence like
 * it, and a set with a single part in it is not one anybody numbers.
 */
const SPELLED_CARDINALS: Readonly<Record<string, number>> = {
  two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9,
  ten: 10, eleven: 11, twelve: 12,
};

/** A count of the set's members: a number, at most one word, then what is counted. */
const COUNTED_MEMBERS = new RegExp(
  String.raw`\b(\d{1,3}|${Object.keys(SPELLED_CARDINALS).join('|')})\s+`
  + String.raw`(?:[A-Za-z0-9'’-]+\s+)?(files?|migrations?)\b`,
  'gi',
);

/** How a comment line opens, in either language, so that the prose can be read. */
const COMMENT_OPENERS = /^(?:--+|\/\/+|\/\*+|\*+\/?|\*+)\s?/;

/**
 * Every run of consecutive comment lines in a source, as one paragraph of prose
 * with the openers stripped, keyed by the line the run starts on.
 *
 * Joined rather than read line by line because prose wraps: a count written at the
 * end of a line and the noun it counts at the start of the next is the same
 * sentence to a reader, and a scanner that read one line at a time would miss it
 * and be a scanner narrowed by where the last author happened to break the line.
 */
function commentParagraphs(contents: string): { line: number; prose: string }[] {
  const paragraphs: { line: number; prose: string }[] = [];
  let start = 0;
  let lines: string[] = [];
  const close = (): void => {
    if (lines.length > 0) {
      paragraphs.push({ line: start, prose: lines.join(' ').replace(/\s+/g, ' ').trim() });
      lines = [];
    }
  };
  contents.split('\n').forEach((raw, index) => {
    const trimmed = raw.trim();
    if (!COMMENT_OPENERS.test(trimmed)) {
      close();
      return;
    }
    if (lines.length === 0) start = index + 1;
    lines.push(trimmed.replace(COMMENT_OPENERS, ''));
  });
  close();
  return paragraphs;
}

/** How a sentence says it is about this set rather than about migrations at large. */
const NAMES_THE_SET = /trade[ _]record[ _]v1|\bsets?\b/i;

/**
 * Every size the sources state for the trade record v1 set in a comment.
 *
 * Pure over the sources it is handed, so the test below can show it prose the
 * repository does not contain. A count is read only where the sentence carrying it
 * says it is about this set, which is why part 7 can say that a comment restated
 * in a pair of migrations is a pair of comments that drift apart and be left
 * alone: a paragraph is too coarse a unit, because a migration's whole preamble is
 * one run of comment lines headed by the name of the set.
 *
 * What it can and cannot do, stated rather than implied. It reads a count written
 * as a numeral or spelled out and standing in front of what it counts, which is
 * how every such sentence in these files is written; prose that says `all nine of
 * them` states the same fact and is not read. So it is a guard and not a proof,
 * and the fix it guards is that the size is not written in prose at all: the
 * headers carry it, `misnumberedSetHeaders` reads them against the directory, and
 * a sentence that restates the number is a second authority nothing checks. That
 * is F37, where this file and `tables.ts` went on giving the set a size smaller
 * than the directory held while every header on disk counted it correctly.
 */
function setSizesStatedInComments(sources: readonly ScannedSource[]): StatedSetSize[] {
  const stated: StatedSetSize[] = [];
  for (const source of sources) {
    for (const paragraph of commentParagraphs(source.contents)) {
      for (const sentence of paragraph.prose.split(/(?<=\.)\s+/)) {
        if (!NAMES_THE_SET.test(sentence)) continue;
        for (const match of sentence.matchAll(COUNTED_MEMBERS)) {
          const spelled = SPELLED_CARDINALS[match[1].toLowerCase()];
          stated.push({
            file: source.file,
            line: paragraph.line,
            phrase: match[0],
            size: spelled ?? Number(match[1]),
          });
        }
      }
    }
  }
  return stated;
}

/** The sources whose comments describe the set: this package's own and the set's. */
function sourcesThatDocumentTheSet(): ScannedSource[] {
  const own = packageSources().filter((file) => file.endsWith('.ts'));
  const members = migrationFiles().filter((file) => file.includes(TRADE_RECORD_MIGRATION_MARKER));
  return [...own, ...members].map((file) => ({
    file,
    contents: readRepositoryFile(file),
  }));
}

/**
 * A source as prose: comment openers gone, a string broken across lines joined
 * back into the sentence it is, whitespace flat.
 *
 * Written because the four sentences F43 found were in four shapes at once. Two
 * were SQL comments, one was the message a `raise exception` hands a person, and
 * one was the message an assertion prints when it fails, and a scanner that read
 * comments alone would have found half of a defect whose whole point is that the
 * reader is told the wrong thing wherever they meet it. So the prose of a file
 * here is everything written in it for a person to read, however it is quoted.
 *
 * Joining is the part worth stating. A sentence that wraps is two string literals
 * with `+` between them in TypeScript and two adjacent literals in PL/pgSQL, and
 * both are joined with a space, which is where the author's own trailing space
 * already is. What that cannot do is put back together a literal broken inside a
 * word, which nothing in these files does and which would read as two words here.
 */
function proseOf(contents: string): string {
  return contents
    .replace(/\\'/g, '\'')
    .replace(/^\s*(?:--+|\/\/+|\/\*+|\*+\/?|\*+)\s?/gm, ' ')
    .replace(/'\s*\+?\s*\n\s*\+?\s*'/g, ' ')
    .replace(/\s+/g, ' ');
}

/**
 * Every line a phrase starts on in a source, so that a report sends its reader to
 * the sentence rather than to the file.
 *
 * Read over a sliding window of lines rather than off the phrase's first few words,
 * because a sentence that wraps begins on one line and ends on another and because
 * the first few words of one withdrawn claim are the first few words of prose that
 * is not withdrawn at all: `which no default privilege` opens the sentence about a
 * type as well as the one about a routine, and a report that named the line of the
 * first is a round of rework sent to the wrong file. The window is one line wider
 * than the phrase has fragments, so a sentence broken at a different point than
 * the one this list records is still found, and a window is reported only where the
 * phrase does not also fit inside the window starting below it, which is what makes
 * one sentence one line and not a line for every window that covers it.
 */
function linesWhere(contents: string, phrase: string, span: number): number[] {
  const lines = contents.split('\n');
  const window = (index: number): string => proseOf(lines.slice(index, index + span).join('\n'));
  const found: number[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    if (window(index).includes(phrase) && !window(index + 1).includes(phrase)) found.push(index + 1);
  }
  return found;
}

/**
 * Every withdrawn claim about how an object is born that is still written down,
 * named with the file and the line it is written on.
 *
 * Pure over the sources it is handed, so the test below can show it prose the
 * repository does not contain and prove the scanner sees something rather than
 * passing because it looks at nothing.
 */
function withdrawnClaimsStillStanding(sources: readonly ScannedSource[]): string[] {
  const standing: string[] = [];
  for (const source of sources) {
    const prose = proseOf(source.contents);
    for (const claim of WITHDRAWN_BIRTH_CLAIMS) {
      const phrase = claim.spelling.join(' ');
      if (!prose.includes(phrase)) continue;
      const where = linesWhere(source.contents, phrase, claim.spelling.length + 1);
      standing.push(`${source.file}:${where.join(', ') || 'somewhere'} still says "${phrase}" of `
        + `a ${claim.objectClass}, and ${claim.instead}`);
    }
  }
  return standing;
}

/** Every forbidden privilege statement in the migrations, named with its file. */
function blanketPrivilegeStatements(): string[] {
  const found: string[] = [];
  for (const file of migrationFiles()) {
    const statements = statementsOf(readRepositoryFile(file));
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
 * The file of one ticket, as a path relative to the repository root, found by its
 * id and not by its whole name.
 *
 * The rest of a ticket's filename is a slug of its title, and CLAUDE.md lets the
 * generator behind the council artefact rewrite a ticket that is still
 * `status: todo`, which every ticket read here is. A file that cannot be found is
 * thrown rather than reported as an obligation nobody kept: it means the id in
 * `tables.ts` is wrong, and saying "SEEN-062 does not carry its obligation" when
 * no SEEN-062 can be found would send the next reader to edit a file that is not
 * there.
 */
function ticketFile(ticket: string): string {
  if (!repositoryPathExists(TICKETS_DIRECTORY)) {
    throw new Error(
      `There is no ${TICKETS_DIRECTORY} directory under ${REPOSITORY_ROOT}, so a test that reads `
      + 'a ticket as an authority proves nothing.',
    );
  }
  const matches = listRepositoryDirectory(TICKETS_DIRECTORY)
    .filter((name) => name.startsWith(`${ticket}-`) && name.endsWith('.md'));
  if (matches.length !== 1) {
    throw new Error(
      `${matches.length} files in ${TICKETS_DIRECTORY} are named for ${ticket}, and this test `
      + `needs exactly one to read: ${matches.join(', ') || 'none'}. Either the id in `
      + 'CONSTRAINED_NOT_BUYER_PII_COLUMNS names no ticket, or a ticket has been duplicated.',
    );
  }
  return `${TICKETS_DIRECTORY}/${matches[0]}`;
}

/**
 * The acceptance criteria of a ticket file, one string per checkbox, with the box
 * and its tick dropped.
 *
 * The criteria and not the whole file, because the criteria are the definition of
 * done: CLAUDE.md says so, and an obligation written anywhere else in a ticket is
 * a sentence its author may read, where a criterion is one they have to tick. A
 * ticket with no criteria section is thrown for the same reason a missing file is.
 */
function acceptanceCriteriaOf(file: string): string[] {
  const lines = readRepositoryFile(file).split('\n');
  const heading = lines.findIndex((line) => /^##\s+Acceptance criteria\s*$/i.test(line));
  if (heading === -1) {
    throw new Error(
      `${file} has no "## Acceptance criteria" heading, so this test cannot read its definition `
      + 'of done and proves nothing about what its author is held to.',
    );
  }
  const criteria: string[] = [];
  for (const line of lines.slice(heading + 1)) {
    if (line.startsWith('## ')) break;
    const item = /^\s*-\s*\[[ xX]\]\s*(.+?)\s*$/.exec(line);
    if (item !== null) criteria.push(item[1] as string);
  }
  if (criteria.length === 0) {
    throw new Error(
      `${file} states no acceptance criteria under its own heading, so this test proves nothing `
      + 'about what its author is held to.',
    );
  }
  return criteria;
}

/**
 * Whether one criterion carries every term of an obligation.
 *
 * Whole words, so that `detail` is not found inside `detailed` and `digest` is not
 * found inside a hyphenated neighbour, and case-insensitively, so that writing
 * `message-id` rather than `Message-ID` is a spelling and not a failure. The terms
 * are required together in one criterion rather than anywhere in the ticket, which
 * is what keeps them about a single sentence: SEEN-062 already speaks of hashing
 * an attachment, and a criterion about that plus a criterion mentioning a buyer is
 * not the obligation.
 */
function carriesEveryTerm(criterion: string, terms: readonly string[]): boolean {
  return terms.every((term) => {
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`(^|[^\\w-])${escaped}([^\\w-]|$)`, 'i').test(criterion);
  });
}

/** The ticket files the obligation guard reads as an authority, deduplicated. */
function constrainedTicketFiles(): string[] {
  const tickets = new Set(
    Object.values(CONSTRAINED_NOT_BUYER_PII_COLUMNS).flatMap((entry) => entry.tickets),
  );
  return [...tickets].sort().map(ticketFile);
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

  it('would see a partitioned table a later migration added, and its partitions', async () => {
    // A partitioned table is a table in the public schema and answers to `relkind
    // = 'p'`, so every guard above that asks for `relkind = 'r'` alone walks past
    // one: it is not listed, it is not asked for a tenant_id column, it is not
    // asked whether row-level security is on, and none of its policies is read.
    // That is the fifth Codex review of SEEN-008 (F29), and it is the distance
    // between criterion 2's sentence, "every table in the public schema", and what
    // the guards were actually asserting.
    //
    // The partition is asserted beside the parent, and it is not the same question
    // asked twice. A partition is a relation in its own right and answers to `'r'`,
    // so the guards see it already, and it needs its own enabled policy rather than
    // inheriting the parent's. Measured against this stack in a rolled-back
    // transaction: enabling row-level security on the parent leaves
    // `relrowsecurity` false on the partition, the policy created on the parent is
    // the parent's alone in `pg_policies`, and `authenticated` reading the
    // partition directly with select granted on it sees both tenants' rows while
    // the same role reading through the parent sees one tenant's. So both have to
    // be named, and this is the run that shows them being named.
    await client.query('begin');
    try {
      await client.query(
        'create table public.seen_partitioned_probe ('
        + 'recorded_at timestamptz not null, note text) partition by range (recorded_at)',
      );
      await client.query(
        'create table public.seen_partition_probe partition of public.seen_partitioned_probe '
        + "for values from ('2026-01-01') to ('2027-01-01')",
      );
      const probes = ['seen_partition_probe', 'seen_partitioned_probe'];
      // Each guard answers with either a bare relation name or a name followed by
      // the way it failed, so a probe counts as named by either shape.
      const probesAmong = (entries: readonly string[]): string[] => probes.filter(
        (probe) => entries.some((entry) => entry === probe || entry.startsWith(`${probe}:`)),
      );
      const seen = {
        listed: probesAmong(await tablesIn(client, 'public')),
        withoutTenantId: probesAmong(await tenantIdGapsIn(client, 'public')),
        withoutRowLevelSecurity: probesAmong(await rlsGapsIn(client, 'public')),
        unboundByAPolicy: probesAmong(await tenancyGapsIn(client, 'public')),
      };
      expect(
        seen,
        'A partitioned table carrying neither tenant_id nor row-level security was added to the '
        + 'public schema with one partition under it, and the guards named '
        + `${JSON.stringify(seen)}. Each of the four owes both names: the parent because a query `
        + "through it returns every partition's rows under the parent's own policy, and the "
        + 'partition because a query against the partition itself is governed by the partition\'s '
        + "policies and never by the parent's",
      ).toEqual({
        listed: probes,
        withoutTenantId: probes,
        withoutRowLevelSecurity: probes,
        unboundByAPolicy: probes,
      });
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
    //
    // What is measured is what each role can do, not what each table's access
    // control list says, and the two are not the same question: the second misses
    // a grant to PUBLIC, a grant on one column and a privilege held through
    // membership of another role. So a holding here can name columns, and
    // "SELECT (buyer_name)" is not "SELECT" and is not what any role is meant to
    // hold on anything.
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

  it('would see a select granted to PUBLIC, which names no role and gives it to every one',
    async () => {
      // F30. `grant ... to public` lands in the relation's own access control list
      // as a grantee with no role behind it, so a guard reading that list for
      // `anon`, `authenticated` and `service_role` by name walks past the one grant
      // that hands the privilege to all three at once. The question the assertion
      // above means to ask is what a role can do, and a relation's access control
      // list is not that question. `has_table_privilege` is, and it is what the
      // append-only guard on `audit_events` further down this file has asked all
      // along: it accounts for a grant to PUBLIC, for a privilege held through
      // membership of another role, and for the owner's own rights.
      //
      // What a select to PUBLIC breaks here is the privilege half of the boundary
      // and not the row half: the tenancy policy still yields `anon` no rows,
      // because it carries no claim. That half is the whole reason `anon` holds no
      // select on a table it could read nothing through, and the reason is written
      // at `TABLE_PRIVILEGES`: a table that later loses its policy must not also be
      // readable by a caller who never signed in. The probe on a view at the end of
      // this file is where the rows themselves cross, because no policy stands
      // behind the privilege there at all.
      await client.query('begin');
      try {
        await client.query('grant select on public.shipments to public');
        const measured = {
          privilegesTheGuardReportsForAnon:
            (await privilegesIn(client, 'public')).get('shipments|anon') ?? [],
          theDatabaseAnsweredAnon: await answeredAs(
            client, 'anon', 'select tenant_id from public.shipments',
          ),
        };
        expect(
          measured,
          'A select on public.shipments was granted to PUBLIC, so `anon` holds it without being '
          + 'named anywhere, and the database answered its read '
          + `${JSON.stringify(measured.theDatabaseAnsweredAnon)} where a role holding nothing at `
          + 'all is refused 42501. The privilege guard has to report the select, or the one grant '
          + 'that gives a privilege to every role at once is the one grant it cannot see',
        ).toEqual({
          privilegesTheGuardReportsForAnon: ['SELECT'],
          theDatabaseAnsweredAnon: { answer: 'accepted', rows: 0 },
        });
      } finally {
        await client.query('rollback');
      }
    });

  it('would see a select granted on one column, which is in no relation\'s access control list',
    async () => {
      // The other half of F30, and the one a relation's own access control list
      // cannot answer even in principle: a column grant is filed in
      // `pg_attribute.attacl` and `pg_class.relacl` is not touched by it at all. So
      // the table reads as holding nothing for `anon` while `anon` reads a buyer's
      // name out of it. A table-level answer does not see it either, which is why
      // the guard has to ask `has_column_privilege` of every column of every
      // relation as well as `has_table_privilege` of the relation.
      await client.query('begin');
      try {
        await client.query('grant select (buyer_name) on public.shipments to anon');
        const measured = {
          privilegesTheGuardReportsForAnon:
            (await privilegesIn(client, 'public')).get('shipments|anon') ?? [],
          theBuyerNameColumn: await answeredAs(
            client, 'anon', 'select buyer_name from public.shipments',
          ),
          everyOtherColumn: await answeredAs(client, 'anon', 'select * from public.shipments'),
        };
        expect(
          measured,
          'A select on public.shipments.buyer_name alone was granted to `anon`, and the database '
          + `answered its read of that column ${JSON.stringify(measured.theBuyerNameColumn)} and `
          + `its read of the rest ${JSON.stringify(measured.everyOtherColumn)}. The grant is `
          + 'therefore real and usable and the table\'s own access control list is unchanged by '
          + 'it, so a guard that reads that list reports a boundary that is open',
        ).toEqual({
          privilegesTheGuardReportsForAnon: ['SELECT (buyer_name)'],
          theBuyerNameColumn: { answer: 'accepted', rows: 0 },
          everyOtherColumn: { answer: '42501', rows: null },
        });
      } finally {
        await client.query('rollback');
      }
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

  it('says which ticket owes it, wherever not buyer PII is a constraint and not an observation',
    async () => {
      // F31: `message_threads.external_thread_id` was classified not buyer PII
      // because "an identifier the rail assigned, not anything a buyer wrote",
      // and on the mail rail that is false. A thread opened by a buyer is
      // identified by the root Message-ID their own mail system generated, which
      // carries the sending host on the right of the at sign and a local part
      // their client chose. `messages.external_message_id` said the same thing
      // and had it worse, because every inbound mail message carries one rather
      // than only the thread root. The column stays not buyer PII because
      // SEEN-062 stores a digest of the Message-ID and never the id itself, which
      // is a constraint on a ticket nobody has written and not a fact about the
      // schema.
      //
      // No test can tell a true reason from a false one, which is why F31 took
      // five reviews to find. What this can tell is a classification that rests
      // on somebody keeping a promise from one that rests on what the column is,
      // and it requires the first kind to name the ticket the promise falls to.
      // Read in both directions: a listed column whose comment states no
      // obligation has had the promise edited away while the classification
      // stayed, and an unlisted column that states one is a promise nobody is
      // tracking. `audit_events.payload` and `claim_events.detail` were already
      // written this way in part 7, so the shape is the file's own and not new
      // machinery for two columns.
      const columns = await freeTextColumnsIn(client, 'public');
      const byName = new Map(columns.map((column) => [column.column, column]));
      const owed = Object.entries(CONSTRAINED_NOT_BUYER_PII_COLUMNS)
        .map(([column, entry]) => [column, entry.tickets] as const);
      assertPopulated(owed.map(([column]) => column), 'the classifications that are obligations');
      const wrong: string[] = [];
      for (const [column, owners] of owed) {
        const row = byName.get(column);
        if (row === undefined) {
          wrong.push(`${column} is not a column of schema public that can hold a sentence`);
          continue;
        }
        if (!row.comment.startsWith(NOT_BUYER_PII_MARKER)) {
          wrong.push(`${column} is no longer classified "${NOT_BUYER_PII_MARKER}"`);
          continue;
        }
        if (!row.comment.includes(CONSTRAINED_NOT_BUYER_PII_MARKER)) {
          wrong.push(
            `${column} does not say "${CONSTRAINED_NOT_BUYER_PII_MARKER}", so it reads as a fact `
            + 'about the column when it is a constraint on whoever writes it',
          );
        }
        const unnamed = owners.filter((owner) => !row.comment.includes(owner));
        if (unnamed.length > 0) {
          wrong.push(`${column} names none of ${unnamed.join(', ')} as owing the constraint`);
        }
      }
      expect(
        wrong,
        'Columns whose non-PII classification depends on a later ticket writing them a certain '
        + `way, and whose own comment does not say so or does not name that ticket: ${
          wrong.join('; ')}`,
      ).toEqual([]);

      const unlisted = columns
        .filter((column) => column.comment.startsWith(NOT_BUYER_PII_MARKER)
          && column.comment.includes(CONSTRAINED_NOT_BUYER_PII_MARKER))
        .map((column) => column.column)
        .filter((column) => CONSTRAINED_NOT_BUYER_PII_COLUMNS[column] === undefined);
      expect(
        unlisted,
        'Columns whose comment states an obligation on a later ticket that is tracked nowhere, so '
        + `nothing reads the promise back when that ticket is worked: ${unlisted.join(', ')}`,
      ).toEqual([]);
    });

  it('is carried by the criteria of the ticket that owes it, and not by the comment alone', () => {
    // F34. The assertion above requires the comment to name the ticket and
    // requires the ticket to be told nothing, and a promise the promiser never
    // hears is not one. All four of these classifications were made in a migration
    // no ticket links to, and none of SEEN-027, SEEN-032, SEEN-034 or SEEN-062
    // carried a word of its obligation in its acceptance criteria, which CLAUDE.md
    // makes the definition of done a ticket is worked against. SEEN-062's author
    // would then write the obvious thing, store the Message-ID the Postmark
    // payload hands them, and that value would sit in cleartext for ever with
    // SEEN-083's expiry passing it by, because SEEN-083 reads the classification
    // and the classification says not buyer PII. CLAUDE.md's buyer PII rule broken
    // by construction, with this schema's approval.
    //
    // Amending the tickets is the fix; this is what stops it coming back. All four
    // are `status: todo`, and CLAUDE.md has the plan generator rewriting a ticket
    // at that status, so an amendment can be regenerated away with nobody
    // noticing. If it is, this goes red and names the column that fell with it.
    // The tickets are hashed into the test task below for the same reason the
    // architecture document is: otherwise the cache replays a pass over a ticket
    // the suite never read.
    const owed = Object.entries(CONSTRAINED_NOT_BUYER_PII_COLUMNS);
    assertPopulated(owed.map(([column]) => column), 'the classifications that are obligations');
    const offenders: string[] = [];
    for (const [column, entry] of owed) {
      assertPopulated([...entry.terms], `the terms ${column}'s obligation is recognised by`);
      for (const ticket of entry.tickets) {
        const file = ticketFile(ticket);
        const criteria = acceptanceCriteriaOf(file);
        if (criteria.some((criterion) => carriesEveryTerm(criterion, entry.terms))) continue;
        offenders.push(
          `${column} is classified "${NOT_BUYER_PII_MARKER}" only for as long as ${ticket} `
          + `writes it a certain way, and none of the ${criteria.length} acceptance criteria of `
          + `${file} says ${entry.terms.map((term) => `"${term}"`).join(' and ')}. What that `
          + `ticket owes: ${entry.obligation}. Put it in the criteria rather than here, because `
          + 'the criteria are what its author is held to, and see the column\'s own comment in '
          + 'the migration that classifies it for why. SEEN-008 recorded this as F34.',
        );
      }
    }
    expect(
      offenders,
      'Classifications that rest on a ticket keeping a promise the ticket has never been told '
      + `about: ${offenders.join(' ')}`,
    ).toEqual([]);
  });
});

describe('the migrations that write the schema', () => {
  // Properties of the migrations as files rather than of the database they
  // produce, because each is about what the next migration will do. Counting them
  // here would be one more number in a comment that the file beneath it decides. The end state
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
      //
      // The ticket files of the constrained not-buyer-PII columns joined this list
      // when F34 made them an authority too: the suite now reads SEEN-062's
      // acceptance criteria to decide whether the promise its column comment rests
      // on is carried anywhere its author will see it. Regenerating that criterion
      // away changes nothing under packages/core, so without this the cache would
      // report the guard as passed over a ticket that no longer carries it, which
      // is the precise failure the guard exists to make loud.
      const inputs = testTaskInputs();
      expect(inputs.length, 'turbo reported no inputs at all for @seen/core#test').toBeGreaterThan(0);
      const documents = [...HASHED_REPOSITORY_DOCUMENTS, ...constrainedTicketFiles()];
      const unhashed = documents.filter(
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

  it('would number a new migration into the set without this test being rewritten', () => {
    // The obvious assertion hard-codes the size the directory happens to have and
    // fails the moment a part is added, which punishes the next author for doing the
    // right thing. The size is the number of members found on disk, so the checker
    // is shown a fabricated set of five to prove it: five headers that count five
    // pass, and the same five still reading `of 4` are all named. A file in the
    // directory that is not of this set, the evidence bucket today, is not counted
    // and needs no header.
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

  it('gives its size in the headers and in no comment that could contradict them', () => {
    // F37. `tables.ts` told an author what the set was and gave a size the
    // directory had grown past, while every header on disk counted correctly. The
    // assertion above reads the headers, so it passed, and the prose beside it did
    // not have to be right about anything. That is the same route the counting was
    // made a test for: a reader who believes the smaller number stops before the
    // last part and never reads what it decides. A number written in prose and also
    // computable from disk drifts from it, which this one has done in this package
    // and in the ticket's own Outcome, corrected round after round. So the size
    // belongs in the headers, which are read against the directory, and a comment
    // that gives the set a different one is reported here.
    const size = tradeRecordSetHeaders().length;
    const contradicted = setSizesStatedInComments(sourcesThatDocumentTheSet())
      .filter((stated) => stated.size !== size);
    const named = contradicted.map(
      (stated) => `${stated.file}, comment at line ${stated.line}: "${stated.phrase}"`,
    );
    expect(
      named,
      `The directory holds ${size} members of the set and every header counts them, and these `
      + 'comments hand a reader a different number, which is how the last part of the set goes '
      + `unread: ${named.join('; ')}`,
    ).toEqual([]);
  });

  it('would see a size a comment gave the set, wrapped across lines or not', () => {
    // The assertion above passes over prose nobody has written yet, so the scanner
    // is shown prose this repository does not contain. A count of the members is
    // read whether it is spelled or a numeral and whether or not the line breaks
    // between it and what it counts, and a paragraph counting something other than
    // the set is left alone: part 7 says a comment restated in a pair of migrations
    // is a pair of comments that drift, and that is not a claim about this set.
    const scanned = (prose: string) => [{ file: 'supabase/migrations/2027_x.sql', contents: prose }];
    expect(
      setSizesStatedInComments(scanned(
        '-- Trade record v1, part 9 of 9: a part this ticket does not have.\n'
        + '-- The set is these nine files, and the evidence bucket is not one of them.',
      )).map((stated) => stated.size),
      'A comment naming the set and counting its members is not read, so the assertion above '
      + 'passes by finding nothing rather than by reading the prose',
    ).toEqual([9]);
    expect(
      setSizesStatedInComments(scanned(
        '-- The trade record v1 set is the migrations whose names carry the marker, of\n'
        + '-- which there are 12 files today.',
      )).map((stated) => stated.size),
      'A count written as a numeral, or broken from what it counts by the end of a line, is '
      + 'missed, so the scanner is narrowed by how the last author happened to write it',
    ).toEqual([12]);
    expect(
      setSizesStatedInComments(scanned(
        '-- Trade record v1, part 9 of 9: a part this ticket does not have.\n'
        + '--\n'
        + '-- A comment restated in two migrations is two comments that drift apart.',
      )),
      'A sentence counting something other than the members is read as a size of the set '
      + 'because the preamble it sits in is headed by the name of the set, so the whole of a '
      + 'migration\'s opening comment is answered with numbers that have nothing to do with it',
    ).toEqual([]);
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
 * F28: the refusal above rests on a read, and a read does not see an erasure that
 * has not committed yet.
 *
 * `seen.refuse_erased_tenant_id` asks whether a tombstone exists. At read
 * committed, which is what Postgres defaults to and what the API and the workers
 * run at, that question is answered from a snapshot, and a snapshot holds no row
 * a concurrent transaction has written and not committed. So two sessions can
 * interleave like this:
 *
 *   1. A deletes the tenant. The after-delete trigger writes the tombstone. A has
 *      not committed.
 *   2. B inserts a tenant carrying the same id. The existence check sees no
 *      tombstone, because A's is invisible to it, and lets the insert through.
 *   3. B's insert reaches the primary key, where the row is being deleted by A and
 *      not yet committed, so B waits.
 *   4. A commits. The row is gone and the tombstone stands.
 *   5. B wakes, the key is free, and the insert succeeds.
 *
 * The id is then live and tombstoned at once, which is the state the whole of part
 * 8 exists to make impossible, reached without disabling a trigger or holding the
 * database: two ordinary statements from two ordinary sessions.
 *
 * Two connections, because one cannot say this. A check that passes because
 * another transaction has not committed yet has no single-transaction form: inside
 * one transaction the delete and the insert see each other, and the refusal fires.
 * So the timing is forced rather than hoped for. B's insert is issued without being
 * waited on, and the test then watches `pg_stat_activity` until Postgres reports
 * B's backend waiting on a lock, which is the proof that B is inside the insert and
 * past its guard; only then does A commit. If B never blocks the wait raises rather
 * than carrying on, because a run in which the interleaving did not happen proves
 * nothing and must not read as a pass.
 *
 * This is the one block here whose fixtures are committed, and it has to be: an
 * erasure that is rolled back is not an erasure another session can race. It
 * therefore leaves a tombstone in the registry on every run, permanently, as part 8
 * intends and `assertNoTombstones` describes. That is hygiene and not correctness,
 * for the same reason given there: every id is server-generated and never supplied,
 * so nothing a later run creates can collide with one.
 */
describe('a tenant id being erased by one session while another inserts it', () => {
  /** How long the second session is given to reach its lock wait. It is reached in
   * milliseconds; the allowance is for a loaded machine, not for a hope. */
  const BLOCKED_WITHIN_MS = 10_000;

  let erasing: Client;
  let inserting: Client;
  let observer: Client;
  let insertingPid: number;

  /** What Postgres says the second session's backend is doing, as one string. */
  async function backendState(pid: number): Promise<string> {
    const { rows } = await observer.query<{
      state: string | null; kind: string | null; event: string | null;
    }>(
      `select state, wait_event_type as kind, wait_event as event
         from pg_catalog.pg_stat_activity where pid = $1`,
      [pid],
    );
    const row = rows[0];
    if (!row) return 'gone';
    return `${row.state ?? 'no state'}, waiting on ${row.kind ?? 'nothing'}/${row.event ?? '-'}`;
  }

  /** Blocks until the second session is waiting on a lock, and answers what it is
   * waiting on. Raises rather than returning when it never blocks, because the
   * interleaving is the whole of what this test measures. */
  async function waitUntilBlocked(pid: number): Promise<string> {
    const deadline = Date.now() + BLOCKED_WITHIN_MS;
    let last = 'nothing at all';
    while (Date.now() < deadline) {
      const { rows } = await observer.query<{ kind: string | null; event: string | null }>(
        `select wait_event_type as kind, wait_event as event
           from pg_catalog.pg_stat_activity where pid = $1`,
        [pid],
      );
      const row = rows[0];
      if (row?.kind === 'Lock') return `${row.kind}/${row.event ?? '-'}`;
      last = await backendState(pid);
      await new Promise((resume) => { setTimeout(resume, 20); });
    }
    throw new Error(
      `The second session never blocked within ${BLOCKED_WITHIN_MS}ms, so it did not attempt its `
      + 'insert while the erasure was uncommitted and this test proves nothing about the race. '
      + `Postgres reported its backend as: ${last}.`,
    );
  }

  /** A committed tenant, because an erasure that is rolled back is not one another
   * session can race. */
  async function seedCommitted(name: string): Promise<string> {
    const { rows } = await observer.query<{ tenant_id: string }>(
      'insert into public.tenants (name) values ($1) returning tenant_id',
      [name],
    );
    return rows[0].tenant_id;
  }

  /** How many rows of `relation` carry this id, read on the third connection so
   * that neither session's open transaction decides the answer. */
  async function rowsFor(relation: string, tenant: string): Promise<number> {
    const { rows } = await observer.query<{ total: string }>(
      `select count(*) as total from ${relation} where tenant_id = $1`,
      [tenant],
    );
    return Number(rows[0].total);
  }

  beforeAll(async () => {
    [erasing, inserting, observer] = await Promise.all([connect(), connect(), connect()]);
    const present = await tablesIn(observer, 'public');
    if (!present.includes('tenants')) {
      throw new Error(
        'This test cannot say anything about two sessions racing over a tenant id: '
        + 'public.tenants does not exist. Apply the trade record migrations with `pnpm db:reset`.',
      );
    }
    const { rows } = await inserting.query<{ pid: number }>('select pg_backend_pid() as pid');
    insertingPid = rows[0].pid;
  });

  afterAll(async () => {
    await Promise.all([erasing?.end(), inserting?.end(), observer?.end()]);
  });

  it('is refused the insert that passed its guard before the erasure committed', async () => {
    const tenant = await seedCommitted('Tenant erased while a second session inserts it');
    let theInsert = 'not attempted';
    let waitedOn = 'not observed';
    let measured: Record<string, unknown> = {};
    try {
      await erasing.query('begin');
      await erasing.query('set local role service_role');
      await erasing.query('delete from public.tenants where tenant_id = $1', [tenant]);

      await inserting.query('begin');
      await inserting.query('set local role service_role');
      // So that a fix which blocks for ever fails as a lock wait rather than as a
      // test that hangs. Longer than the erasure is ever held for here.
      await inserting.query("set local lock_timeout = '30s'");
      // Deliberately not awaited: it has to be in flight while the erasure is
      // uncommitted. The outcome is captured on the promise itself, so a refusal
      // is a value this test reads rather than an unhandled rejection.
      const attempt = inserting
        .query('insert into public.tenants (tenant_id, name) values ($1, $2)',
          [tenant, 'Tenant put back by the second session'])
        .then(() => 'accepted')
        .catch((error) => (error as { code?: string }).code ?? (error as Error).message);

      waitedOn = await waitUntilBlocked(insertingPid);
      await erasing.query('commit');
      theInsert = await attempt;
      await inserting.query(theInsert === 'accepted' ? 'commit' : 'rollback');

      measured = {
        theInsert,
        liveRowsAfterwards: await rowsFor('public.tenants', tenant),
        tombstones: await rowsFor(ERASURE_REGISTRY_TABLE, tenant),
      };
    } finally {
      await erasing.query('rollback').catch(() => undefined);
      await inserting.query('rollback').catch(() => undefined);
      await observer
        .query('delete from public.tenants where tenant_id = $1', [tenant])
        .catch(() => undefined);
    }
    expect(
      measured,
      `The second session's insert of an id the first session was erasing was ${theInsert}, `
      + `leaving ${measured.liveRowsAfterwards} tenant rows carrying that id and `
      + `${measured.tombstones} tombstones for it. The interleaving was forced rather than `
      + `hoped for: Postgres reported the second session waiting on ${waitedOn} while the `
      + 'erasure was uncommitted, and the erasure committed only once it was. A refusal (23001) '
      + 'is the only answer that keeps the id from being live and tombstoned at once; an '
      + 'accepted insert is the existence check reading a snapshot taken before the erasure it '
      + 'exists to see',
    ).toEqual({ theInsert: '23001', liveRowsAfterwards: 0, tombstones: 1 });
  }, 40_000);
});

/**
 * F42: the lock serialises two sessions, and a snapshot older than both of them
 * is not something serialising can repair.
 *
 * The pair above take the same advisory lock, so the registry is never read while
 * an erasure of that id is open. That closes the window in which the erasure is
 * uncommitted and says nothing about a session whose snapshot was taken before
 * the erasure began: the lock is free by the time such a session asks for it, and
 * waiting for nobody refreshes nothing. Measured against this stack, as
 * `service_role` on both sides, with a second session at repeatable read:
 *
 *   1. The second session begins and counts `public.tenants`, which pins the one
 *      snapshot it has for its whole life. The id does not exist yet, and neither
 *      does the transaction that will create it.
 *   2. The first session creates a tenant and commits, writes an audit event for
 *      it, erases it and commits. The tombstone stands and the audit event went
 *      with the tenant, as part 2 intends.
 *   3. The second session inserts that tenant id. The advisory lock is free, the
 *      existence test reads a snapshot older than the tombstone, and the primary
 *      key finds no live tuple to conflict with because the row it would have
 *      conflicted with is committed-deleted. Accepted.
 *
 * The id is then live and tombstoned at once with no audit events behind it,
 * which is the state the whole of part 8 exists to make impossible, reached by
 * two ordinary sessions with nothing disabled and nothing held.
 *
 * The distinction that decides what a fix has to do, because it is what tells
 * this apart from a race the database already refuses: a snapshot pinned while
 * the row still exists is not this. There the erasure's delete conflicts with the
 * second session's insert, Postgres refuses it with 40001, and the id is not
 * resurrected. What this needs is a snapshot older than the id's creation, so
 * that the insert has no conflicting tuple and the existence test has no
 * tombstone in view.
 *
 * Both levels that give a transaction one snapshot for its whole life are asked,
 * and serialisable is the point rather than thoroughness: it is the level a
 * caller reaches for in order to be safe, and it was measured accepting this
 * ordering too, so the hole is not a read-committed one that a stricter caller
 * escapes. Read committed is absent because it takes a fresh snapshot per
 * statement, which is the block above.
 *
 * The ordering is forced rather than hoped for, and the forcing is asserted with
 * everything else: the second session reports the xmax of its snapshot and the
 * first reports the transaction id that creates the tenant, and a run in which
 * the creating transaction was already in the reader's snapshot has not measured
 * this defect and must not read as a pass.
 *
 * Committed fixtures, as the block above and for the same reason: an erasure that
 * is rolled back is not one another session can race. Each case therefore leaves
 * one permanent tombstone per run, which is what part 8 intends and what
 * `assertNoTombstones` describes.
 */
describe('a tenant id created and erased after another session pinned its snapshot', () => {
  /** The two isolation levels that pin one snapshot for a whole transaction,
   * spelled as Postgres spells them. */
  const PINNING_LEVELS = ['repeatable read', 'serializable'] as const;

  let pinned: Client;
  let spending: Client;
  let observer: Client;

  /** How many rows of `relation` carry this id, read on a third connection so
   * that neither session's transaction decides the answer. */
  async function rowsFor(relation: string, tenant: string): Promise<number> {
    const { rows } = await observer.query<{ total: string }>(
      `select count(*) as total from ${relation} where tenant_id = $1`,
      [tenant],
    );
    return Number(rows[0].total);
  }

  /** The ordering above, run at one isolation level, and what an observer sees
   * afterwards. Everything it creates is committed, so the cleanup is explicit. */
  async function raceAPinnedSnapshot(level: string): Promise<Record<string, unknown>> {
    let tenant: string | undefined;
    let theInsert = 'not attempted';
    try {
      // The snapshot this session keeps for its whole life, taken before the
      // transaction that creates the id exists. The count is what pins it; the
      // xmax is what proves when.
      await pinned.query(`begin isolation level ${level}`);
      await pinned.query('set local role service_role');
      const { rows: [snapshot] } = await pinned.query<{ xmax: string }>(
        'select count(*) as tenants, pg_snapshot_xmax(pg_current_snapshot())::text as xmax '
        + 'from public.tenants',
      );

      // The id is created and committed. pg_current_xact_id assigns and reports
      // this transaction's id, which is the number the reader's xmax is read
      // against.
      await spending.query('begin');
      await spending.query('set local role service_role');
      const { rows: [creating] } = await spending.query<{ xid: string }>(
        'select pg_current_xact_id()::text as xid',
      );
      const { rows: [created] } = await spending.query<{ tenant_id: string }>(
        'insert into public.tenants (name) values ($1) returning tenant_id',
        [`Tenant erased under an older ${level} snapshot`],
      );
      tenant = created.tenant_id;
      await spending.query('commit');

      // And spent, with an audit event behind it so that the observer below can
      // tell an erasure from no erasure the way an auditor would.
      await spending.query('begin');
      await spending.query('set local role service_role');
      await spending.query(
        `insert into public.audit_events (tenant_id, event_type, actor)
         values ($1, 'test.written_before_erasure', 'test')`,
        [tenant],
      );
      await spending.query('delete from public.tenants where tenant_id = $1', [tenant]);
      await spending.query('commit');

      try {
        await pinned.query(
          'insert into public.tenants (tenant_id, name) values ($1, $2)',
          [tenant, 'Tenant put back from a snapshot older than its erasure'],
        );
        theInsert = 'accepted';
      } catch (error) {
        theInsert = (error as { code?: string }).code ?? (error as Error).message;
      }
      await pinned.query(theInsert === 'accepted' ? 'commit' : 'rollback');

      return {
        theCreationWasOutsideTheSnapshot: BigInt(creating.xid) >= BigInt(snapshot.xmax),
        theInsert,
        liveRowsAfterwards: await rowsFor('public.tenants', tenant),
        tombstones: await rowsFor(ERASURE_REGISTRY_TABLE, tenant),
        auditEventsBehindIt: await rowsFor('public.audit_events', tenant),
      };
    } finally {
      await pinned.query('rollback').catch(() => undefined);
      await spending.query('rollback').catch(() => undefined);
      if (tenant) {
        await observer
          .query('delete from public.tenants where tenant_id = $1', [tenant])
          .catch(() => undefined);
      }
    }
  }

  beforeAll(async () => {
    [pinned, spending, observer] = await Promise.all([connect(), connect(), connect()]);
    const present = await tablesIn(observer, 'public');
    if (!present.includes('tenants')) {
      throw new Error(
        'This test cannot say anything about an erasure a second session cannot see: '
        + 'public.tenants does not exist. Apply the trade record migrations with `pnpm db:reset`.',
      );
    }
  });

  afterAll(async () => {
    await Promise.all([pinned?.end(), spending?.end(), observer?.end()]);
  });

  for (const level of PINNING_LEVELS) {
    it(`is refused the insert a ${level} snapshot cannot see the tombstone from`, async () => {
      const measured = await raceAPinnedSnapshot(level);
      expect(
        measured,
        `A session at ${level} whose snapshot was pinned before the id existed inserted that `
        + `erased id and was ${measured.theInsert}, leaving ${measured.liveRowsAfterwards} `
        + `tenant rows carrying it, ${measured.tombstones} tombstones for it and `
        + `${measured.auditEventsBehindIt} audit events behind it. Live and tombstoned at once `
        + 'with no audit history is the state part 8 exists to make impossible, and a refusal '
        + '(23001) is the only answer that keeps the id spent. The ordering was forced: the '
        + 'transaction that created the id is outside the reader\'s snapshot '
        + `(${measured.theCreationWasOutsideTheSnapshot}), without which the run measured a `
        + 'reader that could see the erasure all along and proves nothing',
      ).toEqual({
        theCreationWasOutsideTheSnapshot: true,
        theInsert: '23001',
        liveRowsAfterwards: 0,
        tombstones: 1,
        auditEventsBehindIt: 0,
      });
    }, 40_000);
  }
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
  // Every guard above asked pg_catalog for `relkind = 'r'`, and so did part 4's
  // per-table revoke and its self-check. That is an ordinary table and nothing
  // else. Four other relation kinds hold rows, are served by the Data API exactly
  // as a table is, and were invisible to all of it.
  //
  // One of the four has since moved: a partitioned table is a table here, because
  // this schema's tenancy can be written on one and is enforced for a query through
  // it, so it is listed, asked for tenant_id and an enabled policy, and granted what
  // a table is granted. The three left are the ones no policy of this database can
  // govern, and they are governed by a privilege and a place instead.
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

  it('is born unreachable: no client-bound role holds a default privilege on a new object',
    async () => {
      // This is the prevention half and it is the one that closes the hole. With
      // the default access control list of schema public standing, a view is
      // readable by `anon` from the moment `create view` returns, and no statement
      // in the migration that created it says so. The Outcome of the first review
      // named this and left it open as "detection rather than prevention"; a view
      // is what made detection impossible as well, because nothing looked at one.
      //
      // Every class `pg_default_acl` files for this schema is read, not the
      // relations alone: F32 is that this assertion and part 6's revoke were each
      // written about `'r'`, so the EXECUTE Supabase defaults to `anon` and
      // `authenticated` on functions stood untouched and unseen, and F33 is the
      // same sentence again for `'S'`, where Supabase defaults SELECT, UPDATE and
      // USAGE to both roles on every sequence the next migration creates.
      const held = await defaultPrivilegesForClientRolesIn(client, 'public');
      expect(
        held,
        `${held.length} default privileges stand on schema public, so every table, view, `
        + 'materialised view, sequence and function a later migration creates there is born '
        + 'holding them, a view is not subject to row-level security unless it says '
        + '`security_invoker = true`, a sequence holds no row for a policy to be applied to at '
        + 'all, and a `security definer` function is subject to none of them either: '
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

  it('carries no foreign table, for the reason it carries no materialised view', async () => {
    const federated = await foreignTablesIn(client, 'public');
    expect(
      federated,
      `${federated.length} foreign tables are in the public schema. A foreign table's rows are `
      + 'on another server, so no policy of this database governs which of them a caller sees, '
      + 'no tenant_id column on one is a claim this database can check, and part 5\'s reference '
      + 'to public.tenants cannot be written on one at all: ' + federated.join('; '),
    ).toEqual([]);
  });

  it('counts a partitioned table as a table, and not as a relation that is not one', async () => {
    // The other half of F29, and the reason the fix is not `('r', 'p')` pasted into
    // every filter in the suite. The guards read this schema as two families. One
    // is the relations whose rows this database's own policies govern, which owe a
    // tenant_id column, an enabled policy that names the tenant, and exactly the
    // privileges the trade record intends. The other is the relations whose rows
    // those policies cannot reach, which owe a browser-bound role nothing at all.
    //
    // A partitioned table is in the first family: `enable row level security` and
    // `create policy` are both accepted on one, and the policy is applied to every
    // row a query through it returns. A foreign table is not, because its rows are
    // on another server that no policy of this database governs, and a materialised
    // view cannot be, which is why part 6 keeps one out of `public` rather than
    // asking it for a policy.
    //
    // The two families have to agree about a partitioned table, and while it sat in
    // the second they could not: the table guard would require `authenticated` to
    // hold select on one exactly as on any other table, and the guard on the
    // relations that are not tables would report that same select as a privilege a
    // browser-bound role must not hold.
    await client.query('begin');
    try {
      await client.query(
        'create table public.seen_governed_partition_probe ('
        + 'tenant_id uuid not null, recorded_at timestamptz not null) '
        + 'partition by range (recorded_at)',
      );
      await client.query(
        'alter table public.seen_governed_partition_probe enable row level security',
      );
      await client.query(
        'create policy tenant_isolation on public.seen_governed_partition_probe '
        + 'for all to authenticated using (tenant_id = seen.current_tenant()) '
        + 'with check (tenant_id = seen.current_tenant())',
      );
      await client.query('grant select on public.seen_governed_partition_probe to authenticated');
      const held = await privilegesIn(client, 'public');
      const measured = {
        amongTheRelationsThatAreNotTables: (await nonTableRelationsIn(client, 'public'))
          .filter((relation) => relation.name === 'seen_governed_partition_probe')
          .map(named),
        objectedToByTheirPrivilegeGuard: (await clientPrivilegesOnNonTablesIn(client, 'public'))
          .filter((entry) => entry.startsWith('seen_governed_partition_probe')),
        readByAuthenticatedAsATable: held.get('seen_governed_partition_probe|authenticated') ?? [],
      };
      expect(
        measured,
        'A partitioned table carrying the tenancy policy and the select `authenticated` holds on '
        + 'every other table was added to the public schema, and the guards answered '
        + `${JSON.stringify(measured)}. It is a table here: the guard on the relations that are `
        + 'not tables must not name it, must not report its select as a privilege no '
        + 'browser-bound role may hold, and the privilege guard on the tables must be the one '
        + 'that reads it',
      ).toEqual({
        amongTheRelationsThatAreNotTables: [],
        objectedToByTheirPrivilegeGuard: [],
        readByAuthenticatedAsATable: [...TABLE_PRIVILEGES.authenticated],
      });
    } finally {
      await client.query('rollback');
    }
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

  it('states its rules as checks that pass when they are replayed against this schema',
    async () => {
      // The mechanism the test below rests on, asserted on its own so that the two
      // failures read differently. Part 6 states each of its rules as a `do` block
      // that raises, and the suite runs those blocks rather than restating them,
      // so a block the extractor mangles or a rule this schema has drifted out of
      // would otherwise be reported as "a foreign table was accepted" when it was
      // nothing of the kind.
      await client.query('begin');
      try {
        const raised = await replayedAgainstTheSchema(
          client, migrationNamed(RELATION_RULE_MIGRATION_MARKER),
        );
        expect(
          raised,
          'Part 6 replayed against the schema its own migration set left behind raised: '
          + `${raised}. Either the schema has drifted out of a rule this file states, or the `
          + 'blocks are being read out of the file wrongly, and until this passes the test '
          + 'below proves nothing about a foreign table',
        ).toBeNull();
      } finally {
        await client.query('rollback');
      }
    });

  it('refuses a foreign table in public, as it refuses a materialised view', async () => {
    // The seventh review of SEEN-008 (F35). The finding is about a rule and not
    // about a route out: the privilege half was measured closed, because
    // `defaclobjtype = 'r'` covers a foreign table as surely as a view, so one
    // created here is born holding nothing for either browser-bound role, and the
    // guard above catches a `grant select` a later migration writes by hand. What
    // was open is that no statement anywhere forbade the relation itself, while
    // `tables.ts` told the next reader that its rule was the materialised view's,
    // which is that it does not belong in a schema the Data API serves.
    //
    // The three refusals measured below are why that is the only honest rule rather
    // than the strict one. A foreign table cannot carry this schema's tenancy at
    // all, which is also what makes criterion 2's exclusion of the kind sound
    // rather than convenient; it cannot carry part 5's reference to
    // `public.tenants`, so an erased tenant's rows in one are outside part 8's
    // cascade altogether; and `information_schema.tables` reports it in the public
    // schema regardless, as FOREIGN beside the twenty-nine BASE TABLEs, where
    // `service_role`, the role every worker and API call in this product connects
    // as, reads it unfiltered and no policy narrows what it sees.
    //
    // Planted through `postgres_fdw` over a server that is named and never
    // connected to, because `create foreign table` contacts nothing: the relation
    // exists in this catalogue the moment the statement returns, which is the whole
    // of what the rule is about. The extension, the server and the relation are all
    // created inside the transaction and go with its rollback.
    //
    // The extension goes in `extensions` and not in `public`, and that is a
    // measurement rather than tidiness. `create extension postgres_fdw` with no
    // schema clause puts its five routines in `public`, owned by `supabase_admin`
    // and carrying `anon=X/supabase_admin`, and part 6 raises on them - so a probe
    // that put it there would be reporting F32's rule working rather than anything
    // about a foreign table. Worth knowing on its own account, because `revoke` by
    // this role answers "no privileges could be revoked" as a warning and not an
    // error there; that is the `supabase_admin` grantor limit part 6 states, and an
    // ordinary `create extension` is a route to it. It is not this finding.
    await client.query('begin');
    try {
      await client.query('create extension if not exists postgres_fdw with schema extensions');
      await client.query(
        'create server seen_warehouse_probe foreign data wrapper postgres_fdw '
        + "options (host 'localhost', port '5432', dbname 'postgres')",
      );
      await client.query(
        'create foreign table public.seen_foreign_table_probe ('
        + 'tenant_id uuid not null, total_cents bigint not null) '
        + "server seen_warehouse_probe options (schema_name 'reporting', table_name 'orders')",
      );
      const { rows } = await client.query<{ table_type: string }>(
        'select table_type from information_schema.tables '
        + 'where table_schema = $1 and table_name = $2',
        ['public', 'seen_foreign_table_probe'],
      );
      const measured = {
        informationSchemaCallsIt: rows[0]?.table_type ?? 'nothing at all',
        enableRowLevelSecurity: await refusedWith(
          client, 'alter table public.seen_foreign_table_probe enable row level security',
        ),
        createPolicy: await refusedWith(
          client, 'create policy tenant_isolation on public.seen_foreign_table_probe '
          + 'for all to authenticated using (tenant_id = seen.current_tenant())',
        ),
        referenceToTenants: await refusedWith(
          client, 'alter table public.seen_foreign_table_probe add constraint tenant_fk '
          + 'foreign key (tenant_id) references public.tenants (id) on delete cascade',
        ),
        theGuardReports: await foreignTablesIn(client, 'public'),
        partSixRaised: await replayedAgainstTheSchema(
          client, migrationNamed(RELATION_RULE_MIGRATION_MARKER),
        ),
      };
      expect(
        measured,
        'A foreign table was created in the public schema and the database answered '
        + `${JSON.stringify(measured)}. It cannot be enabled for row-level security, no policy `
        + 'can be created on it, and it cannot reference public.tenants, so not one of the three '
        + 'guarantees this schema makes about a relation in public can be made about it, and '
        + 'information_schema still reports it there as a table. Part 6 refuses a materialised '
        + 'view for the weaker half of that reason and has to refuse this kind by name too, in '
        + 'the words a later author will read when their migration fails',
      ).toEqual({
        informationSchemaCallsIt: 'FOREIGN',
        enableRowLevelSecurity: '42809',
        createPolicy: '42809',
        referenceToTenants: '0A000',
        theGuardReports: ['seen_foreign_table_probe (a foreign table)'],
        partSixRaised: expect.stringContaining('seen_foreign_table_probe'),
      });
    } finally {
      await client.query('rollback');
    }
  });

  it('would see a select on a view granted to PUBLIC, and the rows it lets through', async () => {
    // F30 on the part 6 half, and this is where the rows actually cross. The
    // assertion above says no client-bound role holds anything on a relation that
    // is not a table, and it reads the view's own access control list to say it, so
    // a grant to PUBLIC satisfies it while every role there is holds the select.
    // The view is deliberately created without `security_invoker = true`, which is
    // how a view is created unless its author knew to say otherwise, so it reads
    // `public.tenants` with its owner's rights and the tenancy policy underneath it
    // is not applied to the request at all: `anon` reads every tenant row there is.
    // The invoker-rights assertion is what objects to that view, and it is a
    // different assertion; what is measured here is that the privilege guard says
    // nothing, and a view carrying `security_invoker = true` and this same grant
    // would pass both while every browser-bound caller could reach it.
    await client.query('begin');
    try {
      await client.query("insert into public.tenants (name) values ('Tenant behind a view')");
      const { rows: counted } = await client.query<{ there: string }>(
        'select count(*)::int as there from public.tenants',
      );
      const tenantRowsThereReally = Number(counted[0].there);
      await client.query(
        'create view public.seen_public_grant_view_probe as '
        + 'select tenant_id, name from public.tenants',
      );
      await client.query('grant select on public.seen_public_grant_view_probe to public');
      const reported = (await clientPrivilegesOnNonTablesIn(client, 'public'))
        .filter((entry) => entry.startsWith('seen_public_grant_view_probe'));
      const read = await answeredAs(
        client, 'anon', 'select name from public.seen_public_grant_view_probe',
      );
      const measured = {
        privilegesTheGuardReportsOnTheProbe: reported.length,
        rowsAnonReadThroughIt: read.rows,
        tenantRowsThereReally,
      };
      expect(
        measured,
        'A select on a view over public.tenants was granted to PUBLIC, and `anon` answered '
        + `${JSON.stringify(read)}, reading ${read.rows} of the ${tenantRowsThereReally} tenant `
        + 'rows that exist through a view that is not subject to their row-level security. The '
        + `guard reported ${reported.join('; ') || 'nothing at all'}: it has to report the select `
        + '`anon` and `authenticated` both hold, which is two entries, one per browser-bound role',
      ).toEqual({
        privilegesTheGuardReportsOnTheProbe: 2,
        rowsAnonReadThroughIt: tenantRowsThereReally,
        tenantRowsThereReally,
      });
    } finally {
      await client.query('rollback');
    }
  });

  it('would see a select on one column of a view, which its own access control list omits',
    async () => {
      // The same on the route no relation's access control list records at all. The
      // grant names `anon` outright here, so there is no question of a grantee the
      // guard failed to recognise: the entry is filed against the column and the
      // view's list stays empty, and a guard reading that list reports a relation
      // no browser-bound role can reach while `anon` reads a tenant's name out of
      // it.
      await client.query('begin');
      try {
        await client.query("insert into public.tenants (name) values ('Tenant behind a column')");
        const { rows: counted } = await client.query<{ there: string }>(
          'select count(*)::int as there from public.tenants',
        );
        const tenantRowsThereReally = Number(counted[0].there);
        await client.query(
          'create view public.seen_column_grant_view_probe as '
          + 'select tenant_id, name from public.tenants',
        );
        await client.query('grant select (name) on public.seen_column_grant_view_probe to anon');
        const reported = (await clientPrivilegesOnNonTablesIn(client, 'public'))
          .filter((entry) => entry.startsWith('seen_column_grant_view_probe'));
        const read = await answeredAs(
          client, 'anon', 'select name from public.seen_column_grant_view_probe',
        );
        const measured = {
          privilegesTheGuardReportsOnTheProbe: reported.length,
          rowsAnonReadThroughIt: read.rows,
          tenantRowsThereReally,
        };
        expect(
          measured,
          'A select on one column of a view over public.tenants was granted to `anon`, and it '
          + `answered ${JSON.stringify(read)}, reading ${read.rows} of the `
          + `${tenantRowsThereReally} tenant rows that exist. The guard reported `
          + `${reported.join('; ') || 'nothing at all'}: a column grant is filed in `
          + 'pg_attribute.attacl and never in pg_class.relacl, so it has to be asked for column '
          + 'by column or it is invisible to the assertion that says a browser-bound role holds '
          + 'nothing here',
        ).toEqual({
          privilegesTheGuardReportsOnTheProbe: 1,
          rowsAnonReadThroughIt: tenantRowsThereReally,
          tenantRowsThereReally,
        });
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

  it('would see a default privilege granted to PUBLIC, and the table born readable by it',
    async () => {
      // F30 reaches this assertion too, and this is the third inventory it does:
      // the rule that a relation is born holding nothing for a browser-bound role
      // is read out of `pg_default_acl` by grantee name, so `alter default
      // privileges ... to public` satisfies it while the next table, view or
      // materialised view is born readable by every role there is.
      //
      // `has_table_privilege` cannot be the answer here, because there is no
      // relation yet to ask it about: a default privilege is a statement about
      // objects that do not exist, and `pg_default_acl` is the only place it is
      // written. What the guard can do is stop reading the grantee as a name, and
      // PUBLIC is filed as grantee 0, which `regrole` renders as a hyphen and no
      // role is spelled that way.
      //
      // The table is created inside the probe and carries no policy, which is how
      // a table is created unless its migration says otherwise, so the row crosses
      // rather than being held back by a tenancy the probe supplied for it.
      await client.query('begin');
      try {
        await client.query(
          'alter default privileges in schema public grant select on tables to public',
        );
        await client.query(
          'create table public.seen_born_readable_probe (tenant_id uuid not null)',
        );
        await client.query(
          'insert into public.seen_born_readable_probe (tenant_id) values (gen_random_uuid())',
        );
        const held = await defaultPrivilegesForClientRolesIn(client, 'public');
        const measured = {
          defaultPrivilegesTheGuardReports: held.length,
          theDatabaseAnsweredAnon: await answeredAs(
            client, 'anon', 'select tenant_id from public.seen_born_readable_probe',
          ),
        };
        expect(
          measured,
          'A select on every table created in schema public was granted by default to PUBLIC, a '
          + 'table was then created there, and `anon` answered '
          + `${JSON.stringify(measured.theDatabaseAnsweredAnon)}, reading a row of a table it was `
          + `never granted anything on. The guard reported ${held.join('; ') || 'nothing at all'}: `
          + 'it has to report the one default privilege that stands, or the grant that reaches '
          + 'every role at once is the one it cannot see',
        ).toEqual({
          defaultPrivilegesTheGuardReports: 1,
          theDatabaseAnsweredAnon: { answer: 'accepted', rows: 1 },
        });
      } finally {
        await client.query('rollback');
      }
    });
});

describe('the functions in the public schema', () => {
  // One object class over from the describe above, and the same defect in the file
  // that was written to close it. Every privilege guard in this suite, part 4's
  // per-table revoke and part 6's `revoke all on tables` are statements about
  // `defaclobjtype = 'r'` or `relkind`, which is a relation and nothing else. A
  // function is neither, and `supabase/config.toml` names the class it serves in its
  // own comment: "tables, views, sequences and functions". F19's round answered one
  // quarter of that sentence, and the sixth review of SEEN-008 (F32) is the quarter
  // that lets rows out.
  //
  // Measured against this stack in a rolled-back transaction with two tenants
  // inserted, before this block existed. `pg_default_acl` for schema public, type
  // `'f'`, read `{postgres=X/postgres,anon=X/postgres,authenticated=X/postgres,
  // service_role=X/postgres}`, so `create function public.probe_tenant_directory()
  // returns setof text language sql security definer as $$ select name from
  // public.tenants $$` was born `{=X/postgres,postgres=X/postgres,anon=X/postgres,
  // authenticated=X/postgres,service_role=X/postgres}`, `anon` was refused
  // `public.tenants` with SQLSTATE 42501, and `anon` read both tenants' names
  // through the function. Nothing in the suite saw it: every default-privilege query
  // filtered on `'r'` and `has_function_privilege` appeared nowhere in
  // packages/core/db.
  //
  // Why a function is worse than a view rather than the same. A view can be made to
  // read its base tables as the caller and then the tenancy applies; a `security
  // definer` function runs as its owner, no table in this schema carries
  // `relforcerowsecurity`, and the owner of every one of them is the migration role,
  // so there is no option that puts a policy back in the way. And it is the ordinary
  // Supabase pattern: a function in a served schema is a `POST /rpc/<name>`
  // endpoint, which is how SEEN-024's ops console and SEEN-035's approval inbox
  // would write one without ever deciding to publish it.

  let client: Client;

  beforeAll(async () => {
    client = await connect();
  });

  afterAll(async () => {
    await client?.end();
  });

  it('carries no function a browser-bound role can execute', async () => {
    // There is no function in schema public today, which this asserts rather than
    // assumes: the helpers this schema needs are in `seen`, where the Data API does
    // not reach, and part 6 strips whatever it finds here so that the sentence stays
    // true when the migrations are re-applied against a schema that has one. The
    // probes below are what stop this passing by measuring nothing.
    const callable = await executableRoutinesIn(client, 'public');
    expect(
      callable,
      `${callable.length} routines in schema public can be executed by a role a browser request `
      + 'is bound to. Schema public is served by the Data API, so each of them is a POST '
      + '/rpc/<name> endpoint reachable with the anon key, and a `security definer` one runs as '
      + 'its owner, which every policy in this schema assumes a request is never bound to: '
      + callable.join('; '),
    ).toEqual([]);
  });

  it('would see a security definer function a later migration added, and the rows it lends anon',
    async () => {
      // The access and the silence in one measurement, which is what the assertion
      // above is worth nothing without. The function is the one the reproduction
      // used, and the two tenants are inserted here so that the count proves rows
      // crossed a tenant boundary and not merely that a call was accepted.
      //
      // The grant is written here and is the point rather than setup. Until F39 the
      // database supplied this state by itself, so the fixture said nothing and got
      // its hazard from the default privileges every Supabase project ships with;
      // that is exactly what made the suite refuse a working prevention, because a
      // test that needs the unsafe default in order to demonstrate the hazard is a
      // test that requires the unsafe default. The hazard is now created by the
      // three words that create it in the wild: a later ticket's migration writing
      // `grant execute` on its own RPC, which is the ordinary Supabase instruction
      // and the one route into this schema prevention cannot close, because somebody
      // meant it.
      await client.query('begin');
      try {
        await client.query(
          "insert into public.tenants (name) values ('Tenant A'), ('Tenant B')",
        );
        await client.query(
          'create function public.seen_rpc_probe() returns setof text '
          + 'language sql security definer as $$ select name from public.tenants $$',
        );
        await client.query(
          'grant execute on function public.seen_rpc_probe() to anon, authenticated',
        );
        const measured = {
          routinesTheGuardReports: (await executableRoutinesIn(client, 'public'))
            .filter((entry) => entry.includes('seen_rpc_probe')),
          // And what every guard that existed before this round says about the same
          // function, which is the silence half and is not an aside: a function is
          // in neither relation inventory, so the twenty-nine-table privilege guard
          // and the guard on the relations that are not tables both pass over it.
          // These two stay empty after the fix as well, because the answer was never
          // going to come from a relation: it is `has_function_privilege` above or it
          // is nothing.
          whatTheRelationShapedGuardsSay: {
            amongTheRelationsThatAreNotTables: (await nonTableRelationsIn(client, 'public'))
              .filter((relation) => relation.name === 'seen_rpc_probe').map(named),
            reportedByThePrivilegeGuards: [
              ...(await clientPrivilegesOnNonTablesIn(client, 'public'))
                .filter((entry) => entry.includes('seen_rpc_probe')),
              ...((await privilegesIn(client, 'public')).get('seen_rpc_probe|anon') ?? []),
            ],
          },
          anonReadingTheTableDirectly: await answeredAs(
            client, 'anon', 'select name from public.tenants',
          ),
          anonReadingThroughTheFunction: await answeredAs(
            client, 'anon', 'select * from public.seen_rpc_probe()',
          ),
        };
        expect(
          measured,
          'A `security definer` function over public.tenants was created in schema public, as '
          + 'SEEN-024 and SEEN-035 will create one, and the database answered `anon` '
          + `${JSON.stringify(measured.anonReadingTheTableDirectly)} on the table and `
          + `${JSON.stringify(measured.anonReadingThroughTheFunction)} through the function. Two `
          + 'tenants exist, so that is both of them. The guard has to name the function for both '
          + 'browser-bound roles, or the tenancy this ticket writes is undone by a function '
          + 'nothing in the suite looks at',
        ).toEqual({
          routinesTheGuardReports: [
            'public.seen_rpc_probe() is a function running with its owner rights that anon can '
            + 'execute',
            'public.seen_rpc_probe() is a function running with its owner rights that '
            + 'authenticated can execute',
          ],
          whatTheRelationShapedGuardsSay: {
            amongTheRelationsThatAreNotTables: [],
            reportedByThePrivilegeGuards: [],
          },
          anonReadingTheTableDirectly: { answer: '42501', rows: null },
          anonReadingThroughTheFunction: { answer: 'accepted', rows: 2 },
        });
      } finally {
        await client.query('rollback');
      }
    });

  it('is not closed by revoking from public, which is the statement this repository writes',
    async () => {
      // The part that makes F32 high rather than medium. `revoke all on function ...
      // from public` is what part 8 writes five times over its own helpers, and a
      // reader takes it for the statement that makes a function uncallable. It is
      // not: a grant to PUBLIC and a grant to `anon` are two grants, and the default
      // access control list of schema public wrote the second one. Measured step by
      // step here so the file cannot be read the other way again.
      //
      // The default privilege is granted back inside the probe, and that is the
      // point rather than a convenience. Part 6 revoked it, so a function created
      // here now is born naming neither role and `from public` would close it; this
      // restores the half of the shipped default that names the roles, which is the
      // half the statement under test cannot reach. What has to stay true whatever
      // the default is, is that the two statements are not each other's shorthand.
      // The other half of the shipped default, PostgreSQL's grant to PUBLIC, is not
      // restored here and does not need to be: it is what `from public` reaches, and
      // leaving it closed shows that the named grants alone keep `anon` reading.
      await client.query('begin');
      try {
        await client.query(
          "insert into public.tenants (name) values ('Tenant A'), ('Tenant B')",
        );
        await client.query(
          'alter default privileges in schema public '
          + 'grant execute on functions to anon, authenticated',
        );
        await client.query(
          'create function public.seen_rpc_probe() returns setof text '
          + 'language sql security definer as $$ select name from public.tenants $$',
        );
        await client.query('revoke all on function public.seen_rpc_probe() from public');
        const afterRevokingFromPublic = {
          rolesStillNamed: (await routineAccessControlList(client, 'public.seen_rpc_probe()'))
            .clientRolesNamed,
          anonReadingThroughTheFunction: await answeredAs(
            client, 'anon', 'select * from public.seen_rpc_probe()',
          ),
          routinesTheGuardReports: (await executableRoutinesIn(client, 'public'))
            .filter((entry) => entry.includes('seen_rpc_probe')).length,
        };
        await client.query(
          'revoke all on function public.seen_rpc_probe() from anon, authenticated',
        );
        const afterRevokingFromTheRoles = {
          rolesStillNamed: (await routineAccessControlList(client, 'public.seen_rpc_probe()'))
            .clientRolesNamed,
          anonReadingThroughTheFunction: await answeredAs(
            client, 'anon', 'select * from public.seen_rpc_probe()',
          ),
          routinesTheGuardReports: (await executableRoutinesIn(client, 'public'))
            .filter((entry) => entry.includes('seen_rpc_probe')).length,
        };
        expect(
          { afterRevokingFromPublic, afterRevokingFromTheRoles },
          'A `security definer` function over public.tenants was stripped with `revoke all on '
          + 'function ... from public`, the statement this repository already writes, and the '
          + `database answered \`anon\` ${JSON.stringify(afterRevokingFromPublic.anonReadingThroughTheFunction)} `
          + 'afterwards. Revoking from the two named roles as well is what refuses it 42501. The '
          + 'guard has to report the function in the first state and not in the second, or it '
          + 'agrees with the reading of `from public` that leaves both tenants readable',
        ).toEqual({
          afterRevokingFromPublic: {
            rolesStillNamed: ['anon', 'authenticated'],
            anonReadingThroughTheFunction: { answer: 'accepted', rows: 2 },
            routinesTheGuardReports: 2,
          },
          afterRevokingFromTheRoles: {
            rolesStillNamed: [],
            anonReadingThroughTheFunction: { answer: '42501', rows: null },
            routinesTheGuardReports: 0,
          },
        });
      } finally {
        await client.query('rollback');
      }
    });

  it('is born callable by service_role and by no browser-bound role, PUBLIC included',
    async () => {
      // Prevention, whole, where five rounds of this ticket recorded that prevention
      // was impossible. The seventh Codex review of SEEN-008 (F39) is that the
      // impossibility was a property of the statement those rounds tried and not of
      // PostgreSQL: `alter default privileges ... in schema public ... from public`
      // cannot subtract the built-in grant, because the built-in grant is not filed
      // against a schema, and `alter default privileges for role postgres revoke
      // execute on functions from public`, with no `in schema` clause at all, is
      // filed the same way the built-in grant is and does subtract it.
      //
      // Measured on PostgreSQL 17.6 on this stack in a rolled-back transaction,
      // both forms one after the other. With the per-schema form applied on top of
      // part 6's revoke, `pg_default_acl` for schema public read
      // `{postgres=X/postgres,service_role=X/postgres}` and the function created
      // next was still born `{=X/postgres,postgres=X/postgres,service_role=X/postgres}`
      // with `has_function_privilege('anon', ...)` true, which is what notes 154 and
      // 159 recorded and generalised too far. With the global form, `pg_default_acl`
      // gains a row whose `defaclnamespace` is 0, and the function created next is
      // born `{postgres=X/postgres,service_role=X/postgres}` with no PUBLIC entry at
      // all and `anon`, `authenticated` both false.
      //
      // `service_role` is asserted in the same measurement rather than in one of its
      // own, because the two halves are what makes this a fix instead of an outage:
      // the per-schema entry on public still names `service_role`, and the global
      // revoke takes away the built-in grant underneath it without touching it. A
      // version of this that left `service_role` unable to call the next function in
      // public would pass every security assertion in this file and break every RPC
      // the product ever writes.
      await client.query('begin');
      try {
        await client.query(
          'create function public.seen_born_callable_probe() returns int '
          + 'language sql as $$ select 1 $$',
        );
        const measured = {
          ...await routineAccessControlList(client, 'public.seen_born_callable_probe()'),
          whatTheDatabaseSaysAnonCanDo: await canExecute(
            client, 'anon', 'public.seen_born_callable_probe()',
          ),
          whatTheDatabaseSaysServiceRoleCanDo: await canExecute(
            client, 'service_role', 'public.seen_born_callable_probe()',
          ),
        };
        expect(
          measured,
          'A function was created in schema public and its own access control list reads '
          + `${JSON.stringify(measured)}. Neither browser-bound role may be named in it and `
          + 'PUBLIC may not be either, because PUBLIC is the grantee `anon` reaches EXECUTE '
          + 'through and the one the first five rounds of this ticket recorded as unreachable. '
          + '`service_role` must still hold it, or the next function this schema gains answers '
          + 'nothing to the role every worker and API call connects as',
        ).toEqual({
          clientRolesNamed: [],
          publicIsNamed: false,
          whatTheDatabaseSaysAnonCanDo: false,
          whatTheDatabaseSaysServiceRoleCanDo: true,
        });
      } finally {
        await client.query('rollback');
      }
    });

  it('would see a default privilege on functions a later migration granted back', async () => {
    // The prevention half asked of the database rather than of part 6's file. The
    // forbidden-statement scanner refuses `alter default privileges ... grant` in
    // any spelling, and this is the other end of it: the class the scanner would
    // have let through unnoticed for six rounds is the one asserted here.
    await client.query('begin');
    try {
      await client.query(
        'alter default privileges in schema public grant execute on functions to anon',
      );
      const held = await defaultPrivilegesForClientRolesIn(client, 'public');
      expect(
        held.filter((entry) => entry.includes('function')),
        'A default EXECUTE granted back to `anon` on every function created in schema public was '
        + 'not reported, so the prevention assertion covers the relations alone and the next '
        + `function is born callable with the anon key: it reported ${held.join('; ') || 'nothing at all'}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });
});

describe('the sequences in the public schema', () => {
  // The last quarter of one sentence, and the fourth round to find it. Every guard
  // this ticket wrote asked the catalogue for a relation kind or for a routine:
  // `'r'` until F19, the four relation kinds until F29, `'r'` and `'f'` on the
  // privilege records until F32. `supabase/config.toml` names the class it serves in
  // its own comment, "tables, views, sequences and functions", and a sequence is the
  // quarter left. `relkind = 'S'` appeared in no guard in this package and
  // `has_sequence_privilege` appeared nowhere in it either, so there was no filter
  // to widen: there was no question.
  //
  // Measured against this stack in a rolled-back transaction by the sixth review of
  // SEEN-008 (F33). `pg_default_acl` for schema public, type `'S'`, read
  // `{postgres=rwU/postgres,anon=rwU/postgres,authenticated=rwU/postgres,
  // service_role=rwU/postgres}` from both grantors, so a sequence was born holding
  // all three privileges for both browser-bound roles, and `anon` called `nextval`
  // (accepted), read `last_value` and got a count of rows aggregated over every
  // tenant, and called `setval(seq, 1)` (accepted).
  //
  // Why a sequence is its own kind of exposure rather than a relation with a
  // different letter. It holds no row, so row-level security is not a defence that
  // happens to be missing here: there is nothing for a policy to be applied to, and
  // the tenancy this ticket writes has no expression over one. What it holds instead
  // is a number computed from every tenant's rows at once, which is a fact about
  // tenants the caller can name none of; and the write half is not a read at all but
  // a denial of service on the next ingest, which collides on the primary key until
  // the sequence catches up.
  //
  // And no migration here creates one, which is not the safeguard it reads as: a
  // `bigserial` or a `bigint generated by default as identity` column creates
  // `public.<table>_<column>_seq` without the word sequence appearing in the
  // migration, which is how SEEN-014's ingest or SEEN-021's findings would add one
  // without deciding to.

  let client: Client;

  beforeAll(async () => {
    client = await connect();
  });

  afterAll(async () => {
    await client?.end();
  });

  it('carries no sequence a browser-bound role can reach', async () => {
    // There is no sequence in schema public today, which this asserts rather than
    // assumes: every key in this schema is a uuid with a default, so nothing has
    // needed one yet. Part 6 strips whatever it finds, on the same principle as the
    // loops beside it, so the sentence stays true when these migrations are
    // re-applied against a schema somebody has added one to. The probes below are
    // what stop this passing by measuring nothing.
    const reachable = await sequencesReachableIn(client, 'public');
    expect(
      reachable,
      `${reachable.length} sequences in schema public can be reached by a role a browser request `
      + 'is bound to. A sequence holds no row, so no policy of this database is ever applied to '
      + 'one, and what it holds instead is a number derived from every tenant\'s rows: '
      + reachable.join('; '),
    ).toEqual([]);
  });

  it('is born out of reach, and here the revoke is the whole of prevention rather than a bound '
    + 'on it', async () => {
    // The access and the silence in one measurement, and the one assertion in this
    // block that the revoke in part 6 has to be there for. A sequence is created as
    // a later ticket's migration would create one, and the database is asked the
    // three things `anon` was able to do before the fix, beside what every guard
    // that existed before this round says about the same object.
    //
    // The contrast with F32 is why this assertion takes one statement where the one
    // on functions takes two, and it is what a later reader most needs from this
    // block. PostgreSQL grants EXECUTE to PUBLIC on every routine as a baseline, so
    // a function needs the per-schema revoke for the named grants and a second
    // revoke filed against no schema for the built-in one; five rounds of this
    // ticket recorded the second as impossible and the seventh review (F39) showed
    // it is not. PostgreSQL grants a new sequence nothing to PUBLIC, so there is no
    // baseline underneath this revoke and one statement is the whole of it. Measured
    // on PostgreSQL 17.6 on this stack: after the revoke the sequence is born
    // `{postgres=rwU/postgres,service_role=rwU/postgres}` with no PUBLIC entry at
    // all, and all three calls are refused.
    //
    // The identity column is created beside the sequence because it is the route a
    // later ticket actually takes: it names no sequence and creates one.
    await client.query('begin');
    try {
      await client.query('create sequence public.seen_sequence_probe');
      await client.query(
        'create table public.seen_identity_probe ('
        + 'id bigint generated by default as identity primary key, tenant_id uuid not null)',
      );
      const measured = {
        sequencesTheGuardReports: await sequencesReachableIn(client, 'public'),
        // The silence half, and it is not an aside: a sequence is in neither
        // relation inventory, so these two stay empty after the fix as well. The
        // answer was never going to come from a relation-shaped question.
        whatTheRelationShapedGuardsSay: {
          amongTheRelationsThatAreNotTables: (await nonTableRelationsIn(client, 'public'))
            .filter((relation) => relation.name.startsWith('seen_sequence_probe')).map(named),
          reportedByThePrivilegeGuards: [
            ...(await clientPrivilegesOnNonTablesIn(client, 'public'))
              .filter((entry) => entry.includes('seen_sequence_probe')),
            ...((await privilegesIn(client, 'public')).get('seen_sequence_probe|anon') ?? []),
          ],
        },
        anonCallingNextval: await answeredAs(
          client, 'anon', "select nextval('public.seen_sequence_probe')",
        ),
        anonReadingLastValue: await answeredAs(
          client, 'anon', 'select last_value from public.seen_sequence_probe',
        ),
        anonCallingSetval: await answeredAs(
          client, 'anon', "select setval('public.seen_sequence_probe', 1)",
        ),
        anonCallingNextvalOnTheIdentitySequence: await answeredAs(
          client, 'anon', "select nextval('public.seen_identity_probe_id_seq')",
        ),
      };
      expect(
        measured,
        'A sequence and an identity column were created in schema public, as SEEN-014\'s ingest '
        + 'and SEEN-021\'s findings will create one, and the database answered `anon` '
        + `${JSON.stringify(measured.anonCallingNextval)} to nextval, `
        + `${JSON.stringify(measured.anonReadingLastValue)} to last_value, which is a count of `
        + 'rows across every tenant, and '
        + `${JSON.stringify(measured.anonCallingSetval)} to setval, which collides the next `
        + 'ingest insert on the primary key until the sequence catches up. All three have to be '
        + 'refused 42501, because unlike a function a sequence has no built-in grant to PUBLIC '
        + 'underneath the default privilege and the revoke in part 6 is therefore the whole of '
        + 'prevention here. The relation-shaped guards report '
        + `${JSON.stringify(measured.whatTheRelationShapedGuardsSay)}, which is the silence: a `
        + 'sequence is in neither relation inventory and no widening of them would ever see one',
      ).toEqual({
        sequencesTheGuardReports: [],
        whatTheRelationShapedGuardsSay: {
          amongTheRelationsThatAreNotTables: [],
          reportedByThePrivilegeGuards: [],
        },
        anonCallingNextval: { answer: '42501', rows: null },
        anonReadingLastValue: { answer: '42501', rows: null },
        anonCallingSetval: { answer: '42501', rows: null },
        anonCallingNextvalOnTheIdentitySequence: { answer: '42501', rows: null },
      });
    } finally {
      await client.query('rollback');
    }
  });

  it('would see a sequence a browser-bound role can reach, and the tenant-wide number it lends '
    + 'anon', async () => {
    // What the assertion above is worth nothing without, and it keeps measuring
    // something after the fix because it restores the state every Supabase database
    // ships with before it creates the sequence. Two rows are inserted through the
    // owner so that the number `anon` reads is a fact about both tenants and not
    // merely a number.
    //
    // The value is read three times on purpose, and the third reading is the finding
    // rather than a check of the first two. `nextval` and `setval` are outside
    // transaction control: they are not rolled back, so `anon` setting the sequence
    // back to 1 inside a probe that ends in `rollback to savepoint` leaves it at 1
    // afterwards. That is the shape of the damage stated exactly: a read of another
    // tenant's row count that no policy governs, and a write whose effect no
    // rollback undoes, from a caller who never signed in.
    await client.query('begin');
    try {
      await client.query(
        'alter default privileges in schema public '
        + 'grant all on sequences to anon, authenticated',
      );
      await client.query(
        'create table public.seen_identity_probe ('
        + 'id bigint generated by default as identity primary key, tenant_id uuid not null)',
      );
      await client.query(
        'insert into public.seen_identity_probe (tenant_id) '
        + 'values (gen_random_uuid()), (gen_random_uuid())',
      );
      const lastValue = async (): Promise<string> => (await client.query<{ last: string }>(
        'select last_value::text as last from public.seen_identity_probe_id_seq',
      )).rows[0].last;
      const measured = {
        sequencesTheGuardReports: (await sequencesReachableIn(client, 'public'))
          .filter((entry) => entry.includes('seen_identity_probe_id_seq')),
        rowsAcrossBothTenants: await lastValue(),
        anonReadingLastValue: await answeredAs(
          client, 'anon', 'select last_value from public.seen_identity_probe_id_seq',
        ),
        anonCallingSetval: await answeredAs(
          client, 'anon', "select setval('public.seen_identity_probe_id_seq', 1)",
        ),
        valueAnonLeftBehindAfterItsStatementWasRolledBack: await lastValue(),
      };
      expect(
        measured,
        'A `bigint generated by default as identity` column was added in schema public with the '
        + 'default privileges standing, which is the state a later ticket\'s migration writes '
        + 'without naming a sequence at all, and `anon` answered '
        + `${JSON.stringify(measured.anonReadingLastValue)} reading its last value and `
        + `${JSON.stringify(measured.anonCallingSetval)} setting it. The sequence stood at `
        + `${measured.rowsAcrossBothTenants} for two tenants' rows and stands at `
        + `${measured.valueAnonLeftBehindAfterItsStatementWasRolledBack} after anon's statement `
        + 'was rolled back, because setval is outside transaction control. The guard has to name '
        + 'the sequence for both browser-bound roles and all three privileges, or the one object '
        + 'class this suite never asked about is undetectable again',
      ).toEqual({
        sequencesTheGuardReports: [
          'public.seen_identity_probe_id_seq lets anon read its last value, which is a count of '
          + 'rows across every tenant',
          'public.seen_identity_probe_id_seq lets anon set it with setval, which collides the '
          + 'next insert on the primary key',
          'public.seen_identity_probe_id_seq lets anon advance it with nextval',
          'public.seen_identity_probe_id_seq lets authenticated read its last value, which is a '
          + 'count of rows across every tenant',
          'public.seen_identity_probe_id_seq lets authenticated set it with setval, which '
          + 'collides the next insert on the primary key',
          'public.seen_identity_probe_id_seq lets authenticated advance it with nextval',
        ],
        rowsAcrossBothTenants: '2',
        anonReadingLastValue: { answer: 'accepted', rows: 1 },
        anonCallingSetval: { answer: 'accepted', rows: 1 },
        valueAnonLeftBehindAfterItsStatementWasRolledBack: '1',
      });
    } finally {
      await client.query('rollback');
    }
  });

  it('would see a default privilege on sequences a later migration granted back', async () => {
    // The prevention half asked of the database rather than of part 6's file, as the
    // relations and the functions are asked. The forbidden-statement scanner refuses
    // `alter default privileges ... grant` in any spelling; this is the other end of
    // it, on the class that went unnoticed for six rounds.
    await client.query('begin');
    try {
      await client.query(
        'alter default privileges in schema public grant usage on sequences to anon',
      );
      const held = await defaultPrivilegesForClientRolesIn(client, 'public');
      expect(
        held.filter((entry) => entry.includes('sequence')),
        'A default USAGE granted back to `anon` on every sequence created in schema public was '
        + 'not reported, so the prevention assertion covers the relations and the functions '
        + 'alone and the next identity column is born advanceable with the anon key: it '
        + `reported ${held.join('; ') || 'nothing at all'}`,
      ).not.toEqual([]);
    } finally {
      await client.query('rollback');
    }
  });

  it('holds no default privilege on a type either, which is the one class with nothing to '
    + 'revoke', async () => {
    // The fifth letter `defaclobjtype` has, asked because four rounds of this ticket
    // each found the quarter the round before had not looked at, and an unmentioned
    // class is how every one of them got here.
    //
    // Measured on this stack: there is no `'T'` row in `pg_default_acl` for schema
    // public from either grantor, so part 6 writes no revoke for one, and `alter
    // default privileges ... revoke all on types` records nothing when it is run
    // because a revoke of a grant nobody made writes nothing down. `anon` does hold
    // USAGE on every type here through the grant PostgreSQL makes to PUBLIC, which
    // no default privilege can reach, exactly as for a function.
    //
    // That is harmless, and the reason is asserted rather than left in a comment
    // where the next round would have to take it on trust: USAGE on a type is not a
    // route to a row. The probe creates a domain, shows `anon` holding USAGE on it,
    // and shows that the table whose row type `anon` also holds USAGE on is still
    // refused 42501, which is the whole of the distinction. PostgREST serves no type
    // as an endpoint, which is why `config.toml` names four classes and not five.
    await client.query('begin');
    try {
      await client.query("insert into public.tenants (name) values ('Tenant A')");
      await client.query("create domain public.seen_domain_probe as text check (value <> '')");
      const held = await defaultPrivilegesForClientRolesIn(client, 'public');
      const measured = {
        defaultPrivilegesOnTypesTheGuardReports: held.filter((entry) => entry.includes('type')),
        anonHoldsUsageOnTheDomain: (await client.query<{ allowed: boolean }>(
          "select has_type_privilege('anon', 'public.seen_domain_probe', 'USAGE') as allowed",
        )).rows[0].allowed,
        anonHoldsUsageOnTheRowTypeOfATable: (await client.query<{ allowed: boolean }>(
          "select has_type_privilege('anon', 'public.tenants', 'USAGE') as allowed",
        )).rows[0].allowed,
        anonReadingTheTableWhoseRowTypeItHolds: await answeredAs(
          client, 'anon', 'select name from public.tenants',
        ),
      };
      expect(
        measured,
        'A domain was created in schema public and `anon` holds USAGE on it, and on the row type '
        + 'of every table here, through PostgreSQL\'s grant to PUBLIC, which no default privilege '
        + 'can take away. That is not a route to a row and this is where that is shown rather '
        + 'than asserted in prose: the database answered `anon` '
        + `${JSON.stringify(measured.anonReadingTheTableWhoseRowTypeItHolds)} on the table whose `
        + 'row type it holds USAGE on, because reading rows goes through the table privilege part '
        + '4 governs. What is guarded here is that no migration files a default privilege on a '
        + `type: the guard reported ${measured.defaultPrivilegesOnTypesTheGuardReports.join('; ') || 'nothing at all'}`,
      ).toEqual({
        defaultPrivilegesOnTypesTheGuardReports: [],
        anonHoldsUsageOnTheDomain: true,
        anonHoldsUsageOnTheRowTypeOfATable: true,
        anonReadingTheTableWhoseRowTypeItHolds: { answer: '42501', rows: null },
      });
    } finally {
      await client.query('rollback');
    }
  });
});

/**
 * Schema `seen`, which no guard in this package had ever asked anything.
 *
 * Every helper above takes a schema name and every call site passed `public`. That
 * was recorded three times inside this ticket before any finding named it, and
 * what it produced is the second review's F38: `seen.touch_updated_at()` and
 * `seen.refuse_erasure_registry_mutation()` were born with PostgreSQL's EXECUTE to
 * PUBLIC and never revoked, `anon` holds USAGE on this schema from part 1, and so
 * `anon` could name and call both while the suite ran green. They returned
 * `trigger` and answered 0A000, so nothing crossed; the hazard was the next author,
 * who adds a helper here that returns something else and copies the pattern of the
 * functions around it, omission included.
 *
 * What this block checks, and why these and not others. `seen` and `public` do not
 * owe the same things, so the guards are not the same guards: `public` is served by
 * the Data API and owes an emptiness, `seen` is not served and owes an allow-list,
 * because `seen.current_tenant()` has to be callable by `authenticated` or every
 * policy in the trade record returns nothing. Five questions are asked. Which
 * schemas the Data API serves, because that is the premise the other four rest on
 * and it lived in prose alone. Which routines here a browser-bound role can
 * execute, which is F38 and is the only one of the five that is behaviour rather
 * than an inventory. Whether the one allowed routine's access control list still
 * names the three roles part 1 grants it to and no longer names PUBLIC. Whether any
 * relation or sequence here is reachable, which is `seen.erased_tenants` and
 * `seen.marketplace_catalogue` today and whatever a later migration adds beside
 * them. And whether the schema has acquired a `pg_default_acl` entry or a CREATE
 * grant, which are the two ways a later object here would be born granted or be put
 * here by somebody other than a migration.
 *
 * What is deliberately left out, because a guard that checks everything is one
 * nobody maintains. There is no tenancy or row-level-security assertion over
 * `seen`: criterion 2 is a statement about `public`, and the two tables here belong
 * to no tenant and could not satisfy it, so the property they are held to is
 * unreachability instead, which is the stronger one for them. There is no free-text
 * or buyer-PII classification over `seen`: part 7 reads `public` by design, the
 * registry's columns are already asserted to be exactly the two a tombstone may
 * hold, and `seen.marketplace_catalogue` is a static catalogue of the six
 * marketplaces with no prose in it. Nothing here asks PostgREST over HTTP what it
 * is actually serving; the configuration file is what this repository states and
 * what a cloud project would be configured from, and a suite that opened an HTTP
 * connection to answer a question about a committed line would be paying a
 * dependency for no more certainty. And no attempt is made to assert what
 * `supabase_admin` has done in this schema, for the reason part 6 records for
 * `public`: that grantor's entries are outside what the migration role can read
 * meaningfully or revoke at all.
 */
describe('schema seen, which the Data API does not serve', () => {
  let client: Client;

  beforeAll(async () => {
    client = await connect();
  });

  afterAll(async () => {
    await client?.end();
  });

  it('is not served by the Data API, which is what every rule about where an object lives '
    + 'rests on', () => {
    // Text about text, and it is here rather than in a comment because the sentence
    // it guards is load-bearing four times over in this migration set and was
    // written down nowhere a test could reach. If `seen` joins this list, the
    // erasure registry becomes a table endpoint, every helper here becomes a
    // `POST /rpc/<name>`, and the allow-list below stops being an acceptable rule
    // without anything else in the suite noticing.
    const configured = readRepositoryFile(DATA_API_CONFIG);
    const match = DATA_API_SCHEMAS_SETTING.exec(configured);
    expect(match, `${DATA_API_CONFIG} has no \`schemas = [...]\` line, so what the Data API `
      + 'serves cannot be read from the file this repository configures it with').not.toBeNull();
    const served = (match?.[1] ?? '')
      .split(',')
      .map((entry) => entry.trim().replace(/^["']|["']$/g, ''))
      .filter((entry) => entry.length > 0)
      .sort();
    expect(
      served,
      `${DATA_API_CONFIG} serves ${served.join(', ')}. Schema ${HELPER_SCHEMA} being absent from `
      + 'that list is the reason the erasure registry is not a table endpoint, the reason part 6 '
      + 'can send a materialised view and a foreign table to a schema outside public, and the '
      + 'reason a callable routine here is a smaller thing than a callable routine there. A '
      + 'schema added to it is a decision to publish everything in it',
    ).toEqual([...DATA_API_SCHEMAS]);
  });

  it('lets a browser-bound role execute the tenancy helper and nothing else', async () => {
    // F38. The allow-list is composed rather than spelled, so that adding a role to
    // CLIENT_BOUND_ROLES widens this assertion instead of silently leaving the new
    // role unasked, and so that the expected strings carry the same shape the guard
    // produces: a routine that became `security definer` would report "running with
    // its owner rights" and stop matching, which is the condition that makes the one
    // exception an acceptable one.
    const callable = await executableRoutinesIn(client, HELPER_SCHEMA);
    const allowed = HELPER_SCHEMA_CALLABLE_ROUTINES
      .flatMap((signature) => CLIENT_BOUND_ROLES
        .map((role) => `${HELPER_SCHEMA}.${signature} is a function that ${role} can execute`));
    expect(
      callable,
      `${callable.length} routines in schema ${HELPER_SCHEMA} can be executed by a role a browser `
      + `request is bound to, where ${allowed.length} may be. This schema is not served by the `
      + 'Data API, so none of them is an endpoint, but `anon` holds USAGE here and can name and '
      + 'call any of them that carries EXECUTE to PUBLIC. Part 6 takes that grant away from every '
      + 'routine the migration role creates after it, so one reported here was created before '
      + 'part 6 ran, was created under another owner, or has been granted back. '
      + `The guard reported: ${callable.join('; ')}`,
    ).toEqual(allowed);
  });

  it('grants the tenancy helper to the three request-bound roles by name and to PUBLIC no '
    + 'longer', async () => {
    // The other half of what part 1 writes, and the half a grant statement hides. The
    // three grants beside the function read as the whole of its access control list
    // and are not: `create function` had already given EXECUTE to PUBLIC, the grants
    // sit beside that rather than replace it, and until part 1 revoked it the three
    // named grants bought nothing that was not already true of every role in the
    // database.
    //
    // Removing it is safe and that was established rather than assumed, because
    // getting it wrong returns nothing from every table in the schema. Measured on
    // this stack: thirty policies reference the helper and nothing else in the
    // database does, no column default, no check constraint, no view definition and
    // no other routine body; every one of those thirty policies is `to
    // authenticated`, which holds an explicit grant; of the ten roles that lose
    // EXECUTE with PUBLIC gone, eight hold no privilege on any of the twenty-nine
    // tables, so they are refused 42501 before a policy is evaluated at all, and the
    // remaining two carry BYPASSRLS, so no policy is applied to them and the helper
    // is never called on their behalf. Then behaviourally, in a rolled-back
    // transaction with the grant revoked: `authenticated` carrying a tenant claim
    // still read exactly its own tenant's row out of two.
    const { clientRolesNamed, publicIsNamed } = await routineAccessControlList(
      client, `${HELPER_SCHEMA}.current_tenant()`,
    );
    expect(
      { clientRolesNamed, publicIsNamed },
      'The access control list of the tenancy helper has to name the roles part 1 grants it to '
      + 'and must not name PUBLIC, because a grant to PUBLIC is the route past every guard that '
      + `matches a grantee by name. It reads ${clientRolesNamed.join(', ') || 'no client role'}`
      + `${publicIsNamed ? ' and PUBLIC' : ' and not PUBLIC'}`,
    ).toEqual({ clientRolesNamed: [...CLIENT_BOUND_ROLES], publicIsNamed: false });
  });

  it('holds no relation and no sequence a browser-bound role can reach', async () => {
    // seen.erased_tenants and seen.marketplace_catalogue, and whatever is put here
    // next. Asked over both relation families and over sequences in one breath,
    // because the question this schema owes is the same for all of them and is not
    // the question public owes: there is no view here that may publish itself by
    // granting its own select, and no table here that carries a tenancy policy. A
    // reachable relation in `seen` is a defect whatever its kind, and a tombstone a
    // request-bound role can delete is a tenant id that can be created again a
    // statement later.
    //
    // `service_role` is asked as well as the two browser-bound roles, which is the
    // one place this guard is stricter than its counterpart in public. There it is
    // granted per table by name and is how the API writes the trade record; here it
    // is the role the defect at F21 was measured with, and part 8's own self-check
    // already refuses it any privilege on the registry.
    const reachable = [
      ...(await effectivePrivilegesIn(
        client, HELPER_SCHEMA,
        [...Object.keys(TABLE_RELKINDS), ...Object.keys(NON_TABLE_RELKINDS)],
        DATA_API_ROLES,
      )).map((holding) => `${HELPER_SCHEMA}.${named(holding)} lets ${holding.role} `
        + holdingLabel(holding)),
      ...await sequencesReachableIn(client, HELPER_SCHEMA),
    ];
    expect(
      reachable,
      `${reachable.length} objects in schema ${HELPER_SCHEMA} can be reached by a role the Data `
      + 'API binds a request to. Nothing here belongs to a tenant, so nothing here can carry the '
      + 'tenancy that would make reaching it safe, and the boundary is the privilege alone: '
      + reachable.join('; '),
    ).toEqual([]);
  });

  it('files no default privilege and lets no request-bound role create anything here', async () => {
    // The two routes by which a later object in `seen` would arrive already reachable,
    // rather than be made reachable by a statement somebody wrote. Part 8 states the
    // first as a measured fact, that this schema carries no `pg_default_acl` entry at
    // all and so a table created here starts owner-only, and rests its revoke on it;
    // that is a claim about behaviour in a file that explains itself, which is exactly
    // what this ticket has learned to put an assertion beside.
    //
    // What this pair does not cover is said as carefully as what it does, because
    // reading it as the whole of the prevention is how F38 happened. It is an
    // assertion about what is filed against this schema, and the statement that
    // keeps a routine here out of reach is filed against no schema at all: part 6's
    // revoke of EXECUTE to PUBLIC writes a `pg_default_acl` row whose
    // `defaclnamespace` is 0, which this pair reads as nothing and would go on
    // passing over if somebody dropped it. The test below is what measures that one,
    // the allow-list above is what sees a routine carrying the grant anyway, and the
    // revokes each migration writes beside its own functions are what close a
    // routine created before part 6 ran.
    const measured = {
      defaultPrivilegesFiledHere: await defaultPrivilegesForClientRolesIn(client, HELPER_SCHEMA),
      rolesThatCanCreateHere: (await client.query<{ role: string }>(
        `select r.rolname as role
           from pg_catalog.pg_roles r
          where (r.rolname = any($1) or r.rolname = 'service_role')
            and has_schema_privilege(r.oid, $2, 'CREATE')
          order by r.rolname`,
        [[...CLIENT_BOUND_ROLES], HELPER_SCHEMA],
      )).rows.map((row) => row.role),
      rolesThatCanEnterHere: (await client.query<{ role: string }>(
        `select r.rolname as role
           from pg_catalog.pg_roles r
          where (r.rolname = any($1) or r.rolname = 'service_role')
            and has_schema_privilege(r.oid, $2, 'USAGE')
          order by r.rolname`,
        [[...CLIENT_BOUND_ROLES], HELPER_SCHEMA],
      )).rows.map((row) => row.role),
    };
    expect(
      measured,
      `Schema ${HELPER_SCHEMA} may file no default privilege, because an object created here has `
      + 'to start owner-only for part 8\'s revoke on the erasure registry to mean what it says; '
      + 'and no role a request is bound to may hold CREATE here, because a role that can put a '
      + 'function in this schema can put one there that the allow-list was written to stop. USAGE '
      + 'is the one thing all three do hold, deliberately and not as an oversight: the tenancy '
      + 'helper is evaluated as the caller inside every policy, so a request that could not enter '
      + `this schema would read every table in the trade record as empty. Measured: ${JSON.stringify(measured)}`,
    ).toEqual({
      defaultPrivilegesFiledHere: [],
      rolesThatCanCreateHere: [],
      rolesThatCanEnterHere: [...CLIENT_BOUND_ROLES, 'service_role'].sort(),
    });
  });

  it('is where a helper created now is born out of reach, and nothing here says it cannot be',
    async () => {
      // The claim part 6 and part 8 both make about this schema, measured, and the
      // four sentences that went on denying it, read.
      //
      // Both halves are one test because either alone is the defect. The
      // measurement alone is what the ninth review (F43) had to make by hand before
      // it could see the contradiction, and it would go on passing beside prose
      // telling the author of SEEN-014 or SEEN-021 that a helper they add here is
      // callable by `anon` until they revoke it, which is the reasoning F39 was
      // raised to end. The reading alone would hold this set to a sentence and not
      // to a database, and would pass unchanged on a stack where somebody had
      // dropped part 6's statement and made the withdrawn claim true again.
      //
      // The probe returns `int` and is not `security definer`, which is the whole
      // difference between this and the test below it: that one asks what a routine
      // carrying EXECUTE to PUBLIC can hand back, and this one asks whether a
      // routine is born carrying it at all. Nothing is granted on it and nothing is
      // revoked from it, because what is measured is the state it arrives in.
      // Measured on PostgreSQL 17.6 on this stack: `{postgres=X/postgres}`, with
      // `has_function_privilege` false for `anon`, `authenticated` and
      // `service_role` alike, which is schema `seen` carrying no `pg_default_acl`
      // entry of its own and so leaving part 6's global entry as the whole of what
      // applies. The access control list is asked for as well as the three roles,
      // because a null one is the state in which every role there is can execute
      // and would answer this question the wrong way round.
      //
      // The owner is read from the catalogue rather than named, so that a stack
      // reached through SEEN_DATABASE_URL under another role is held to the property
      // and not to the word `postgres`.
      await client.query('begin');
      try {
        const probe = `${HELPER_SCHEMA}.seen_born_out_of_reach_probe()`;
        await client.query(
          `create function ${probe} returns int language sql as $$ select 1 $$`,
        );
        const granted = (await client.query<{ grantee: string; owner: string }>(
          `select case when a.grantee = 0 then 'PUBLIC' else a.grantee::regrole::text end
                    as grantee,
                  p.proowner::regrole::text as owner
             from pg_catalog.pg_proc p
             cross join lateral aclexplode(p.proacl) a
            where p.oid = $1::regprocedure
            order by grantee`,
          [probe],
        )).rows;
        const rolesThatCanExecuteIt: string[] = [];
        for (const role of DATA_API_ROLES) {
          if (await canExecute(client, role, probe)) rolesThatCanExecuteIt.push(role);
        }
        const bornWith = {
          accessControlListIsNull: granted.length === 0,
          grantedToAnybodyButItsOwner: granted
            .filter((row) => row.grantee !== row.owner)
            .map((row) => row.grantee),
          rolesThatCanExecuteIt,
        };
        const stillStanding = withdrawnClaimsStillStanding(sourcesThatDocumentTheSet());
        expect(
          { bornWith, stillStanding },
          'A function was created in schema seen, granted nothing and revoked nothing, and the '
          + `database answered ${JSON.stringify(bornWith)}. It has to arrive holding nothing for `
          + 'anybody but its owner, because that is what part 6 and part 8 tell a later author '
          + 'this schema does for them, and an access control list of its own has to exist at '
          + 'all, because a null one is the state in which every role can execute. And no file '
          + 'that documents this set may go on denying it: five rounds of this ticket wrote that '
          + 'denial down, F39 withdrew it, and F43 found four places it had been left. What is '
          + `still standing: ${stillStanding.join('; ') || 'nothing'}`,
        ).toEqual({
          bornWith: {
            accessControlListIsNull: false,
            grantedToAnybodyButItsOwner: [],
            rolesThatCanExecuteIt: [],
          },
          stillStanding: [],
        });
      } finally {
        await client.query('rollback');
      }
    });

  it('reads a withdrawn claim wherever a person would meet one, quoted or commented', () => {
    // The scanner shown prose the repository does not hold, because a guard that
    // passes by finding nothing is the shape every silent boundary in this ticket
    // had. Three sources, one per way the four sentences of F43 were written: a SQL
    // comment, the message a `raise exception` hands a person, and the message an
    // assertion prints when it fails. The second and third are the ones a scanner
    // over comments alone would walk past, and the third is written wrapped, so it
    // also shows that a sentence broken across two string literals is read as the
    // sentence it is and not as two halves of one.
    const [inAComment, inARaise, wrapped] = WITHDRAWN_BIRTH_CLAIMS;
    const reported = withdrawnClaimsStillStanding([
      {
        file: 'a.sql',
        contents: '-- A function added here is callable by name, and there is\n'
          + `-- ${inAComment.spelling.join(' ')}, so this raises instead.\n`,
      },
      {
        file: 'b.sql',
        contents: '  raise exception \'a routine here is callable by name \'\n'
          + `    '${inARaise.spelling.join(' ')} from public: %', offenders;\n`,
      },
      {
        file: 'c.ts',
        contents: `      + 'call any of them: a routine stays callable, ${wrapped.spelling[0]} '\n`
          + `      + '${wrapped.spelling.slice(1).join(' ')}. '\n`,
      },
    ]);
    const where = reported.map((entry) => entry.slice(0, entry.indexOf(' still says ')));
    expect(
      where,
      'The scanner was shown one withdrawn claim in each of the three shapes F43 found one in, '
      + 'and has to report all three at the line the sentence starts on. A scanner over comments '
      + 'alone walks past a raise message and an assertion message, which are the two places a '
      + 'person is told something the database contradicts; a scanner that did not join a '
      + 'wrapped string walks past the third, which is how all four of them are written. It '
      + `reported: ${reported.join('; ') || 'nothing'}`,
    ).toEqual(['a.sql:2', 'b.sql:2', 'c.ts:1']);
  });

  it('would see a helper a later migration added here, born callable by anon', async () => {
    // What the allow-list is worth nothing without, and the hazard F38 names stated
    // as a measurement rather than as a prediction. The probe returns text rather
    // than `trigger`, which is the whole of the difference between the two functions
    // F38 found and the one the next author writes: those answered 0A000 because of
    // what they returned, and this one answers with the row. Two tenants are inserted
    // so that the count shows a tenant boundary was crossed and not merely that a
    // call was accepted.
    //
    // The second half is the fix, measured on the same object: `revoke all on
    // function ... from public` is one statement and is the whole of the prevention
    // here, where in schema public the same statement leaves `anon=X` standing
    // because the default access control list there names the role outright. That
    // asymmetry is why part 8's revokes are written the way they are and why they
    // are not the rule for writing a function in `public`.
    //
    // The grant to PUBLIC is written here rather than waited for, and what it means
    // changed with F39. It is the grant PostgreSQL used to make by itself on every
    // routine, so until part 6 gained its global revoke this fixture got its hazard
    // from the database and a later author installing prevention would have been
    // told by this test that they had broken something. The grant now says in one
    // line what the hazard is: a routine in this schema that carries EXECUTE to
    // PUBLIC, however it came by it, is callable by `anon`, because `anon` holds
    // USAGE here. Part 6 stops it arriving by default and part 8's revokes stop it
    // arriving from a routine created before part 6 runs; neither stops somebody
    // writing it, which is what this measures.
    await client.query('begin');
    try {
      await client.query(
        "insert into public.tenants (name) values ('Tenant A'), ('Tenant B')",
      );
      await client.query(
        `create function ${HELPER_SCHEMA}.seen_helper_probe() returns setof text `
        + 'language sql security definer as $$ select name from public.tenants $$',
      );
      await client.query(
        `grant execute on function ${HELPER_SCHEMA}.seen_helper_probe() to public`,
      );
      const bornWith = {
        routinesTheGuardReports: (await executableRoutinesIn(client, HELPER_SCHEMA))
          .filter((entry) => entry.includes('seen_helper_probe')),
        anonCallingIt: await answeredAs(
          client, 'anon', `select * from ${HELPER_SCHEMA}.seen_helper_probe()`,
        ),
      };
      await client.query(
        `revoke all on function ${HELPER_SCHEMA}.seen_helper_probe() from public`,
      );
      const afterTheRevoke = {
        routinesTheGuardReports: (await executableRoutinesIn(client, HELPER_SCHEMA))
          .filter((entry) => entry.includes('seen_helper_probe')),
        anonCallingIt: await answeredAs(
          client, 'anon', `select * from ${HELPER_SCHEMA}.seen_helper_probe()`,
        ),
      };
      expect(
        { bornWith, afterTheRevoke },
        'A `security definer` helper created in schema seen, which nobody granted anything on, '
        + 'is callable by `anon` and hands back every tenant\'s rows, because a routine is born '
        + 'with EXECUTE to PUBLIC and `anon` holds USAGE on this schema. That is the hazard the '
        + 'allow-list above exists to catch and the revoke in each migration exists to close, and '
        + `both halves are measured here: ${JSON.stringify({ bornWith, afterTheRevoke })}`,
      ).toEqual({
        bornWith: {
          routinesTheGuardReports: CLIENT_BOUND_ROLES.map((role) => `${HELPER_SCHEMA}`
            + `.seen_helper_probe() is a function running with its owner rights that ${role} `
            + 'can execute'),
          anonCallingIt: { answer: 'accepted', rows: 2 },
        },
        afterTheRevoke: {
          routinesTheGuardReports: [],
          anonCallingIt: { answer: '42501', rows: null },
        },
      });
    } finally {
      await client.query('rollback');
    }
  });
});
