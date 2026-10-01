import { Storage } from '@google-cloud/storage';

/** The import that would make go-live a refactor rather than a configuration. */
export const evidence = new Storage().bucket('evidence');
