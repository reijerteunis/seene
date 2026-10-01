// The violation harness/no-live-marketplace-host refuses: a connector test that
// would reach a real marketplace. SEEN-114. A test pointed at a live API is a
// test that fails when Bol is slow, charges the rate limit this repository shares
// with its pilots, and reads a seller account nobody meant to touch from CI.
//
// The rule is `harness lint`, which walks every tracked file in any language
// rather than only TypeScript, which is why it is the harness's own check and not
// an ast-grep rule: the same host in a Python fixture or a shell script is the
// same defect.
import { describe, expect, it } from 'vitest';

describe('orders', () => {
  it('reads the open orders page', async () => {
    const response = await fetch('https://api.bol.com/retailer/orders?status=OPEN');
    expect(response.status).toBe(200);
  });
});
