// Refused by biome/noMisusedPromises. A promise used as a condition is always
// truthy, so a gate asked without the await decides autonomous for every action.
async function autonomyAllowed(): Promise<boolean> {
  return false;
}

export function decide(): string {
  if (autonomyAllowed()) {
    return 'autonomous';
  }
  return 'approval';
}
