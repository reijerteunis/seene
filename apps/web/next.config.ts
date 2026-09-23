import type { NextConfig } from 'next';

const config: NextConfig = {
  // The workspace packages ship TypeScript sources with no build step, so Next
  // compiles them itself. That is what keeps a trade-record change to one commit.
  transpilePackages: ['@seen/core', '@seen/connectors', '@seen/agent'],
};

export default config;
