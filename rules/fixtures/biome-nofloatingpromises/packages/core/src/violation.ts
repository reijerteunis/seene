// Refused by biome/noFloatingPromises. An unawaited write to the audit log is a
// side effect that happened before its event was committed, and the error it
// drops is the error nobody sees.
async function writeAuditEvent(): Promise<void> {
  return undefined;
}

export function submitClaim(): void {
  writeAuditEvent();
}
