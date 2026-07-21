from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_PATH = ROOT / "artifacts/deployment.json"


def deployment_value(name):
    if not DEPLOYMENT_PATH.is_file():
        return ""
    try:
        data = json.loads(DEPLOYMENT_PATH.read_text())
    except json.JSONDecodeError:
        return ""
    return str(data.get(name) or "")


escrow = os.getenv("ESCROW_CONTRACT_ADDRESS") or deployment_value("escrow")
mock_usdc = os.getenv("MOCK_USDC_ADDRESS") or deployment_value("mockUsdc")
chain_id = os.getenv("CHAIN_ID") or deployment_value("chainId") or "11155111"

required = ["KEEPERHUB_API_KEY"]
missing = [name for name in required if not os.getenv(name)]
if not escrow:
    missing.append("artifacts/deployment.json:escrow")
if not mock_usdc:
    missing.append("artifacts/deployment.json:mockUsdc")
if missing:
    print("Missing:", ", ".join(missing))
    sys.exit(1)
if not os.environ["KEEPERHUB_API_KEY"].startswith("kh_"):
    print("KEEPERHUB_API_KEY must be an organisation key starting with kh_")
    sys.exit(1)

base = os.getenv("KEEPERHUB_BASE_URL", "https://app.keeperhub.com").rstrip("/")
headers = {"Authorization": f"Bearer {os.environ['KEEPERHUB_API_KEY']}"}
with httpx.Client(timeout=30) as client:
    response = client.get(f"{base}/api/chains", headers=headers)
    print("KeeperHub /api/chains:", response.status_code)
    if response.is_error:
        print(response.text[:1000])
        sys.exit(1)
    chains = response.json()
    print("Authentication OK. Configured chain:", chain_id)
    print("Escrow:", escrow)
    print("MockUSDC:", mock_usdc)
    print("Live preflight passed; use the UI to run the official simulation before broadcast.")
