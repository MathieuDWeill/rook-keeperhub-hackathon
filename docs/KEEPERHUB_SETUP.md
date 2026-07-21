# KeeperHub live setup — exact final steps

Rook uses KeeperHub's **Direct Execution API** rather than a custom workflow. This removes workflow-building work and lets the app call `RookEscrow.release(...)` directly.

## 1. Create the KeeperHub organization key

In KeeperHub, create an **organization-scoped** API key. It must start with `kh_`.

Put it in the root `.env`:

```dotenv
KEEPERHUB_API_KEY=kh_...
KEEPERHUB_MODE=live
```

## 2. Obtain the KeeperHub executor wallet

The organization wallet that sends direct-execution transactions must receive `EXECUTOR_ROLE` in the escrow contract. Set:

```dotenv
KEEPERHUB_EXECUTOR_ADDRESS=0x...
```

The deployment script grants that address the role in the constructor.

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

The script deploys `MockUSDC`, deploys `RookEscrow`, mints test tokens, approves, and funds the escrow. It writes `artifacts/deployment.json`.

Copy the emitted escrow address into `.env`:

```dotenv
ESCROW_CONTRACT_ADDRESS=0x...
```

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
