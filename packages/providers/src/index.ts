/**
 * The three things the cloud will configure: where credentials come from, where
 * bytes are kept, and where traces and cost go. Every cloud SDK import lives in
 * this package and nowhere else, which is what makes go-live (SEEN-007) a change
 * of environment variables rather than a change of code.
 */

export { findRepositoryRoot, loadLocalEnvironment, repositoryRoot } from './environment.ts';

export {
  type Environment,
  ProviderConfigurationError,
  required,
  selectImplementation,
} from './selection.ts';

export {
  createSecretsProvider,
  environmentVariableFor,
  envSecretsProvider,
  SECRETS_PROVIDERS,
  type SecretsProvider,
  type SecretsProviderName,
} from './secrets.ts';

export {
  createStorageProvider,
  sha256,
  STORAGE_PROVIDERS,
  type StorageProvider,
  type StorageProviderName,
  type StoredObject,
  supabaseStorageProvider,
} from './storage.ts';

export {
  type Attributes,
  type AttributeValue,
  consoleTelemetryProvider,
  type CostEntry,
  createTelemetryProvider,
  otlpTelemetryProvider,
  otlpTracesPayload,
  type Span,
  TELEMETRY_PROVIDERS,
  type TelemetryProvider,
  type TelemetryProviderName,
} from './telemetry.ts';
