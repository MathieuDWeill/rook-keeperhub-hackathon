# Security policy

Rook is a hackathon prototype and must not custody production funds.

## Design controls
- deterministic policy decisions;
- no LLM authority over release rules;
- verified evidence requirements;
- open disputes block settlement;
- KeeperHub dry-run before every broadcast;
- organization-scoped API keys kept outside source control;
- idempotent offchain execution and replay protection onchain;
- fixed artisan recipient;
- client refund only after escrow expiry;
- role-based executor authorization and reentrancy protection.

## Reporting
Do not open a public issue for a live vulnerability. Contact the repository owner privately and include reproduction steps without secrets or funded keys.
