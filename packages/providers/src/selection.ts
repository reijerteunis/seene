/** The environment a factory reads. Passed in rather than reached for, so a test needs no global. */
export type Environment = Readonly<Record<string, string | undefined>>;

/**
 * A provider could not be built from the environment as it stands. Always names
 * the variable, because the fix is always to set or correct one.
 */
export class ProviderConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ProviderConfigurationError';
  }
}

/**
 * Reads one variable and returns one of the names this factory knows. Unknown
 * values are refused rather than falling back: a typo that silently kept the
 * laptop implementation is how a pilot's credentials end up in the wrong place
 * with nothing in the log to say so.
 */
export function selectImplementation<T extends string>(
  env: Environment,
  variable: string,
  known: readonly T[],
  fallback: T,
): T {
  const value = env[variable];
  if (value === undefined || value === '') return fallback;
  if ((known as readonly string[]).includes(value)) return value as T;

  throw new ProviderConfigurationError(
    `${variable} is set to '${value}', which is not one of ${known.join(', ')}.`,
  );
}

/** A cloud implementation is named here before it exists, so the switch is visible. */
export function notUntilGoLive(variable: string, value: string): never {
  throw new ProviderConfigurationError(
    `${variable} is set to '${value}', which is only available after the go decision in SEEN-007. ` +
      'Until then the local implementation is the one that runs.',
  );
}

/** A variable the chosen implementation cannot do without. */
export function required(env: Environment, variable: string): string {
  const value = env[variable];
  if (value === undefined || value === '') {
    throw new ProviderConfigurationError(`${variable} is required and is not set.`);
  }
  return value;
}
