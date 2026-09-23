import { describe, expect, it } from 'vitest';

import { packageName } from './index';

describe('@seen/core', () => {
  it('resolves, compiles and runs under vitest', () => {
    expect(packageName).toBe('@seen/core');
  });
});
