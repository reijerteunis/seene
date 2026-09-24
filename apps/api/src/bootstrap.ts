import { loadLocalEnvironment } from '@seen/providers';

/**
 * Imported first by main.ts, and for one reason: modules read process.env while
 * they are being loaded (the worker's Redis connection is built at module scope),
 * so the file has to be in the environment before any of them is required.
 *
 * A side-effect import is the only ordering that holds. Calling this inside
 * bootstrap() would run it after every import above it had already read an empty
 * environment.
 */
loadLocalEnvironment();
