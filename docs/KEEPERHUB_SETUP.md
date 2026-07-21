# KeeperHub live setup — exact final steps

Rook uses KeeperHub's **Direct Execution API** rather than a custom workflow. This removes workflow-building work and lets the app call `RookEscrow.release(...)` directly.

## 1. Create the KeeperHub organization key

In KeeperHub, create an **organization-scoped** API key. It must start with `kh_`.

Put it in the root `.env`:

```dotenv
KEEPERHUB_API_KEY=kh_...
KEEPERHUB_MODE=live
```

## 2. KeeperHub executor wallet

The organization wallet that sends Direct Execution transactions must receive `EXECUTOR_ROLE` in the escrow contract. By default, `make deploy` derives this address from a strict KeeperHub `simulate: true` request and grants it in the constructor.

Only set this optional override if KeeperHub support gives you a specific sender address:

```dotenv
KEEPERHUB_EXECUTOR_ADDRESS=0x...
```

The deployment script grants the derived or overridden address the role in the constructor.

## 3. Prepare Sepolia deployment values

```dotenv
CHAIN_ID=11155111
RPC_URL=https://...
DEPLOYER_PRIVATE_KEY=0x...
ARTISAN_ADDRESS=0x...
FUNDED_AMOUNT_MINOR=10000000000
```

Use a dedicated test wallet. Never commit `.env`.

## 4. Deploy and fund

```bash
./scripts/bootstrap.sh
cp .env.example .env  # only if bootstrap did not already create it
# edit .env
make test
make deploy
```

The script deploys `MockUSDC`, deploys `RookEscrow`, mints test tokens, approves, and funds the escrow. It writes `mockUsdc` and `escrow` to `artifacts/deployment.json`; `make live-preflight` and `make run-demo` read those addresses automatically.

## 5. Verify connectivity

```bash
source .venv/bin/activate
python scripts/live_preflight.py
```

## 6. Run

Terminal 1:

```bash
source .venv/bin/activate
uvicorn apps.api.app.main:app --reload --port 8000
```

Terminal 2:

```bash
source .venv/bin/activate
streamlit run apps/demo/app.py
```

## What the live path does

1. POSTs the exact `release` contract call with `simulate: true`.
2. Stops if KeeperHub reports a revert.
3. Broadcasts the identical body with an `Idempotency-Key`.
4. Fetches `/api/execute/{executionId}/status`.
5. Displays KeeperHub's authoritative transaction hash and explorer link.
