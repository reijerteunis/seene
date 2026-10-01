/**
 * SEEN-097 F2: the local Supabase service-role JWT as a literal fallback, which
 * gitleaks did not catch because the key is the CLI's published demo one.
 */
const serviceRole =
  process.env.SUPABASE_SERVICE_ROLE_KEY ?? 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';

export const key = serviceRole;
