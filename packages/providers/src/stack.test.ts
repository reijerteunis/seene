import { describe, expect, it } from 'vitest';

import { createStorageProvider, sha256 } from './storage';
import { otlpTelemetryProvider } from './telemetry';

/**
 * The two providers that talk to something, against the containers `pnpm dev:up`
 * starts. Nothing here is mocked: a storage provider that has never written to
 * Supabase and a telemetry provider that has never been accepted by a collector
 * are both untested, however many unit tests surround them.
 *
 * The same containers run in CI, from the same docker-compose.yml and
 * supabase/config.toml, so a green here is a green there.
 */

// vitest.setup.ts fills these from the running stack, so no key is committed here
// and a fresh clone with the stack up needs no .env.local to run the suite.
const supabaseEnv = () => ({
  SEEN_STORAGE_PROVIDER: 'supabase',
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
  SEEN_STORAGE_BUCKET: 'evidence',
});

describe('local Supabase Storage', () => {
  const path = `test/${process.pid}-${Date.now()}.txt`;
  const body = new TextEncoder().encode('A settlement line, as bytes.');

  it('writes bytes, hands back their sha256 and reads the same bytes out', async () => {
    const storage = createStorageProvider(supabaseEnv());

    const stored = await storage.put(path, body, 'text/plain');

    expect(stored).toEqual({ path, sha256: sha256(body), bytes: body.byteLength });
    expect(await storage.get(path)).toEqual(body);
  });

  it('signs a URL that serves the object without a service role key', async () => {
    const storage = createStorageProvider(supabaseEnv());
    await storage.put(path, body, 'text/plain');

    const url = await storage.signedUrl(path, 60);
    const response = await fetch(url);

    expect(response.status).toBe(200);
    expect(new Uint8Array(await response.arrayBuffer())).toEqual(body);
  });

  it('says which path it could not read rather than returning nothing', async () => {
    const storage = createStorageProvider(supabaseEnv());

    await expect(storage.get('test/not-a-real-object.txt')).rejects.toThrow(
      /test\/not-a-real-object\.txt/,
    );
  });
});

describe('the OpenTelemetry collector', () => {
  const endpoint = process.env.SEEN_OTLP_ENDPOINT ?? 'http://127.0.0.1:4318';
  const metricsUrl = process.env.SEEN_OTLP_METRICS_URL ?? 'http://127.0.0.1:8888/metrics';

  /** The collector's own count of spans it accepted, which is the only account that matters. */
  const acceptedSpans = async (): Promise<number> => {
    const text = await (await fetch(metricsUrl)).text();
    const total = [...text.matchAll(/^otelcol_receiver_accepted_spans(?:_total)?\{[^}]*}\s+(\d+)/gm)]
      .reduce((sum, match) => sum + Number(match[1]), 0);

    return total;
  };

  it('accepts a span and a per-tenant cost line sent as OTLP over HTTP', async () => {
    const before = await acceptedSpans();
    const telemetry = otlpTelemetryProvider({
      SEEN_OTLP_ENDPOINT: endpoint,
      SEEN_SERVICE_NAME: 'seen-providers-test',
    });

    const result = await telemetry.span('reconcile.match', { 'seen.tenant_id': 'demo-tenant' }, async () => 42);
    telemetry.cost({
      tenantId: 'demo-tenant',
      operation: 'agent.draft_claim',
      model: 'claude-opus-5',
      inputTokens: 1200,
      outputTokens: 340,
      cents: 7,
    });
    await telemetry.flush();

    expect(result).toBe(42);

    // The batch processor holds a span for up to a second before the pipeline sees it.
    const deadline = Date.now() + 10_000;
    let after = before;
    while (after < before + 2 && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      after = await acceptedSpans();
    }

    expect(after).toBeGreaterThanOrEqual(before + 2);
  });

  it('records a failing span as an error rather than losing it', async () => {
    const before = await acceptedSpans();
    const telemetry = otlpTelemetryProvider({ SEEN_OTLP_ENDPOINT: endpoint });

    await expect(
      telemetry.span('ingest.bol', {}, async () => {
        throw new Error('the marketplace said no');
      }),
    ).rejects.toThrow('the marketplace said no');
    await telemetry.flush();

    const deadline = Date.now() + 10_000;
    let after = before;
    while (after < before + 1 && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      after = await acceptedSpans();
    }

    expect(after).toBeGreaterThanOrEqual(before + 1);
  });

  it('says where it could not export to', async () => {
    const telemetry = otlpTelemetryProvider({ SEEN_OTLP_ENDPOINT: 'http://127.0.0.1:4319' });
    await telemetry.span('nowhere', {}, async () => null);

    await expect(telemetry.flush()).rejects.toThrow();
  });
});
