import { readFileSync } from 'node:fs';

/** A fee schedule read from disk is a fee schedule nobody ingested. */
export function schedule(path: string): string {
  return readFileSync(path, 'utf8');
}
