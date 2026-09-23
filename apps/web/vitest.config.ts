import { defineConfig } from 'vitest/config';

export default defineConfig({
  // A pure module, not a rendered component: App Router rendering tests need a
  // DOM and a React testing setup, and they arrive with the first real screen.
  test: { environment: 'node' },
});
