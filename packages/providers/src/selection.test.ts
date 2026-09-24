import { describe, expect, it } from 'vitest';

import { createSecretsProvider } from './secrets';
import { createStorageProvider } from './storage';
import { createTelemetryProvider } from './telemetry';
import { ProviderConfigurationError } from './selection';

/**
 * The cloud is a configuration switch (SEEN-007), which is only true if the
 * switch is the whole of what selects an implementation. These tests hold each
 * factory to one environment variable and to refusing anything it does not know
 * by name, because a factory that silently falls back to the local implementation
 * would send a pilot's credentials to a laptop and report success.
 */
describe('provider selection', () => {
  describe('secrets', () => {
    it('defaults to the .env.local implementation when nothing is set', () => {
      expect(createSecretsProvider({}).name).toBe('env');
    });

    it('is chosen by SEEN_SECRETS_PROVIDER alone', () => {
      expect(createSecretsProvider({ SEEN_SECRETS_PROVIDER: 'env' }).name).toBe('env');
    });

    it('names the variable and the value it could not honour', () => {
      expect(() => createSecretsProvider({ SEEN_SECRETS_PROVIDER: 'vault' })).toThrow(
        /SEEN_SECRETS_PROVIDER.*vault/s,
      );
      expect(() => createSecretsProvider({ SEEN_SECRETS_PROVIDER: 'vault' })).toThrow(
        ProviderConfigurationError,
      );
    });

    it('knows the Secret Manager implementation by name and refuses it until SEEN-007', () => {
      expect(() => createSecretsProvider({ SEEN_SECRETS_PROVIDER: 'gcp-secret-manager' })).toThrow(
        /SEEN-007/,
      );
    });
  });

  describe('storage', () => {
    const local = {
      SEEN_STORAGE_PROVIDER: 'supabase',
      SUPABASE_URL: 'http://127.0.0.1:54321',
      SUPABASE_SERVICE_ROLE_KEY: 'local-service-role',
      SEEN_STORAGE_BUCKET: 'evidence',
    };

    it('defaults to local Supabase Storage', () => {
      expect(createStorageProvider(local).name).toBe('supabase');
    });

    it('names the variable and the value it could not honour', () => {
      expect(() => createStorageProvider({ ...local, SEEN_STORAGE_PROVIDER: 's3' })).toThrow(
        /SEEN_STORAGE_PROVIDER.*s3/s,
      );
    });

    it('refuses to be built without the connection details it needs', () => {
      expect(() => createStorageProvider({ SEEN_STORAGE_PROVIDER: 'supabase' })).toThrow(
        /SUPABASE_URL/,
      );
    });
  });

  describe('telemetry', () => {
    it('defaults to the console implementation', () => {
      expect(createTelemetryProvider({}).name).toBe('console');
    });

    it('is chosen by SEEN_TELEMETRY_PROVIDER alone', () => {
      expect(
        createTelemetryProvider({
          SEEN_TELEMETRY_PROVIDER: 'otlp',
          SEEN_OTLP_ENDPOINT: 'http://127.0.0.1:4318',
        }).name,
      ).toBe('otlp');
    });

    it('names the variable and the value it could not honour', () => {
      expect(() => createTelemetryProvider({ SEEN_TELEMETRY_PROVIDER: 'datadog' })).toThrow(
        /SEEN_TELEMETRY_PROVIDER.*datadog/s,
      );
    });

    it('knows the Cloud Logging implementation by name and refuses it until SEEN-007', () => {
      expect(() => createTelemetryProvider({ SEEN_TELEMETRY_PROVIDER: 'cloud-logging' })).toThrow(
        /SEEN-007/,
      );
    });
  });
});
