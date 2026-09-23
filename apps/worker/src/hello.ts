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

export function startHelloWorker(): Worker<HelloPayload, HelloResult> & {
  createQueueEventsInstance: () => QueueEvents;
} {
  const worker = new Worker<HelloPayload, HelloResult>(
    HELLO_QUEUE,
    async (job) => ({ greeted: job.data.name }),
    { connection },
  ) as Worker<HelloPayload, HelloResult> & { createQueueEventsInstance: () => QueueEvents };

  // waitUntilFinished needs its own events connection; keeping it beside the
  // worker means a caller cannot forget to close one of the two.
  const events = new QueueEvents(HELLO_QUEUE, { connection });
  worker.createQueueEventsInstance = () => events;
  const close = worker.close.bind(worker);
  worker.close = async (force?: boolean) => {
    await events.close();
    return close(force);
  };

  return worker;
}
