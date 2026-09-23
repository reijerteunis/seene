import { Queue } from 'bullmq';
import { afterAll, describe, expect, it } from 'vitest';

import { connection, HELLO_QUEUE, startHelloWorker } from './hello';

describe('the hello job', () => {
  const queue = new Queue(HELLO_QUEUE, { connection });
  const worker = startHelloWorker();

  afterAll(async () => {
    await worker.close();
    await queue.obliterate({ force: true });
    await queue.close();
  });

  it('is ready before anything is enqueued, so no completion can be missed', async () => {
    await worker.ready();

    expect(worker.isRunning()).toBe(true);
  });

  it('is processed by the worker and returns what it greeted', async () => {
    await worker.ready();

    const job = await queue.add('hello', { name: 'Seen' });
    const result = await job.waitUntilFinished(worker.events);

    expect(result).toEqual({ greeted: 'Seen' });
  });
});
