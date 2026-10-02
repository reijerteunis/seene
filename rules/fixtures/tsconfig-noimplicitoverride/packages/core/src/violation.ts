// Refused by tsconfig/noImplicitOverride. A method that silently shadows the
// base class is a capability routed one way and implemented another.
class MarketplaceConnector {
  capabilities(): readonly string[] {
    return [];
  }
}

export class BolConnector extends MarketplaceConnector {
  capabilities(): readonly string[] {
    return ['ingest-orders'];
  }
}
