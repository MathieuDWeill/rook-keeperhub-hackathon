# ADR-001: Use KeeperHub Direct Execution

**Status:** accepted

Rook uses KeeperHub Direct Execution rather than a custom signer or a visual workflow. The module needs one precise contract call and benefits directly from simulation, gas management, execution audit and idempotency. A provider-neutral application boundary remains so iArtisanat can use regulated rails in production.
