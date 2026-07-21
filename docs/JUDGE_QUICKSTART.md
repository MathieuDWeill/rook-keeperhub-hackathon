# Judge quickstart

## 60-second local proof

```bash
cp .env.example .env
./scripts/bootstrap.sh
make readiness
make judge-demo
```

Then launch `make run-api` and `make run-demo` in separate terminals.

The approved scenario exposes the exact KeeperHub payload in stub mode. The rejected scenario proves that missing client acceptance stops before KeeperHub. Live submission requires the transaction URL recorded in `artifacts/DORAHACKS_SUBMISSION.md`.
