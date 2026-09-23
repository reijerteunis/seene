import { describe, expect, it } from 'vitest';

import { site } from './site';

describe('the site', () => {
  it('names the product rather than the repository', () => {
    expect(site.name).toBe('Seen');
  });

  it('carries a description the layout can put in a meta tag', () => {
    expect(site.description).toContain('marketplace');
  });
});
