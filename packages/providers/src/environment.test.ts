import { existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';

import { loadLocalEnvironment, repositoryRoot } from './environment.ts';
import { createSecretsProvider } from './secrets.ts';

/**
 * .env.local is where every variable lives on a laptop: the README says to copy
 * .env.example to it, and the secrets provider's own error tells you to put a
 * credential there. Something has to read it, or all of that is decoration.
 */
describe('loading .env.local', () => {
  const added: string[] = [];

  const write = (contents: string): string => {
    const directory = mkdtempSync(join(tmpdir(), 'seen-env-'));
    writeFileSync(join(directory, '.env.local'), contents);
    return directory;
  };

  const set = (name: string, value: string): void => {
    added.push(name);
    process.env[name] = value;
  };

  /**
   * The global setup loads the developer's own .env.local, and this suite's whole
   * subject is that a value already in the environment wins. Without clearing the
   * name first, every assertion here depends on what happens to be in that file,
   * which is a test that passes on most machines and fails on one.
   */
  const clear = (name: string): void => {
    added.push(name);
    delete process.env[name];
  };

  afterEach(() => {
    for (const name of added.splice(0, added.length)) delete process.env[name];
  });

  it('puts what the file holds into the environment', () => {
    clear('SEEN_SECRET_BOL_NL_CLIENT_SECRET');
    clear('REDIS_PORT');
    const directory = write('SEEN_SECRET_BOL_NL_CLIENT_SECRET=from-the-file\nREDIS_PORT=6380\n');

    const loaded = loadLocalEnvironment(directory);

    expect(loaded).toBe(join(directory, '.env.local'));
    expect(process.env.SEEN_SECRET_BOL_NL_CLIENT_SECRET).toBe('from-the-file');
    expect(process.env.REDIS_PORT).toBe('6380');
  });

  it('leaves a variable the environment already set alone, so a real deployment wins', () => {
    set('SEEN_SECRET_BOL_NL_CLIENT_SECRET', 'from-the-environment');
    const directory = write('SEEN_SECRET_BOL_NL_CLIENT_SECRET=from-the-file\n');

    loadLocalEnvironment(directory);

    expect(process.env.SEEN_SECRET_BOL_NL_CLIENT_SECRET).toBe('from-the-environment');
  });

  it('defaults to the repository root, not the working directory', () => {
    // nest start runs from apps/api and pnpm --filter runs from the package, so a
    // default of process.cwd() looks for a .env.local that is not there and finds
    // nothing, silently. That is the bug this test exists for.
    expect(repositoryRoot(join(repositoryRoot(), 'packages', 'providers', 'src'))).toBe(
      repositoryRoot(),
    );
    expect(existsSync(join(repositoryRoot(), 'pnpm-workspace.yaml'))).toBe(true);
  });

  it('does nothing at all when there is no file, because after go-live there will not be one', () => {
    expect(loadLocalEnvironment(mkdtempSync(join(tmpdir(), 'seen-env-')))).toBeNull();
  });

  it('gives the secrets provider the credential the README told you to put there', async () => {
    clear('SEEN_SECRET_BOL_NL_CLIENT_SECRET');
    const directory = write('SEEN_SECRET_BOL_NL_CLIENT_SECRET=a-bol-client-secret\n');

    loadLocalEnvironment(directory);

    await expect(createSecretsProvider().get('bol/nl/client-secret')).resolves.toBe(
      'a-bol-client-secret',
    );
  });
});
