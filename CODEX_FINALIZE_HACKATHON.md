# Codex finalization — only environment-dependent work remains

Do not redesign or expand the product. The repository already contains the policy engine, KeeperHub adapter, contracts, demo, tests, CI, threat model, deployment automation and submission kit.

## Execute

```bash
./scripts/bootstrap.sh
make quality
```

## Human values required

Populate `.env` with:

- `KEEPERHUB_API_KEY` — organization key beginning `kh_`;
- `RPC_URL` — Ethereum Sepolia RPC;
- `DEPLOYER_PRIVATE_KEY` — testnet-only deployment key;
- `ARTISAN_ADDRESS` — testnet recipient.

Never copy these values into source, logs, screenshots or commits.

`KEEPERHUB_EXECUTOR_ADDRESS` is optional: when it is absent, deployment derives the KeeperHub organization wallet from a Direct Execution dry-run simulation and grants that wallet `EXECUTOR_ROLE`.

## Live completion

1. Confirm Sepolia is enabled in KeeperHub and the organization wallet has test ETH.
2. Run `make deploy`.
3. `artifacts/deployment.json` records `mockUsdc` and `escrow`; later live commands read those addresses automatically.
4. Set `KEEPERHUB_MODE=live`.
5. Run `make live-preflight`.
6. Start `make run-api` and `make run-demo` in separate terminals.
7. Execute one approved release through the UI.
8. Save KeeperHub's `executionId`, `transactionHash` and `transactionLink`.
9. Execute the rejected scenario by removing signed acceptance; confirm no KeeperHub call occurs.
10. Fill the final URLs and run `make submission`.

## Definition of done

- all local and CI checks pass;
- no secrets are committed;
- deployed escrow is funded;
- KeeperHub wallet has `EXECUTOR_ROLE`;
- at least one real KeeperHub transaction is linked;
- demo video follows `docs/DEMO_RUNBOOK.md`;
- README links are updated, without claiming unavailable evidence.

Report only actual results and precise blockers. Never substitute a direct signer transaction for KeeperHub.
