import { QueueEvents, Worker } from 'bullmq';
import type { ConnectionOptions } from 'bullmq';

/**
 * The first job, and the shape every later one follows: a named queue, a typed
 * payload, and a worker that returns what it did so the caller can prove it ran.
 *
 * Redis is read from the environment, so the same test runs against the local
 * server on a developer's machine and against the service container in CI.
 */
export const HELLO_QUEUE = 'hello';

export const connection: ConnectionOptions = {
  host: process.env.REDIS_HOST ?? '127.0.0.1',
  port: Number(process.env.REDIS_PORT ?? 6379),
};

export interface HelloPayload {
  name: string;
}

export interface HelloResult {
  greeted: string;
}

export interface HelloWorker extends Worker<HelloPayload, HelloResult> {
  /** The events connection waitUntilFinished needs, owned so it cannot be forgotten. */
  events: QueueEvents;
  /**
   * Resolves once the worker and its events connection are both subscribed.
   *
   * Without this a job can finish before the events connection subscribes, and
   * waitUntilFinished then waits for an event that has already gone past. It
   * passed on a laptop and timed out in CI on the same commit, which is what a
   * race looks like from the outside.
   */
  ready: () => Promise<void>;
}

export function startHelloWorker(): HelloWorker {
  const worker = new Worker<HelloPayload, HelloResult>(
    HELLO_QUEUE,
    async (job) => ({ greeted: job.data.name }),
    { connection },
  ) as HelloWorker;

  worker.events = new QueueEvents(HELLO_QUEUE, { connection });
  worker.ready = async () => {
    await Promise.all([worker.waitUntilReady(), worker.events.waitUntilReady()]);
  };

  const close = worker.close.bind(worker);
  worker.close = async (force?: boolean) => {
    await worker.events.close();
    return close(force);
  };

  return worker;
}
