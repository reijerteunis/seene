import { randomBytes } from 'node:crypto';

import {
  type Environment,
  notUntilGoLive,
  selectImplementation,
} from './selection';

/**
 * Traces and per-tenant cost. Cost is first class rather than a log line because
 * the agent's spend per tenant is a number the business reads, and a number that
 * only exists in a log is a number nobody reads.
 */
export interface TelemetryProvider {
  readonly name: TelemetryProviderName;
  /** Runs the function inside a span, recording how long it took and how it ended. */
  span<T>(name: string, attributes: Attributes, run: () => Promise<T>): Promise<T>;
  /** One agent run's spend, attributed to the tenant that caused it. */
  cost(entry: CostEntry): void;
  /** Sends anything still buffered. A process that exits without this loses it. */
  flush(): Promise<void>;
}

export type AttributeValue = string | number | boolean;
export type Attributes = Readonly<Record<string, AttributeValue | undefined>>;

export interface CostEntry {
  tenantId: string;
  /** What spent it: an agent run, a connector call, a report. */
  operation: string;
  model?: string;
  inputTokens?: number;
  outputTokens?: number;
  /** Integer cents, like every other amount in the trade record. */
  cents: number;
}

export const TELEMETRY_PROVIDERS = ['console', 'otlp', 'cloud-logging'] as const;
export type TelemetryProviderName = (typeof TELEMETRY_PROVIDERS)[number];

export interface Span {
  traceId: string;
  spanId: string;
  name: string;
  startUnixNano: bigint;
  endUnixNano: bigint;
  attributes: Attributes;
  /** OTLP status codes: 1 is Ok, 2 is Error. */
  status: 1 | 2;
}

const serviceName = (env: Environment): string => env.SEEN_SERVICE_NAME ?? 'seen';

function nowUnixNano(): bigint {
  return BigInt(Date.now()) * 1_000_000n;
}

function costAttributes(entry: CostEntry): Attributes {
  return {
    'seen.tenant_id': entry.tenantId,
    'seen.operation': entry.operation,
    'seen.model': entry.model,
    'seen.input_tokens': entry.inputTokens,
    'seen.output_tokens': entry.outputTokens,
    'seen.cost_cents': entry.cents,
    'seen.currency': 'EUR',
  };
}

/**
 * Records a span around the function whatever happens to it, so a failure is a
 * span with an error status rather than a gap in the trace.
 */
async function timed<T>(
  name: string,
  attributes: Attributes,
  run: () => Promise<T>,
  emit: (span: Span) => void,
): Promise<T> {
  const start = nowUnixNano();
  const span = {
    traceId: randomBytes(16).toString('hex'),
    spanId: randomBytes(8).toString('hex'),
    name,
    startUnixNano: start,
    attributes,
  };

  try {
    const result = await run();
    emit({ ...span, endUnixNano: nowUnixNano(), status: 1 });
    return result;
  } catch (error) {
    emit({
      ...span,
      endUnixNano: nowUnixNano(),
      attributes: { ...attributes, 'seen.error': String(error) },
      status: 2,
    });
    throw error;
  }
}

/** Development's default: everything on stdout, nothing to run alongside. */
export function consoleTelemetryProvider(
  env: Environment,
  write: (line: string) => void = (line) => console.log(line),
): TelemetryProvider {
  const service = serviceName(env);

  return {
    name: 'console',

    span: (name, attributes, run) =>
      timed(name, attributes, run, (span) => {
        const ms = Number(span.endUnixNano - span.startUnixNano) / 1_000_000;
        write(
          `[${service}] span ${span.name} ${ms.toFixed(1)}ms ` +
            `${span.status === 1 ? 'ok' : 'error'} ${JSON.stringify(span.attributes)}`,
        );
      }),

    cost(entry) {
      write(`[${service}] cost ${JSON.stringify(costAttributes(entry))}`);
    },

    async flush() {},
  };
}

/** OTLP over HTTP with a JSON body: the shape the collector in docker compose reads. */
export function otlpTelemetryProvider(env: Environment): TelemetryProvider {
  const service = serviceName(env);
  const endpoint = (env.SEEN_OTLP_ENDPOINT ?? 'http://127.0.0.1:4318').replace(/\/$/, '');
  const pending: Span[] = [];

  const send = async (spans: readonly Span[]): Promise<void> => {
    if (spans.length === 0) return;

    const response = await fetch(`${endpoint}/v1/traces`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(otlpTracesPayload(service, spans)),
    });
    if (!response.ok) {
      throw new Error(`OTLP export to ${endpoint} failed: ${response.status}`);
    }
  };

  const record = (span: Span): void => {
    pending.push(span);
  };

  return {
    name: 'otlp',
    span: (name, attributes, run) => timed(name, attributes, run, record),

    cost(entry) {
      const at = nowUnixNano();
      record({
        traceId: randomBytes(16).toString('hex'),
        spanId: randomBytes(8).toString('hex'),
        name: 'seen.cost',
        startUnixNano: at,
        endUnixNano: at,
        attributes: costAttributes(entry),
        status: 1,
      });
    },

    async flush() {
      const batch = pending.splice(0, pending.length);
      await send(batch);
    },
  };
}

/** The OTLP/HTTP JSON encoding, written out rather than pulled in. */
export function otlpTracesPayload(service: string, spans: readonly Span[]): unknown {
  return {
    resourceSpans: [
      {
        resource: { attributes: otlpAttributes({ 'service.name': service }) },
        scopeSpans: [
          {
            scope: { name: '@seen/providers' },
            spans: spans.map((span) => ({
              traceId: span.traceId,
              spanId: span.spanId,
              name: span.name,
              kind: 1,
              startTimeUnixNano: span.startUnixNano.toString(),
              endTimeUnixNano: span.endUnixNano.toString(),
              attributes: otlpAttributes(span.attributes),
              status: { code: span.status },
            })),
          },
        ],
      },
    ],
  };
}

export function otlpAttributes(attributes: Attributes): unknown[] {
  return Object.entries(attributes)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => ({ key, value: otlpValue(value as AttributeValue) }));
}

function otlpValue(value: AttributeValue): unknown {
  if (typeof value === 'boolean') return { boolValue: value };
  if (typeof value === 'number') {
    // int64 travels as a string in OTLP/JSON; a non-integer is a double.
    return Number.isInteger(value) ? { intValue: String(value) } : { doubleValue: value };
  }
  return { stringValue: value };
}

export function createTelemetryProvider(env: Environment = process.env): TelemetryProvider {
  const name = selectImplementation(
    env,
    'SEEN_TELEMETRY_PROVIDER',
    TELEMETRY_PROVIDERS,
    'console',
  );

  switch (name) {
    case 'console':
      return consoleTelemetryProvider(env);
    case 'otlp':
      return otlpTelemetryProvider(env);
    case 'cloud-logging':
      return notUntilGoLive('SEEN_TELEMETRY_PROVIDER', name);
  }
}
