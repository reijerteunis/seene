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
export function loadLocalEnvironment(directory?: string): string | null {
  // No repository means no .env.local, which is the normal case in a built image:
  // after go-live (SEEN-007) Cloud Run has no pnpm-workspace.yaml anywhere above it.
  // This is called from a bootstrap module imported first by both apps, so throwing
  // here would be both services failing to start on the one path this whole package
  // exists to make uneventful.
  const root = directory ?? findRepositoryRoot();
  if (root === null) return null;

  const path = join(root, '.env.local');
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
 * The repository root: the directory up the tree holding pnpm-workspace.yaml, or
 * null when there is no repository, as in a built image.
 *
 * Walking up rather than counting '..' from this file, because this module compiles
 * to CommonJS in the apps and runs as ESM under vitest, and neither __dirname nor
 * import.meta.url is available in both.
 *
 * It is what loadLocalEnvironment looks from, and it has to be: the working
 * directory is not the root for any of the ways this code is started. `nest start`
 * runs from apps/api and `pnpm --filter` runs from the package, and both would look
 * for a .env.local that is not there and find nothing, silently.
 */
export function findRepositoryRoot(from: string = process.cwd()): string | null {
  let directory = from;

  for (;;) {
    if (existsSync(join(directory, 'pnpm-workspace.yaml'))) return directory;

    const parent = dirname(directory);
    if (parent === directory) return null;
    directory = parent;
  }
}

/**
 * The repository root, or an error naming where it looked. For callers that only
 * ever run inside the repository, such as a test reading a fixture out of it, where no
 * root is a broken assumption rather than a deployment.
 */
export function repositoryRoot(from: string = process.cwd()): string {
  const root = findRepositoryRoot(from);
  if (root === null) {
    throw new Error(`No pnpm-workspace.yaml above '${from}', so there is no repository root.`);
  }
  return root;
}
