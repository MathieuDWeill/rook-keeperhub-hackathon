# Threat model

| Threat | Control |
|---|---|
| Agent hallucinates approval | Agent cannot change deterministic policy outcome |
| Missing acceptance or invoice | Mandatory verified evidence checks |
| Active dispute | Hard policy rejection |
| Duplicate HTTP retry | KeeperHub `Idempotency-Key` |
| Duplicate onchain mandate | `consumedDecision` mapping |
| Recipient substitution | Contract enforces immutable artisan address |
| Client claws funds back early | Refund only after immutable expiry |
| ABI, allowance or balance error | Same-payload KeeperHub simulation |
| Compromised deployer key | Deployer is not used by runtime execution |
| Secret leakage | `.env` ignored, preflight scan and CI secret scan |

## Trust boundaries
Rook trusts the configured KeeperHub organization wallet as executor, the evidence verification inputs supplied by the host product, and the target chain. Production usage additionally requires regulated payment/custody partners and stronger identity, dispute and evidence-verification controls.
