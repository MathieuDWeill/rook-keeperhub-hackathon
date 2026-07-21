# Architecture

```text
iArtisanat / Demo UI
        |
        v
Rook API ──> deterministic policy engine ──> immutable decision record
        |                                            |
        | approved only                              | decisionId
        v                                            v
KeeperHub execution adapter ──> KeeperHub workflow ──> RookEscrow.release(...)
        |                                            |
        └──────── execution/audit status <───────────┘
```

## Security invariants

1. AI output is advisory; deterministic policy controls execution.
2. Rejected decisions never reach KeeperHub.
3. Each approved decision has a unique idempotency key.
4. The contract rejects replay of a decision identifier.
5. The executor can release only up to the funded amount.
6. Secrets are environment-only.
7. Stub mode explicitly reports that no transaction was submitted.

## Production evolution

A regulated payment provider should custody fiat/e-money. The on-chain contract can remain a proof-of-concept or support stablecoin-native professional flows where legally appropriate. The product model should not depend on forcing consumers to use crypto.
