import { describe, expect, it } from 'vitest';

import { packageName } from './index';

describe('@seen/agent', () => {
  it('resolves, compiles and runs under vitest', () => {
    expect(packageName).toBe('@seen/agent');
  });
});
