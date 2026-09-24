import { createHash } from 'node:crypto';

import { createClient } from '@supabase/supabase-js';

import {
  type Environment,
  notUntilGoLive,
  required,
  selectImplementation,
} from './selection';

/**
 * Raw payloads and evidence. Evidence is hashed on write, so a claim can name the
 * bytes it was built from and a reviewer can check they have not moved.
 */
export interface StorageProvider {
  readonly name: StorageProviderName;
  /** Writes the bytes and returns the path and their sha256. */
  put(path: string, body: Uint8Array, contentType?: string): Promise<StoredObject>;
  get(path: string): Promise<Uint8Array>;
  /** A time-limited URL, for a case pack a person opens rather than a job reads. */
  signedUrl(path: string, expiresInSeconds: number): Promise<string>;
}

export interface StoredObject {
  path: string;
  sha256: string;
  bytes: number;
}

export const STORAGE_PROVIDERS = ['supabase', 'gcs'] as const;
export type StorageProviderName = (typeof STORAGE_PROVIDERS)[number];

export function sha256(body: Uint8Array): string {
  return createHash('sha256').update(body).digest('hex');
}

/**
 * Local Supabase Storage now, the EU Supabase project after go-live. The same
 * implementation serves both: only SUPABASE_URL changes.
 */
export function supabaseStorageProvider(env: Environment): StorageProvider {
  const url = required(env, 'SUPABASE_URL');
  const key = required(env, 'SUPABASE_SERVICE_ROLE_KEY');
  const bucket = env.SEEN_STORAGE_BUCKET ?? 'evidence';
  const client = createClient(url, key, { auth: { persistSession: false } });

  return {
    name: 'supabase',

    async put(path, body, contentType = 'application/octet-stream') {
      const { error } = await client.storage
        .from(bucket)
        .upload(path, body, { contentType, upsert: true });
      if (error) throw new Error(`Storage put '${path}' failed: ${error.message}`);

      return { path, sha256: sha256(body), bytes: body.byteLength };
    },

    async get(path) {
      const { data, error } = await client.storage.from(bucket).download(path);
      if (error || !data) throw new Error(`Storage get '${path}' failed: ${error?.message}`);

      return new Uint8Array(await data.arrayBuffer());
    },

    async signedUrl(path, expiresInSeconds) {
      const { data, error } = await client.storage
        .from(bucket)
        .createSignedUrl(path, expiresInSeconds);
      if (error || !data) throw new Error(`Storage sign '${path}' failed: ${error?.message}`);

      return data.signedUrl;
    },
  };
}

export function createStorageProvider(env: Environment = process.env): StorageProvider {
  const name = selectImplementation(env, 'SEEN_STORAGE_PROVIDER', STORAGE_PROVIDERS, 'supabase');

  switch (name) {
    case 'supabase':
      return supabaseStorageProvider(env);
    case 'gcs':
      return notUntilGoLive('SEEN_STORAGE_PROVIDER', name);
  }
}
