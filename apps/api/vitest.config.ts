import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: { environment: 'node' },
  resolve: {
    alias: { '@seen/core': new URL('../../packages/core/src/index.ts', import.meta.url).pathname },
  },
});
