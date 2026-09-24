import { execFileSync } from 'node:child_process';

/**
 * The Supabase keys are generated per machine, so they are asked of the running
 * stack rather than committed anywhere or kept in a .env.local a fresh clone does
 * not have. CI does the same thing through `supabase status -o env`, which is why
 * `pnpm test` behaves the same in both places.
 */
export default function setup(): void {
  if (process.env.SUPABASE_SERVICE_ROLE_KEY && process.env.SUPABASE_URL) return;

  let output: string;
  try {
    output = execFileSync('supabase', ['status', '-o', 'env'], { encoding: 'utf8' });
  } catch {
    throw new Error(
      'The local stack is not running, so there are no Supabase keys to read. ' +
        'Run `pnpm dev:up` first, or set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.',
    );
  }

  const read = (name: string): string | undefined =>
    new RegExp(`^${name}="?([^"\\n]+)"?$`, 'm').exec(output)?.[1];

  process.env.SUPABASE_URL ??= read('API_URL');
  process.env.SUPABASE_SERVICE_ROLE_KEY ??= read('SERVICE_ROLE_KEY');
}
