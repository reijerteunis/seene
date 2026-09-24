import './bootstrap';

import { startHelloWorker } from './hello';

/**
 * The worker process. Every queue it serves is started here, so what runs in
 * production is one list in one file rather than a discovery mechanism.
 */
const worker = startHelloWorker();

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    void worker.close().then(() => process.exit(0));
  });
}
