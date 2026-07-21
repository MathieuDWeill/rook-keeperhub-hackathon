"""Zero-secret smoke test of the public API in KeeperHub stub mode."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hashlib
import os
from fastapi.testclient import TestClient

os.environ["KEEPERHUB_MODE"] = "stub"
from apps.api.app.main import app  # noqa: E402

client = TestClient(app)
def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
payload = {
    "project_id": "12345678-1234-5678-1234-567812345678",
    "milestone_id": "roof-complete",
    "amount_minor": 3_000_000_000,
    "token": "USDC",
    "recipient": "0x1111111111111111111111111111111111111111",
    "escrow_contract": "0x2222222222222222222222222222222222222222",
    "client_accepted": True,
    "invoice_verified": True,
    "compliance_clear": True,
    "dispute_open": False,
    "retention_bps": 500,
    "evidence": [
        {"kind": "signed_acceptance", "uri": "ipfs://acceptance", "sha256": sha("acceptance"), "verified": True},
        {"kind": "invoice", "uri": "ipfs://invoice", "sha256": sha("invoice"), "verified": True},
    ],
}
approved = client.post("/v1/releases/execute", json=payload)
assert approved.status_code == 200, approved.text
assert approved.json()["decision"]["status"] == "approved"
assert approved.json()["execution"]["status"] == "not_submitted"

payload["client_accepted"] = False
rejected = client.post("/v1/releases/execute", json=payload)
assert rejected.status_code == 200, rejected.text
assert rejected.json()["decision"]["status"] == "rejected"
assert rejected.json()["execution"] is None
print("Rook smoke demo passed: approved mandate preview + rejected unsafe mandate.")
