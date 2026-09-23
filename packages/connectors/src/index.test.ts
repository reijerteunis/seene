import { describe, expect, it } from 'vitest';

import { packageName } from './index';

describe('@seen/connectors', () => {
  it('resolves, compiles and runs under vitest', () => {
    expect(packageName).toBe('@seen/connectors');
  });
});
