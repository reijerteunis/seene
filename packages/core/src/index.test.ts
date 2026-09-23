import { describe, expect, it } from 'vitest';

import { LEDGER_CURRENCY, packageName, sumCents } from './index';

describe('@seen/core', () => {
  it('resolves, compiles and runs under vitest', () => {
    expect(packageName).toBe('@seen/core');
  });
});

describe('cents', () => {
  it('sums integer amounts without floating point drift', () => {
    expect(sumCents([1999, 1, 250])).toBe(2250);
  });

  it('denominates the ledger in EUR', () => {
    expect(LEDGER_CURRENCY).toBe('EUR');
  });
});
