import { defineConfig } from 'vitest/config';

export default defineConfig({
  // The worker test talks to a real Redis, so it is slower than a unit test and
  // is given room rather than a flaky default.
  test: { environment: 'node', testTimeout: 20000, hookTimeout: 20000 },
  resolve: {
    alias: { '@seen/core': new URL('../../packages/core/src/index.ts', import.meta.url).pathname },
  },
});
