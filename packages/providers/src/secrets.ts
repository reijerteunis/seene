import {
  type Environment,
  notUntilGoLive,
  ProviderConfigurationError,
  selectImplementation,
} from './selection.ts';

/**
 * Credentials are held per connection and read at job time. The database holds
 * only the reference, never the secret, so this interface is the only way a
 * credential reaches a connector.
 */
export interface SecretsProvider {
  /** The implementation that was selected, so a log line can say which one ran. */
  readonly name: SecretsProviderName;
  /** Resolves a reference such as 'bol/nl/client-secret' to its value. */
  get(reference: string): Promise<string>;
}

export const SECRETS_PROVIDERS = ['env', 'gcp-secret-manager'] as const;
export type SecretsProviderName = (typeof SECRETS_PROVIDERS)[number];

/**
 * A reference is a path; the variable is that path shouted. 'bol/nl/client-secret'
 * reads SEEN_SECRET_BOL_NL_CLIENT_SECRET, which is greppable in both directions.
 */
export function environmentVariableFor(reference: string): string {
  return `SEEN_SECRET_${reference.replace(/[^a-zA-Z0-9]+/g, '_').toUpperCase()}`;
}

/** The development and pilot implementation: values live in .env.local, gitignored. */
export function envSecretsProvider(env: Environment): SecretsProvider {
  return {
    name: 'env',
    async get(reference: string): Promise<string> {
      const variable = environmentVariableFor(reference);
      const value = env[variable];
      if (value === undefined || value === '') {
        throw new ProviderConfigurationError(
          `No secret for '${reference}'. Set ${variable} in .env.local.`,
        );
      }
      return value;
    },
  };
}

export function createSecretsProvider(env: Environment = process.env): SecretsProvider {
  const name = selectImplementation(env, 'SEEN_SECRETS_PROVIDER', SECRETS_PROVIDERS, 'env');

  switch (name) {
    case 'env':
      return envSecretsProvider(env);
    case 'gcp-secret-manager':
      return notUntilGoLive('SEEN_SECRETS_PROVIDER', name);
  }
}
