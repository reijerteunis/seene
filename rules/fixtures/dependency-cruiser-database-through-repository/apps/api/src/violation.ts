import { Client } from 'pg';

/** A query outside the repository layer is a query no tenancy guard covers. */
export async function findings(tenantId: string): Promise<unknown> {
  const client = new Client();
  await client.connect();
  return client.query('select * from findings where tenant_id = $1', [tenantId]);
}
