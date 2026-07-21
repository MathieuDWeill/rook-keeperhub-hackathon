from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

required = ["KEEPERHUB_API_KEY", "ESCROW_CONTRACT_ADDRESS"]
missing = [name for name in required if not os.getenv(name)]
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
    print("Authentication OK. Configured chain:", os.getenv("CHAIN_ID", "11155111"))
    print("Escrow:", os.environ["ESCROW_CONTRACT_ADDRESS"])
    print("Live preflight passed; use the UI to run the official simulation before broadcast.")
