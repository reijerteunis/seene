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

  it('is processed by the worker and returns what it greeted', async () => {
    const job = await queue.add('hello', { name: 'Seen' });

    const result = await job.waitUntilFinished(worker.createQueueEventsInstance());

    expect(result).toEqual({ greeted: 'Seen' });
  });
});
