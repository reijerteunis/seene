import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { CLOUD_SDK_PREFIXES, findCloudSdkImports, repositoryRoot } from './boundary';

/**
 * The rule the whole repository is held to: a cloud SDK may only be imported
 * inside packages/providers. It is what makes SEEN-007 a configuration change
 * rather than a refactor, and it is the kind of rule that decays silently, so a
 * test rather than a convention.
 */
describe('the cloud SDK boundary', () => {
  it('finds an import that a grep for the package name would also have to find', () => {
    const root = mkdtempSync(join(tmpdir(), 'seen-boundary-'));
    mkdirSync(join(root, 'apps', 'api', 'src'), { recursive: true });
    mkdirSync(join(root, 'packages', 'providers', 'src'), { recursive: true });

    writeFileSync(
      join(root, 'apps', 'api', 'src', 'leak.ts'),
      "import { Storage } from '@google-cloud/storage';\nexport const s = Storage;\n",
    );
    // The same import inside the provider package is the point of the package.
    writeFileSync(
      join(root, 'packages', 'providers', 'src', 'allowed.ts'),
      "import { Storage } from '@google-cloud/storage';\nexport const s = Storage;\n",
    );

    const found = findCloudSdkImports(root);

    expect(found).toHaveLength(1);
    expect(found[0]?.file).toBe('apps/api/src/leak.ts');
    expect(found[0]?.specifier).toBe('@google-cloud/storage');
  });

  it('reads require and dynamic import too, because both reach the same SDK', () => {
    const root = mkdtempSync(join(tmpdir(), 'seen-boundary-'));
    mkdirSync(join(root, 'packages', 'core', 'src'), { recursive: true });

    writeFileSync(
      join(root, 'packages', 'core', 'src', 'a.ts'),
      "const { S3 } = require('@aws-sdk/client-s3');\nexport const s = S3;\n",
    );
    writeFileSync(
      join(root, 'packages', 'core', 'src', 'b.ts'),
      "export const later = () => import('@google-cloud/logging');\n",
    );

    expect(findCloudSdkImports(root).map((f) => f.specifier).sort()).toEqual([
      '@aws-sdk/client-s3',
      '@google-cloud/logging',
    ]);
  });

  it('gives the line of an import broken over several lines', () => {
    const root = mkdtempSync(join(tmpdir(), 'seen-boundary-'));
    mkdirSync(join(root, 'apps', 'api', 'src'), { recursive: true });

    writeFileSync(
      join(root, 'apps', 'api', 'src', 'wrapped.ts'),
      ['// a comment', 'const x = 1;', 'import {', '  Storage,', "} from '@google-cloud/storage';", ''].join(
        '\n',
      ),
    );

    // Line 3, where the statement starts. Searching the file for the matched text
    // finds nothing when the match spans lines, and reported 0.
    expect(findCloudSdkImports(root)).toEqual([
      { file: 'apps/api/src/wrapped.ts', line: 3, specifier: '@google-cloud/storage' },
    ]);
  });

  it('names every SDK the rule is about, so adding one is a deliberate edit', () => {
    expect(CLOUD_SDK_PREFIXES).toContain('@google-cloud/');
    expect(CLOUD_SDK_PREFIXES).toContain('@aws-sdk/');
    expect(CLOUD_SDK_PREFIXES).toContain('googleapis');
  });

  it('finds no cloud SDK anywhere in this repository outside packages/providers', () => {
    expect(findCloudSdkImports(repositoryRoot())).toEqual([]);
  });
});
