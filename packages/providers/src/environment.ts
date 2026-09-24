import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';

/**
 * Reads .env.local into the environment. The README says to copy .env.example to
 * it, .env.example carries every variable the services and the three providers
 * read, and envSecretsProvider's own error tells you to put a credential there,
 * so something has to actually read the file or all of that is decoration.
 *
 * Values already in the environment win. A deployment sets real variables and must
 * not be quietly overridden by a file that happened to be left in the image, and
 * after go-live (SEEN-007) there is no file at all: Secret Manager holds the
 * credentials and Cloud Run holds the rest.
 *
 * Returns the path it read, or null when there was nothing to read.
 */
export function loadLocalEnvironment(directory: string = repositoryRoot()): string | null {
  const path = join(directory, '.env.local');
  if (!existsSync(path)) return null;

  // Node's own parser, so the file behaves the same as `node --env-file` does and
  // there is one syntax to learn rather than a library's dialect of it.
  const before = { ...process.env };
  process.loadEnvFile(path);

  for (const [name, value] of Object.entries(before)) {
    if (value !== undefined) process.env[name] = value;
  }

  return path;
}

/**
 * The repository root: the directory up the tree holding pnpm-workspace.yaml.
 *
 * The default for loadLocalEnvironment, and it has to be, because the working
 * directory is not the root for most of the ways this code is started. `nest start`
 * runs from apps/api, `pnpm --filter` runs from the package, and both would look
 * for a .env.local that is not there and find nothing, silently.
 *
 * Walking up rather than counting '..' from this file: this module compiles to
 * CommonJS in the apps and runs as ESM under vitest, and neither __dirname nor
 * import.meta.url is available in both.
 */
export function repositoryRoot(from: string = process.cwd()): string {
  let directory = from;

  for (;;) {
    if (existsSync(join(directory, 'pnpm-workspace.yaml'))) return directory;

    const parent = dirname(directory);
    if (parent === directory) {
      throw new Error(`No pnpm-workspace.yaml above '${from}', so there is no repository root.`);
    }
    directory = parent;
  }
}
